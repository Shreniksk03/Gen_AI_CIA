import json
import logging
import math
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from supabase import Client, create_client

logger = logging.getLogger("fraud_backend.db_service")

# Path to local resilient SQLite storage
DB_DIR = Path(__file__).resolve().parent.parent / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = DB_DIR / "local_transactions.db"


def init_sqlite_db():
    """Initializes local resilient SQLite tables and performs safe column migrations."""
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cursor = conn.cursor()

        # 1. Main transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                transaction_time TEXT NOT NULL,
                amount REAL NOT NULL,
                fraud_probability REAL NOT NULL,
                is_flagged INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                merchant TEXT,
                merchant_category TEXT,
                location TEXT,
                category TEXT,
                card_last4 TEXT,
                model_version TEXT DEFAULT 'xgboost-tree-explainer-v2.0',
                review_status TEXT DEFAULT 'PENDING',
                analyst_notes TEXT,
                reviewed_by TEXT,
                reviewed_at TEXT,
                shap_explanations TEXT,
                top_contributors TEXT,
                summary_narrative TEXT,
                v_features TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # 2. Review history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transaction_reviews (
                id TEXT PRIMARY KEY,
                transaction_id TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                analyst_notes TEXT,
                reviewed_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
            """
        )

        # 3. Safe migrations for existing SQLite databases
        cursor.execute("PRAGMA table_info(transactions)")
        existing_cols = [col[1] for col in cursor.fetchall()]

        migration_cols = [
            ("merchant_category", "TEXT DEFAULT 'Online Retail'"),
            ("model_version", "TEXT DEFAULT 'xgboost-tree-explainer-v2.0'"),
            ("review_status", "TEXT DEFAULT 'PENDING'"),
            ("analyst_notes", "TEXT"),
            ("reviewed_by", "TEXT"),
            ("reviewed_at", "TEXT"),
            ("top_contributors", "TEXT"),
            ("summary_narrative", "TEXT"),
        ]

        for col_name, col_type in migration_cols:
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Migrated SQLite schema: added column {col_name}")
                except Exception as me:
                    logger.warning(f"Could not add column {col_name}: {me}")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_time ON transactions (transaction_time DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_risk ON transactions (risk_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_flagged ON transactions (is_flagged)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_review ON transactions (review_status)")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize or migrate local SQLite database: {e}")


# Initialize SQLite table on load
init_sqlite_db()


def is_service_role_key(key: Optional[str]) -> bool:
    """Detects whether a key is a Supabase service-role secret (JWT or sb_secret)."""
    if not key:
        return False
    k = key.strip()
    if k.startswith("sb_secret_"):
        return True
    try:
        parts = k.split(".")
        if len(parts) == 3:
            import base64
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
            return payload.get("role") == "service_role"
    except Exception:
        pass
    return False


def ensure_uuid(val: Any) -> str:
    """Ensures a value is a valid UUID string; converts strings to UUID5 if invalid."""
    if not val:
        return str(uuid.uuid4())
    val_str = str(val).strip()
    try:
        return str(uuid.UUID(val_str))
    except (ValueError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, val_str))


def calculate_risk_level(fraud_probability: float) -> str:
    """
    Standard calibrated risk band hierarchy:
    - [0.60, 1.00]: CRITICAL
    - [0.40, 0.60): HIGH
    - [0.25, 0.40): MEDIUM
    - [0.00, 0.25): LOW
    """
    try:
        prob = float(fraud_probability or 0.0)
    except (TypeError, ValueError):
        prob = 0.0

    if prob >= 0.60:
        return "CRITICAL"
    elif prob >= 0.40:
        return "HIGH"
    elif prob >= 0.25:
        return "MEDIUM"
    else:
        return "LOW"


def resolve_review_status(row_status: Optional[str], is_flagged: bool) -> str:
    """
    Returns stored review status.
    - Flagged transactions default to 'PENDING'
    - Unflagged transactions default to 'NOT_FLAGGED'
    Analyst-confirmed statuses: 'CONFIRMED_FRAUD', 'LEGITIMATE'
    In-progress statuses: 'UNDER_REVIEW', 'ESCALATED'
    """
    if row_status and str(row_status).strip():
        val = str(row_status).strip().upper()
        if val in ("PENDING", "UNDER_REVIEW", "CONFIRMED_FRAUD", "LEGITIMATE", "ESCALATED", "NOT_FLAGGED"):
            return val
    return "PENDING" if is_flagged else "NOT_FLAGGED"


def get_supabase_client(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    service_role_key: Optional[str] = None,
) -> Optional[Client]:
    """
    Creates or returns Supabase client.
    Prefers service-role key for backend operations if provided (bypasses RLS securely on server).
    """
    url = supabase_url or os.getenv("SUPABASE_URL")
    
    # Priority: explicit service_role_key -> env SUPABASE_SERVICE_ROLE_KEY -> supabase_key -> env SUPABASE_KEY
    env_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    env_anon_key = os.getenv("SUPABASE_KEY")
    
    key = service_role_key or env_service_key or supabase_key or env_anon_key

    if not url or not key:
        return None

    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


def check_database_connectivity(client: Optional[Client]) -> Dict[str, Any]:
    """
    Performs live diagnostics on both Supabase PostgreSQL and local SQLite.
    Returns truthful status without masking failures.
    """
    supabase_status = "DISCONNECTED"
    supabase_count = 0
    supabase_writable = False
    supabase_error = None

    env_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    env_anon_key = os.getenv("SUPABASE_KEY")
    has_service_key = bool(env_service_key and env_service_key.strip()) or is_service_role_key(env_anon_key)

    if client:
        try:
            # Probe Supabase with a lightweight read
            res = client.table("transactions").select("id", count="exact").limit(1).execute()
            supabase_count = res.count if res.count is not None else len(res.data or [])

            if has_service_key:
                supabase_status = "CONNECTED"
                supabase_writable = True
            else:
                # With publishable key only, RLS blocks inserts
                supabase_status = "READ_ONLY (RLS Blocked — Missing Service Role Key)"
                supabase_writable = False
        except Exception as e:
            err_str = str(e)
            supabase_error = err_str
            if "42501" in err_str or "row-level security" in err_str.lower():
                supabase_status = "RLS_BLOCKED"
            else:
                supabase_status = f"ERROR: {err_str[:80]}"

    # Probe SQLite
    sqlite_status = "INACTIVE"
    sqlite_count = 0
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        sqlite_count = cursor.fetchone()[0]
        conn.close()
        sqlite_status = "ACTIVE"
    except Exception as sqle:
        logger.error(f"SQLite check failed: {sqle}")

    # Determine authoritative source
    if supabase_status == "CONNECTED" and supabase_writable:
        authoritative_source = "SUPABASE_POSTGRESQL"
        authoritative_source_label = "Data Source: Supabase PostgreSQL"
        is_healthy = True
    else:
        authoritative_source = "SQLITE_FALLBACK"
        authoritative_source_label = "Data Source: Local SQLite (Fallback)"
        is_healthy = sqlite_status == "ACTIVE"

    return {
        "authoritative_source": authoritative_source,
        "authoritative_source_label": authoritative_source_label,
        "is_healthy": is_healthy,
        "supabase_status": supabase_status,
        "supabase_count": supabase_count,
        "supabase_writable": supabase_writable,
        "supabase_error": supabase_error,
        "has_service_key": has_service_key,
        "sqlite_status": sqlite_status,
        "sqlite_count": sqlite_count,
    }


def validate_transaction_record(
    transaction_id: str,
    amount: float,
    fraud_probability: float,
    is_flagged: bool,
) -> Tuple[bool, Optional[str]]:
    """Validates transaction values before attempting database insertion."""
    if not transaction_id or not isinstance(transaction_id, str):
        return False, "Invalid transaction_id: must be a non-empty string"
    if amount < 0:
        return False, f"Invalid amount: {amount} cannot be negative"
    if not (0.0 <= fraud_probability <= 1.0):
        return False, f"Invalid fraud_probability: {fraud_probability} must be in [0.0, 1.0]"
    return True, None


def persist_transaction(
    client: Optional[Client],
    transaction_id: str,
    amount: float,
    fraud_probability: float,
    is_flagged: bool,
    risk_level: str,
    shap_explanations: Dict[str, float],
    top_contributors: Optional[List[Dict[str, Any]]] = None,
    summary_narrative: Optional[List[str]] = None,
    features: Optional[Dict[str, Any]] = None,
    merchant: Optional[str] = None,
    merchant_category: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    card_last4: Optional[str] = None,
    model_version: str = "xgboost-tree-explainer-v2.0",
    review_status: str = "PENDING",
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Persists transaction with verified, transparent dual-engine strategy:
    1. Validates record attributes.
    2. Persists to local SQLite to guarantee zero local data loss.
    3. Attempts verified insert into Supabase PostgreSQL.
    4. Returns exact status indicating whether Supabase succeeded or was rejected.
    """
    is_valid, validation_err = validate_transaction_record(
        transaction_id, amount, fraud_probability, is_flagged
    )
    if not is_valid:
        logger.error(f"Transaction validation failed: {validation_err}")
        return {
            "success": False,
            "supabase_persisted": False,
            "sqlite_persisted": False,
            "error": validation_err,
            "database_source": "NONE",
            "database_source_label": "Validation Failed",
        }

    ts = timestamp or datetime.now(timezone.utc)
    iso_timestamp = ts.isoformat()
    safe_uuid = ensure_uuid(transaction_id)

    # 1. Local SQLite persistence (resilient offline replica)
    sqlite_persisted = False
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO transactions (
                id, transaction_time, amount, fraud_probability, is_flagged, risk_level,
                merchant, merchant_category, location, category, card_last4,
                model_version, review_status, shap_explanations, top_contributors,
                summary_narrative, v_features, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                safe_uuid,
                iso_timestamp,
                float(amount),
                float(fraud_probability),
                1 if is_flagged else 0,
                risk_level,
                merchant or "Simulated Terminal",
                merchant_category or category or "Online Retail",
                location or "Encrypted Origin",
                category or "Financial",
                card_last4 or "7890",
                model_version,
                review_status,
                json.dumps(shap_explanations or {}),
                json.dumps(top_contributors or []),
                json.dumps(summary_narrative or []),
                json.dumps(features or {}),
                iso_timestamp,
            ),
        )
        conn.commit()
        conn.close()
        sqlite_persisted = True
        logger.info(f"Persisted transaction {safe_uuid} to local SQLite store.")
    except Exception as sqlite_err:
        logger.error(f"SQLite persistence error for {safe_uuid}: {sqlite_err}")

    # 2. Supabase Cloud PostgreSQL persistence
    supabase_persisted = False
    supabase_error = None

    if client:
        # Full schema record
        full_record = {
            "id": safe_uuid,
            "amount": float(amount),
            "fraud_probability": float(fraud_probability),
            "is_flagged": is_flagged,
            "risk_level": risk_level,
            "merchant": merchant or "Global Payment Terminal",
            "merchant_category": merchant_category or category or "Online Retail",
            "location": location or "Secure POS Gateway",
            "card_last4": card_last4 or "4242",
            "model_version": model_version,
            "review_status": review_status,
            "shap_explanations": shap_explanations or {},
            "top_contributors": top_contributors or [],
            "summary_narrative": summary_narrative or [],
            "v_features": features or {},
            "transaction_time": iso_timestamp,
            "created_at": iso_timestamp,
        }

        try:
            response = client.table("transactions").insert(full_record).execute()
            if response.data:
                supabase_persisted = True
                logger.info(f"Successfully inserted transaction {safe_uuid} into Supabase PostgreSQL.")
        except Exception as insert_err:
            err_str = str(insert_err)
            # If missing columns in unmigrated Supabase schema, try core columns fallback
            if (
                "schema cache" in err_str.lower()
                or "PGRST204" in err_str
                or "42703" in err_str
                or "does not exist" in err_str.lower()
            ):
                core_record = {
                    "id": safe_uuid,
                    "amount": float(amount),
                    "fraud_probability": float(fraud_probability),
                    "is_flagged": is_flagged,
                    "shap_explanations": shap_explanations or {},
                    "v_features": features or {},
                    "transaction_time": iso_timestamp,
                }
                try:
                    core_res = client.table("transactions").insert(core_record).execute()
                    if core_res.data:
                        supabase_persisted = True
                        logger.info(f"Inserted transaction {safe_uuid} into Supabase (core columns fallback).")
                except Exception as core_err:
                    supabase_error = str(core_err)
                    logger.error(f"[SUPABASE INSERT FAILED] Transaction {safe_uuid}: {core_err}")
            else:
                supabase_error = err_str
                logger.error(f"[SUPABASE INSERT FAILED] Transaction {safe_uuid}: {insert_err}")

    # Determine authoritative result
    if supabase_persisted:
        return {
            "success": True,
            "supabase_persisted": True,
            "sqlite_persisted": sqlite_persisted,
            "database_source": "SUPABASE_POSTGRESQL",
            "database_source_label": "Data Source: Supabase PostgreSQL",
            "error": None,
        }
    else:
        return {
            "success": sqlite_persisted,
            "supabase_persisted": False,
            "sqlite_persisted": sqlite_persisted,
            "database_source": "SQLITE_FALLBACK",
            "database_source_label": "Data Source: Local SQLite (Fallback)",
            "error": supabase_error or "Supabase client unavailable",
        }


