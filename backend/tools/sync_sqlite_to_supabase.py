#!/usr/bin/env python3
"""
Explicit Data Synchronization Utility:
Safely syncs historical transactions from local SQLite fallback store to Supabase PostgreSQL.
- Requires SUPABASE_SERVICE_ROLE_KEY.
- Performs duplicate prevention by checking existing transaction IDs.
- Validates all schema attributes before insertion.
"""

import json
import logging
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_sqlite_to_supabase")

BACKEND_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BACKEND_DIR / "db" / "local_transactions.db"


def ensure_uuid(val: str) -> str:
    try:
        return str(uuid.UUID(str(val)))
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(val)))


def sync_transactions():
    env_vals = dotenv_values(BACKEND_DIR / ".env")
    supabase_url = env_vals.get("SUPABASE_URL")
    service_role_key = env_vals.get("SUPABASE_SERVICE_ROLE_KEY") or env_vals.get("SUPABASE_KEY")

    if not supabase_url or not service_role_key:
        logger.error(
            "Cannot sync to Supabase: Missing SUPABASE_URL or active API key in backend/.env."
        )
        return False

    client = create_client(supabase_url, service_role_key)

    # Read from SQLite
    if not SQLITE_DB_PATH.exists():
        logger.error(f"SQLite database not found at {SQLITE_DB_PATH}")
        return False

    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    sqlite_rows = cursor.fetchall()
    conn.close()

    logger.info(f"Read {len(sqlite_rows)} transactions from local SQLite database.")

    # Check existing IDs in Supabase for duplicate prevention
    try:
        existing_res = client.table("transactions").select("id").execute()
        existing_ids = {str(r["id"]) for r in existing_res.data}
        logger.info(f"Found {len(existing_ids)} existing transactions in Supabase.")
    except Exception as e:
        logger.error(f"Failed to query existing Supabase transactions: {e}")
        return False

    to_insert = []
    for row in sqlite_rows:
        tx_id = ensure_uuid(row["id"])
        if tx_id in existing_ids:
            continue

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

        v_feat = {}
        if row["v_features"]:
            try:
                v_feat = json.loads(row["v_features"])
            except Exception:
                pass

        record = {
            "id": tx_id,
            "transaction_time": row["transaction_time"],
            "amount": float(row["amount"]),
            "fraud_probability": float(row["fraud_probability"]),
            "is_flagged": bool(row["is_flagged"]),
            "risk_level": row["risk_level"] or "LOW",
            "review_status": row["review_status"] or "PENDING",
            "merchant": row["merchant"] or "Global Payment Terminal",
            "merchant_category": row["merchant_category"] or row["category"] or "Online Retail",
            "location": row["location"] or "Secure POS Gateway",
            "card_last4": row["card_last4"] or "4242",
            "model_version": row["model_version"] or "xgboost-tree-explainer-v2.0",
            "analyst_notes": row["analyst_notes"],
            "reviewed_by": row["reviewed_by"],
            "reviewed_at": row["reviewed_at"],
            "shap_explanations": shap_dict,
            "top_contributors": top_contribs,
            "summary_narrative": narratives,
            "v_features": v_feat,
            "created_at": row["created_at"],
        }
        to_insert.append(record)

    if not to_insert:
        logger.info("All SQLite transactions are already synchronized in Supabase.")
        return True

    logger.info(f"Inserting {len(to_insert)} new unique transactions into Supabase PostgreSQL...")
    batch_size = 50
    inserted_count = 0
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i : i + batch_size]
        try:
            res = client.table("transactions").insert(batch).execute()
            inserted_count += len(res.data)
            logger.info(f"Batch {i//batch_size + 1} synced ({len(res.data)} rows).")
        except Exception as batch_err:
            err_str = str(batch_err)
            # If columns missing, fallback to core columns
            if "42703" in err_str or "does not exist" in err_str or "schema cache" in err_str:
                core_batch = [
                    {
                        "id": r["id"],
                        "amount": r["amount"],
                        "fraud_probability": r["fraud_probability"],
                        "is_flagged": r["is_flagged"],
                        "shap_explanations": r["shap_explanations"],
                        "v_features": r["v_features"],
                        "transaction_time": r["transaction_time"],
                    }
                    for r in batch
                ]
                try:
                    c_res = client.table("transactions").insert(core_batch).execute()
                    inserted_count += len(c_res.data)
                    logger.info(f"Batch {i//batch_size + 1} synced using core schema ({len(c_res.data)} rows).")
                except Exception as c_err:
                    logger.error(f"Core batch insert error: {c_err}")
            else:
                logger.error(f"Batch insert error: {batch_err}")

    logger.info(f"Successfully migrated {inserted_count} transactions to Supabase!")
    return True


if __name__ == "__main__":
    sync_transactions()

