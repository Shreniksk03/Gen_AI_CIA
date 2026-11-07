"""
backend/tools/diagnose_supabase.py
Comprehensive backend-only diagnostic for Supabase PostgreSQL connectivity and permissions.
Checks:
1. Environment variable presence and configuration.
2. Supabase client initialization.
3. Read access (SELECT) on public.transactions.
4. Schema inspection (column presence).
5. Write access (INSERT) on public.transactions with a valid UUID.
6. Read-back verification (SELECT by UUID).
7. Delete cleanup.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in path and load .env
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

for env_file in [backend_dir / ".env", Path(".env")]:
    if env_file.is_file():
        load_dotenv(env_file, override=True)
        break


def mask_key(k: str | None) -> str:
    if not k:
        return "[NOT SET]"
    if len(k) <= 12:
        return k[:4] + "..." + k[-2:]
    return k[:6] + "..." + k[-4:]


def run_diagnostics():
    print("=" * 70)
    print("FRAUD SENTINEL — SUPABASE CLOUD DATABASE DEEP DIAGNOSTIC")
    print("=" * 70)

    # 1. Environment Inspection
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    print("\n[1] ENVIRONMENT CONFIGURATION:")
    print(f"  • SUPABASE_URL:               {supabase_url or '[NOT CONFIGURED]'}")
    print(f"  • SUPABASE_KEY (Anon):        {mask_key(supabase_key)}")
    print(f"  • SUPABASE_SERVICE_ROLE_KEY:  {mask_key(service_role_key)}")

    if not supabase_url:
        print("\n❌ CRITICAL: SUPABASE_URL is missing from environment.")
        return False

    active_key = service_role_key or supabase_key
    active_key_type = "SERVICE_ROLE (Trusted Server Secret)" if service_role_key else "ANON / PUBLISHABLE (Public Client Key)"

    if not active_key:
        print("\n❌ CRITICAL: Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_KEY is configured.")
        return False

    print(f"  • Active Client Key Type:     {active_key_type}")

    # 2. Client Initialization
    print("\n[2] SUPABASE CLIENT INITIALIZATION:")
    try:
        from supabase import create_client
        client = create_client(supabase_url, active_key)
        print("  ✓ Supabase client initialized successfully.")
    except Exception as e:
        print(f"  ❌ Client initialization failed: {e}")
        return False

    # 3. Read Access Test
    print("\n[3] READ ACCESS (SELECT) ON public.transactions:")
    try:
        res = client.table("transactions").select("id", count="exact").limit(5).execute()
        count = res.count if res.count is not None else len(res.data or [])
        print(f"  ✓ SELECT query succeeded! Current row count in public.transactions: {count}")
    except Exception as e:
        print(f"  ❌ SELECT query failed: {e}")
        return False

    # 4. Schema Column Inspection
    print("\n[4] SCHEMA COLUMN VERIFICATION ON public.transactions:")
    expected_columns = [
        "id", "transaction_time", "amount", "fraud_probability", "is_flagged",
        "risk_level", "review_status", "merchant", "merchant_category",
        "location", "card_last4", "model_version", "shap_explanations",
        "top_contributors", "summary_narrative", "v_features", "created_at"
    ]

    existing_cols = []
    missing_cols = []

    for col in expected_columns:
        try:
            client.table("transactions").select(col).limit(1).execute()
            existing_cols.append(col)
        except Exception:
            missing_cols.append(col)

    print(f"  • Present columns ({len(existing_cols)}): {', '.join(existing_cols)}")
    if missing_cols:
        print(f"  • Missing columns ({len(missing_cols)}): {', '.join(missing_cols)}")
        print("    ⚠️ Note: Missing columns require running backend/migrations/001_align_supabase_schema.sql")
    else:
        print("  ✓ All expected schema columns are present in Supabase!")

    # Check reviews table
    try:
        client.table("transaction_reviews").select("id").limit(1).execute()
        print("  ✓ public.transaction_reviews table exists.")
    except Exception:
        print("  ⚠️ public.transaction_reviews table does NOT exist yet (needs migration).")

    # 5. Write Access Test (INSERT with valid UUID)
    test_uuid = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    print(f"\n[5] WRITE ACCESS (INSERT) TEST:")
    print(f"  • Generating probe transaction with UUID: {test_uuid}")

    # Build payload using available columns
    if not missing_cols:
        probe_record = {
            "id": test_uuid,
            "amount": 99.99,
            "fraud_probability": 0.05,
            "is_flagged": False,
            "risk_level": "LOW",
            "merchant": "Diagnostic Probe Terminal",
            "merchant_category": "System Health",
            "location": "Local Host Test",
            "card_last4": "9999",
            "model_version": "diag-probe-v1.0",
            "review_status": "LEGITIMATE",
            "shap_explanations": {"Amount": 0.01, "Time": -0.02},
            "top_contributors": [],
            "summary_narrative": ["Automated connectivity probe"],
            "v_features": {"probe": True},
            "transaction_time": now_iso,
            "created_at": now_iso,
        }
    else:
        # Core columns only for unmigrated schema
        probe_record = {
            "id": test_uuid,
            "amount": 99.99,
            "fraud_probability": 0.05,
            "is_flagged": False,
            "shap_explanations": {"Amount": 0.01},
            "v_features": {"probe": True},
            "transaction_time": now_iso,
        }

    write_succeeded = False
    try:
        insert_res = client.table("transactions").insert(probe_record).execute()
        if insert_res.data and len(insert_res.data) > 0:
            write_succeeded = True
            print("  ✓ INSERT query succeeded! Supabase accepted the row.")
            print(f"    Returned record id: {insert_res.data[0].get('id')}")
    except Exception as e:
        err_msg = str(e)
        print(f"  ❌ INSERT query failed: {err_msg}")
        if "42501" in err_msg or "row-level security" in err_msg.lower():
            print("\n  🔍 DIAGNOSIS: RLS POLICY VIOLATION (Error 42501)")
            print("     Supabase rejected the insert because Row-Level Security is active and the client")
            print("     is authenticating with the publishable anon key instead of SUPABASE_SERVICE_ROLE_KEY.")
            print("     To fix this:")
            print("     1. Open your Supabase Dashboard -> Project Settings -> API.")
            print("     2. Copy the 'service_role' (secret) key.")
            print("     3. Set SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key> in backend/.env.")
        elif "22P02" in err_msg or "uuid" in err_msg.lower():
            print("\n  🔍 DIAGNOSIS: UUID FORMAT ERROR (Error 22P02)")
            print("     The table 'transactions' requires a valid UUID string for the 'id' column.")
        return False

    # 6. Read-Back Verification
    if write_succeeded:
        print(f"\n[6] READ-BACK VERIFICATION:")
        try:
            read_res = client.table("transactions").select("*").eq("id", test_uuid).limit(1).execute()
            if read_res.data and len(read_res.data) > 0:
                print(f"  ✓ Successfully read back transaction {test_uuid} from Supabase!")
                print(f"    Amount: ${read_res.data[0].get('amount')}, Fraud Probability: {read_res.data[0].get('fraud_probability')}")
            else:
                print(f"  ❌ Record was not found on read-back!")
        except Exception as e:
            print(f"  ❌ Read-back failed: {e}")

        # 7. Cleanup
        print(f"\n[7] CLEANUP TEST RECORD:")
        try:
            client.table("transactions").delete().eq("id", test_uuid).execute()
            print(f"  ✓ Test record {test_uuid} cleaned up from Supabase.")
        except Exception as e:
            print(f"  ⚠️ Cleanup warning: {e}")

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    return write_succeeded


if __name__ == "__main__":
    run_diagnostics()