def query_transactions(
    client: Optional[Client],
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    review_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "transaction_time",
    sort_order: str = "desc",
) -> Tuple[List[Dict[str, Any]], int, int, str, str]:
    """
    Queries transactions from the authoritative data store:
    - If Supabase PostgreSQL is connected and populated: queries Supabase.
    - If Supabase is empty or in fallback mode: queries local SQLite.
    Returns: (records, total_count, total_pages, data_source, data_source_label)
    """
    diag = check_database_connectivity(client)

    # If Supabase is connected and authoritative, query Supabase
    if client and diag["authoritative_source"] == "SUPABASE_POSTGRESQL":
        try:
            query = client.table("transactions").select("*", count="exact")

            if risk_level:
                query = query.eq("risk_level", risk_level.upper())
            if is_flagged is not None:
                query = query.eq("is_flagged", is_flagged)
            if review_status:
                query = query.eq("review_status", review_status.upper())
            if start_date:
                query = query.gte("transaction_time", start_date)
            if end_date:
                query = query.lte("transaction_time", end_date)

            order_col = sort_by if sort_by in ("transaction_time", "amount", "fraud_probability", "risk_level") else "transaction_time"
            query = query.order(order_col, desc=(sort_order.lower() == "desc"))

            offset = (page - 1) * limit
            query = query.range(offset, offset + limit - 1)

            res = query.execute()
            total_count = res.count if res.count is not None else len(res.data)
            total_pages = max(1, math.ceil(total_count / limit))

            records: List[Dict[str, Any]] = []
            for row in res.data:
                v_feat = row.get("v_features") or {}
                prob = float(row.get("fraud_probability") or 0.0)
                is_fl = bool(row.get("is_flagged"))

                # 1. Deterministic risk level
                stored_risk = row.get("risk_level") or (v_feat.get("risk_level") if isinstance(v_feat, dict) else None)
                risk_level = (
                    stored_risk.upper()
                    if (stored_risk and str(stored_risk).upper() in ("LOW", "MEDIUM", "HIGH", "CRITICAL"))
                    else calculate_risk_level(prob)
                )

                # 2. Deterministic review status (default PENDING for flagged)
                stored_status = row.get("review_status") or (v_feat.get("review_status") if isinstance(v_feat, dict) else None)
                review_status = resolve_review_status(stored_status, is_fl)

                stored_notes = row.get("analyst_notes") or (v_feat.get("analyst_notes") if isinstance(v_feat, dict) else None)
                stored_by = row.get("reviewed_by") or (v_feat.get("reviewed_by") if isinstance(v_feat, dict) else None)
                stored_at = row.get("reviewed_at") or (v_feat.get("reviewed_at") if isinstance(v_feat, dict) else None)

                # 3. Rich merchant and location extraction
                merchant = (
                    row.get("merchant")
                    or v_feat.get("merchant")
                    or (f"{v_feat.get('merchant_category', 'Online')} Merchant" if v_feat.get("merchant_category") else "Global Payment Terminal")
                )
                merchant_category = (
                    row.get("merchant_category")
                    or row.get("category")
                    or v_feat.get("merchant_category")
                    or v_feat.get("category")
                    or "Online Retail"
                )
                location = (
                    row.get("location")
                    or v_feat.get("location")
                    or ("International Terminal" if v_feat.get("international_transaction") == 1 else "Domestic POS Gateway")
                )
                card_last4 = str(row.get("card_last4") or v_feat.get("card_last4") or "4242")

                # 4. Top contributors and summary narrative extraction
                top_contribs = row.get("top_contributors") or []
                summary_narr = row.get("summary_narrative") or []
                if not top_contribs and row.get("shap_explanations"):
                    shap_dict = row.get("shap_explanations")
                    if isinstance(shap_dict, dict):
                        sorted_items = sorted(shap_dict.items(), key=lambda kv: abs(float(kv[1])), reverse=True)[:5]
                        top_contribs = [
                            {
                                "feature": k,
                                "display_name": k.replace("_", " ").title(),
                                "shap_value": float(v),
                                "impact": "INCREASED_RISK" if float(v) > 0 else "REDUCED_RISK",
                                "direction": "RISK_INCREASING" if float(v) > 0 else "RISK_DECREASING",
                                "description": f"{k.replace('_', ' ').title()} {'increased' if float(v) > 0 else 'reduced'} fraud probability.",
                                "human_readable": f"{k.replace('_', ' ').title()}: {abs(float(v)):.2f} impact",
                            }
                            for k, v in sorted_items
                        ]

                records.append({
                    "id": str(row.get("id")),
                    "transaction_time": str(row.get("transaction_time")),
                    "amount": float(row.get("amount") or 0.0),
                    "fraud_probability": prob,
                    "is_flagged": is_fl,
                    "risk_level": risk_level,
                    "review_status": review_status,
                    "merchant": merchant,
                    "merchant_category": merchant_category,
                    "location": location,
                    "category": merchant_category,
                    "card_last4": card_last4,
                    "model_version": row.get("model_version") or "xgboost-tree-explainer-v2.0",
                    "analyst_notes": stored_notes,
                    "reviewed_by": stored_by,
                    "reviewed_at": stored_at,
                    "shap_explanations": row.get("shap_explanations") or {},
                    "top_contributors": top_contribs,
                    "summary_narrative": summary_narr,
                    "v_features": v_feat,
                })

            return records, total_count, total_pages, "SUPABASE_POSTGRESQL", "Data Source: Supabase PostgreSQL"

        except Exception as sb_err:
            logger.warning(f"Supabase query failed, falling back to SQLite: {sb_err}")

    # Fallback to local SQLite engine
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses: List[str] = []
        params: List[Any] = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append(
                "(id LIKE ? OR merchant LIKE ? OR location LIKE ? OR card_last4 LIKE ? OR category LIKE ? OR merchant_category LIKE ?)"
            )
            params.extend([term, term, term, term, term, term])

        if risk_level:
            where_clauses.append("risk_level = ?")
            params.append(risk_level.upper())

        if is_flagged is not None:
            where_clauses.append("is_flagged = ?")
            params.append(1 if is_flagged else 0)

        if review_status:
            where_clauses.append("review_status = ?")
            params.append(review_status.upper())

        if start_date:
            where_clauses.append("transaction_time >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("transaction_time <= ?")
            params.append(end_date)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_sql = f"SELECT COUNT(*) FROM transactions {where_sql}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        total_pages = max(1, math.ceil(total_count / limit))
        offset = (page - 1) * limit

        allowed_sort_cols = {
            "transaction_time": "transaction_time",
            "amount": "amount",
            "fraud_probability": "fraud_probability",
            "risk_level": "risk_level",
            "created_at": "created_at",
        }
        order_col = allowed_sort_cols.get(sort_by, "transaction_time")
        order_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        query_sql = f"""
            SELECT * FROM transactions
            {where_sql}
            ORDER BY {order_col} {order_direction}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query_sql, params + [limit, offset])
        rows = cursor.fetchall()

        records = []
        for row in rows:
            shap_dict = {}
            if row["shap_explanations"]:
                try:
                    shap_dict = json.loads(row["shap_explanations"])
                except Exception:
                    pass

            top_contribs = []
            if row["top_contributors"]:
                try:
                    top_contribs = json.loads(row["top_contributors"])
                except Exception:
                    pass

            narratives = []
            if row["summary_narrative"]:
                try:
                    narratives = json.loads(row["summary_narrative"])
                except Exception:
                    pass

            records.append({
                "id": row["id"],
                "transaction_time": row["transaction_time"],
                "amount": float(row["amount"]),
                "fraud_probability": float(row["fraud_probability"]),
                "is_flagged": bool(row["is_flagged"]),
                "risk_level": row["risk_level"],
                "review_status": row["review_status"] or "PENDING",
                "merchant": row["merchant"],
                "merchant_category": row["merchant_category"] or row["category"] or "Online Retail",
                "location": row["location"],
                "category": row["category"],
                "card_last4": row["card_last4"],
                "model_version": row["model_version"] or "xgboost-tree-explainer-v2.0",
                "analyst_notes": row["analyst_notes"],
                "reviewed_by": row["reviewed_by"],
                "reviewed_at": row["reviewed_at"],
                "shap_explanations": shap_dict,
                "top_contributors": top_contribs,
                "summary_narrative": narratives,
            })

        conn.close()
        return records, total_count, total_pages, "SQLITE_FALLBACK", "Data Source: Local SQLite (Fallback)"

    except Exception as e:
        logger.error(f"Error querying transactions from database: {e}")
        return [], 0, 1, "SQLITE_FALLBACK", "Data Source: Local SQLite (Fallback)"


def get_transaction_by_id(client: Optional[Client], transaction_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single transaction by ID from Supabase if connected, else SQLite."""
    diag = check_database_connectivity(client)

    # Try Supabase if connected
    if client and diag["supabase_status"] == "CONNECTED":
        try:
            res = client.table("transactions").select("*").eq("id", transaction_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                v_feat = row.get("v_features") or {}
                prob = float(row.get("fraud_probability") or 0.0)
                is_fl = bool(row.get("is_flagged"))

                stored_risk = row.get("risk_level") or (v_feat.get("risk_level") if isinstance(v_feat, dict) else None)
                risk_level = (
                    stored_risk.upper()
                    if (stored_risk and str(stored_risk).upper() in ("LOW", "MEDIUM", "HIGH", "CRITICAL"))
                    else calculate_risk_level(prob)
                )
                stored_status = row.get("review_status") or (v_feat.get("review_status") if isinstance(v_feat, dict) else None)
                review_status = resolve_review_status(stored_status, is_fl)

                stored_notes = row.get("analyst_notes") or (v_feat.get("analyst_notes") if isinstance(v_feat, dict) else None)
                stored_by = row.get("reviewed_by") or (v_feat.get("reviewed_by") if isinstance(v_feat, dict) else None)
                stored_at = row.get("reviewed_at") or (v_feat.get("reviewed_at") if isinstance(v_feat, dict) else None)

                merchant = (
                    row.get("merchant")
                    or v_feat.get("merchant")
                    or (f"{v_feat.get('merchant_category', 'Online')} Merchant" if v_feat.get("merchant_category") else "Global Payment Terminal")
                )
                merchant_category = (
                    row.get("merchant_category")
                    or row.get("category")
                    or v_feat.get("merchant_category")
                    or v_feat.get("category")
                    or "Online Retail"
                )
                location = (
                    row.get("location")
                    or v_feat.get("location")
                    or ("International Terminal" if v_feat.get("international_transaction") == 1 else "Domestic POS Gateway")
                )
                card_last4 = str(row.get("card_last4") or v_feat.get("card_last4") or "4242")

                top_contribs = row.get("top_contributors") or []
                summary_narr = row.get("summary_narrative") or []
                if not top_contribs and row.get("shap_explanations"):
                    shap_dict = row.get("shap_explanations")
                    if isinstance(shap_dict, dict):
                        sorted_items = sorted(shap_dict.items(), key=lambda kv: abs(float(kv[1])), reverse=True)[:5]
                        top_contribs = [
                            {
                                "feature": k,
                                "display_name": k.replace("_", " ").title(),
                                "shap_value": float(v),
                                "impact": "INCREASED_RISK" if float(v) > 0 else "REDUCED_RISK",
                                "direction": "RISK_INCREASING" if float(v) > 0 else "RISK_DECREASING",
                                "description": f"{k.replace('_', ' ').title()} {'increased' if float(v) > 0 else 'reduced'} fraud probability.",
                                "human_readable": f"{k.replace('_', ' ').title()}: {abs(float(v)):.2f} impact",
                            }
                            for k, v in sorted_items
                        ]

                return {
                    "id": str(row.get("id")),
                    "transaction_time": str(row.get("transaction_time")),
                    "amount": float(row.get("amount") or 0.0),
                    "fraud_probability": prob,
                    "is_flagged": is_fl,
                    "risk_level": risk_level,
                    "review_status": review_status,
                    "merchant": merchant,
                    "merchant_category": merchant_category,
                    "location": location,
                    "category": merchant_category,
                    "card_last4": card_last4,
                    "model_version": row.get("model_version") or "xgboost-tree-explainer-v2.0",
                    "analyst_notes": stored_notes,
                    "reviewed_by": stored_by,
                    "reviewed_at": stored_at,
                    "shap_explanations": row.get("shap_explanations") or {},
                    "top_contributors": top_contribs,
                    "summary_narrative": summary_narr,
                    "review_history": [],
                }
        except Exception as e:
            logger.warning(f"Supabase fetch for {transaction_id} failed: {e}")

    # Fallback to SQLite
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        cursor.execute(
            "SELECT * FROM transaction_reviews WHERE transaction_id = ? ORDER BY created_at DESC",
            (transaction_id,),
        )
        reviews = [
            {
                "id": r["id"],
                "transaction_id": r["transaction_id"],
                "previous_status": r["previous_status"],
                "new_status": r["new_status"],
                "analyst_notes": r["analyst_notes"],
                "reviewed_by": r["reviewed_by"],
                "created_at": r["created_at"],
            }
            for r in cursor.fetchall()
        ]

        shap_dict = {}
        if row["shap_explanations"]:
            try:
                shap_dict = json.loads(row["shap_explanations"])
            except Exception:
                pass

        top_contribs = []
        if row["top_contributors"]:
            try:
                top_contribs = json.loads(row["top_contributors"])
            except Exception:
                pass

        narratives = []
        if row["summary_narrative"]:
            try:
                narratives = json.loads(row["summary_narrative"])
            except Exception:
                pass

        record = {
            "id": row["id"],
            "transaction_time": row["transaction_time"],
            "amount": float(row["amount"]),
            "fraud_probability": float(row["fraud_probability"]),
            "is_flagged": bool(row["is_flagged"]),
            "risk_level": row["risk_level"],
            "review_status": row["review_status"] or "PENDING",
            "merchant": row["merchant"],
            "merchant_category": row["merchant_category"] or row["category"] or "Online Retail",
            "location": row["location"],
            "category": row["category"],
            "card_last4": row["card_last4"],
            "model_version": row["model_version"] or "xgboost-tree-explainer-v2.0",
            "analyst_notes": row["analyst_notes"],
            "reviewed_by": row["reviewed_by"],
            "reviewed_at": row["reviewed_at"],
            "shap_explanations": shap_dict,
            "top_contributors": top_contribs,
            "summary_narrative": narratives,
            "review_history": reviews,
        }
        conn.close()
        return record
    except Exception as e:
        logger.error(f"Error fetching transaction {transaction_id}: {e}")
        return None


VALID_REVIEW_TRANSITIONS = {
    "PENDING": ["UNDER_REVIEW", "CONFIRMED_FRAUD", "LEGITIMATE", "ESCALATED"],
    "UNDER_REVIEW": ["CONFIRMED_FRAUD", "LEGITIMATE", "ESCALATED", "PENDING"],
    "CONFIRMED_FRAUD": ["ESCALATED", "UNDER_REVIEW", "LEGITIMATE"],
    "LEGITIMATE": ["UNDER_REVIEW", "CONFIRMED_FRAUD", "ESCALATED"],
    "ESCALATED": ["CONFIRMED_FRAUD", "LEGITIMATE", "UNDER_REVIEW"],
}


def update_transaction_review(
    client: Optional[Client],
    transaction_id: str,
    new_status: str,
    analyst_notes: Optional[str] = None,
    reviewed_by: str = "analyst@sentinel.internal",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Updates the review status and notes for a transaction.
    Validates state transitions and synchronizes across available stores.
    """
    new_status_upper = new_status.upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT review_status FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None, f"Transaction with ID '{transaction_id}' was not found in the database."

        current_status = row["review_status"] or "PENDING"

        allowed_next = VALID_REVIEW_TRANSITIONS.get(current_status, [])
        if new_status_upper != current_status and new_status_upper not in allowed_next:
            conn.close()
            return None, f"Invalid status transition from {current_status} to {new_status_upper}. Allowed: {allowed_next}"

        # 1. Update SQLite
        cursor.execute(
            """
            UPDATE transactions
            SET review_status = ?,
                analyst_notes = ?,
                reviewed_by = ?,
                reviewed_at = ?
            WHERE id = ?
            """,
            (new_status_upper, analyst_notes, reviewed_by, now_iso, transaction_id),
        )

        review_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO transaction_reviews (
                id, transaction_id, previous_status, new_status, analyst_notes, reviewed_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (review_id, transaction_id, current_status, new_status_upper, analyst_notes, reviewed_by, now_iso),
        )

        conn.commit()
        conn.close()

        # 2. Synchronize with Supabase if available
        if client:
            try:
                # Fetch existing v_features to preserve attributes while persisting review status
                curr = client.table("transactions").select("v_features").eq("id", transaction_id).limit(1).execute()
                v_feat = curr.data[0].get("v_features") or {} if (curr.data and len(curr.data) > 0) else {}
                v_feat["review_status"] = new_status_upper
                v_feat["analyst_notes"] = analyst_notes
                v_feat["reviewed_by"] = reviewed_by
                v_feat["reviewed_at"] = now_iso

                # Attempt full column update; fall back to v_features JSONB if columns are unmigrated
                try:
                    client.table("transactions").update({
                        "review_status": new_status_upper,
                        "analyst_notes": analyst_notes,
                        "reviewed_by": reviewed_by,
                        "reviewed_at": now_iso,
                        "v_features": v_feat,
                    }).eq("id", transaction_id).execute()
                except Exception as up_err:
                    err_str = str(up_err)
                    if "42703" in err_str or "does not exist" in err_str.lower() or "schema cache" in err_str.lower():
                        client.table("transactions").update({
                            "v_features": v_feat,
                        }).eq("id", transaction_id).execute()
                    else:
                        raise up_err
            except Exception as sb_err:
                logger.warning(f"Could not sync review update to Supabase: {sb_err}")

        updated_record = get_transaction_by_id(client, transaction_id)
        return updated_record, None

    except Exception as e:
        logger.error(f"Failed to update transaction review for {transaction_id}: {e}")
        return None, str(e)


def calculate_analytics(client: Optional[Client], time_range: str = "7d") -> Dict[str, Any]:
    """
    Computes system-wide fraud analytics and telemetry aggregations from the authoritative store.
    Clearly distinguishes predicted fraud (is_flagged) from analyst-confirmed fraud (review_status='CONFIRMED_FRAUD').
    """
    range_map = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    delta = range_map.get(time_range, timedelta(days=7))
    start_time = (datetime.now(timezone.utc) - delta).isoformat()

    diag = check_database_connectivity(client)

    # If Supabase is connected and authoritative, aggregate from Supabase
    if client and diag["authoritative_source"] == "SUPABASE_POSTGRESQL":
        try:
            res = client.table("transactions").select("*").gte("transaction_time", start_time).execute()
            rows = res.data or []

            total = len(rows)
            flagged = 0
            not_flagged = 0
            confirmed_fraud = 0
            confirmed_legitimate = 0
            awaiting_review = 0
            under_review = 0
            escalated = 0

            risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            status_dist = {
                "PENDING": 0,
                "NOT_FLAGGED": 0,
                "UNDER_REVIEW": 0,
                "CONFIRMED_FRAUD": 0,
                "LEGITIMATE": 0,
                "ESCALATED": 0,
            }

            for r in rows:
                prob = float(r.get("fraud_probability") or 0.0)
                is_fl = bool(r.get("is_flagged"))
                if is_fl:
                    flagged += 1
                else:
                    not_flagged += 1

                v_feat = r.get("v_features") or {} if isinstance(r.get("v_features"), dict) else {}
                stored_st = r.get("review_status") or v_feat.get("review_status")
                st = resolve_review_status(stored_st, is_fl)
                if st in status_dist:
                    status_dist[st] += 1

                if st == "CONFIRMED_FRAUD":
                    confirmed_fraud += 1
                elif st == "LEGITIMATE":
                    confirmed_legitimate += 1
                elif is_fl and st == "PENDING":
                    awaiting_review += 1
                elif st == "UNDER_REVIEW":
                    under_review += 1
                elif st == "ESCALATED":
                    escalated += 1

                stored_rk = r.get("risk_level") or v_feat.get("risk_level")
                rk = (
                    stored_rk.upper()
                    if (stored_rk and str(stored_rk).upper() in risk_dist)
                    else calculate_risk_level(prob)
                )
                risk_dist[rk] += 1

            fraud_pct = round((flagged / total * 100), 2) if total > 0 else 0.0
            reviewed_total = confirmed_fraud + confirmed_legitimate
            detection_rate = round((confirmed_fraud / reviewed_total * 100), 2) if reviewed_total > 0 else 0.0

            return {
                "time_range": time_range,
                "total_transactions": total,
                "total_flagged_transactions": flagged,
                "total_not_flagged_transactions": not_flagged,
                "total_confirmed_fraud": confirmed_fraud,
                "total_confirmed_legitimate": confirmed_legitimate,
                "total_legitimate": confirmed_legitimate,
                "transactions_awaiting_review": awaiting_review,
                "transactions_under_review": under_review,
                "transactions_escalated": escalated,
                "fraud_detection_rate": detection_rate,
                "fraud_percentage": fraud_pct,
                "risk_distribution": risk_dist,
                "review_status_distribution": status_dist,
                "volume_over_time": [],
                "fraud_volume_over_time": [],
                "data_source": "SUPABASE_POSTGRESQL",
                "data_source_label": "Data Source: Supabase PostgreSQL",
            }
        except Exception as sb_err:
            logger.warning(f"Supabase analytics query failed, falling back to SQLite: {sb_err}")

    # Fallback aggregation from SQLite
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM transactions
            WHERE transaction_time >= ?
            ORDER BY transaction_time ASC
            """,
            (start_time,),
        )
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        flagged = sum(1 for r in rows if r["is_flagged"] == 1)
        confirmed_fraud = sum(1 for r in rows if (r["review_status"] or "").upper() == "CONFIRMED_FRAUD")
        legitimate = sum(1 for r in rows if (r["review_status"] or "").upper() == "LEGITIMATE")
        awaiting_review = sum(1 for r in rows if r["is_flagged"] == 1 and (r["review_status"] or "").upper() in ("PENDING", "UNDER_REVIEW"))

        fraud_pct = round((flagged / total * 100), 2) if total > 0 else 0.0
        reviewed_total = confirmed_fraud + legitimate
        detection_rate = round((confirmed_fraud / reviewed_total * 100), 2) if reviewed_total > 0 else 0.0

        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for r in rows:
            rk = (r["risk_level"] or "LOW").upper()
            if rk in risk_dist:
                risk_dist[rk] += 1
            else:
                risk_dist["MEDIUM"] += 1

        time_series_volume: Dict[str, Dict[str, Any]] = {}
        time_series_fraud: Dict[str, Dict[str, Any]] = {}

        for r in rows:
            tx_time_str = r["transaction_time"]
            bucket = tx_time_str[:13] + ":00:00Z" if time_range == "24h" else tx_time_str[:10]
            amt = float(r["amount"] or 0.0)

            if bucket not in time_series_volume:
                time_series_volume[bucket] = {"timestamp": bucket, "count": 0, "volume_amount": 0.0}
            time_series_volume[bucket]["count"] += 1
            time_series_volume[bucket]["volume_amount"] = round(time_series_volume[bucket]["volume_amount"] + amt, 2)

            if r["is_flagged"] == 1:
                if bucket not in time_series_fraud:
                    time_series_fraud[bucket] = {"timestamp": bucket, "flagged_count": 0, "flagged_amount": 0.0}
                time_series_fraud[bucket]["flagged_count"] += 1
                time_series_fraud[bucket]["flagged_amount"] = round(time_series_fraud[bucket]["flagged_amount"] + amt, 2)

        return {
            "time_range": time_range,
            "total_transactions": total,
            "total_flagged_transactions": flagged,
            "total_confirmed_fraud": confirmed_fraud,
            "total_legitimate": legitimate,
            "transactions_awaiting_review": awaiting_review,
            "fraud_detection_rate": detection_rate,
            "fraud_percentage": fraud_pct,
            "risk_distribution": risk_dist,
            "volume_over_time": list(time_series_volume.values()),
            "fraud_volume_over_time": list(time_series_fraud.values()),
            "data_source": "SQLITE_FALLBACK",
            "data_source_label": "Data Source: Local SQLite (Fallback)",
        }

    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        return {
            "time_range": time_range,
            "total_transactions": 0,
            "total_flagged_transactions": 0,
            "total_confirmed_fraud": 0,
            "total_legitimate": 0,
            "transactions_awaiting_review": 0,
            "fraud_detection_rate": 0.0,
            "fraud_percentage": 0.0,
            "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "volume_over_time": [],
            "fraud_volume_over_time": [],
            "data_source": "SQLITE_FALLBACK",
            "data_source_label": "Data Source: Local SQLite (Fallback)",
        }


def fetch_all_recent_transactions(client: Optional[Client], limit: int = 50) -> List[Dict[str, Any]]:
    records, _, _, _, _ = query_transactions(client=client, page=1, limit=limit, sort_by="transaction_time", sort_order="desc")
    return records
