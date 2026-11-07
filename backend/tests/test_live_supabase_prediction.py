"""
backend/tests/test_live_supabase_prediction.py
End-to-end verification of live prediction, ML scoring, SHAP attributions,
and authoritative persistence to Supabase Cloud PostgreSQL.
"""

import json
import os
import sys
import urllib.request
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in path and load .env
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

for env_file in [backend_dir / ".env", Path(".env")]:
    if env_file.is_file():
        load_dotenv(env_file, override=True)
        break

from services.db_service import get_supabase_client, check_database_connectivity, ensure_uuid


def run_test():
    print("=" * 75)
    print("FRAUD SENTINEL — LIVE PREDICTION & SUPABASE CLOUD PERSISTENCE TEST")
    print("=" * 75)

    client = get_supabase_client()
    diag = check_database_connectivity(client)

    print("\n[STEP 1] DATABASE CONNECTIVITY & PERMISSION AUDIT:")
    print(f"  • Authoritative Source:       {diag['authoritative_source']}")
    print(f"  • Label:                      {diag['authoritative_source_label']}")
    print(f"  • Supabase Status:            {diag['supabase_status']}")
    print(f"  • Supabase Writable:          {diag['supabase_writable']}")
    print(f"  • Supabase Current Rows:      {diag['supabase_count']}")
    print(f"  • SQLite Fallback Rows:       {diag['sqlite_count']}")

    has_service_key = diag.get("has_service_key", False)
    if not has_service_key or not diag.get("supabase_writable", False):
        print("\n" + "!" * 75)
        print("⚠️  PERMISSION BLOCKER DETECTED:")
        print("   Supabase is currently running in READ_ONLY fallback mode.")
        print("   Reason: SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env.")
        print("   Row-Level Security (RLS) on public.transactions will reject the INSERT.")
        print("!" * 75)

    # Generate unique test transaction
    test_uuid = str(uuid.uuid4())
    print(f"\n[STEP 2] GENERATING UNIQUE TEST TRANSACTION:")
    print(f"  • Transaction UUID:           {test_uuid}")

    test_payload = {
        "transaction_id": test_uuid,
        "amount": 1850.00,
        "merchant": "Sentinel Verification Terminal",
        "merchant_category": "Electronics",
        "location": "New York, USA",
        "card_last4": "5521",
        "category": "Retail",
        # Sample tabular features
        "transaction_day_of_week": "Friday",
        "customer_gender": "Female",
        "customer_state": "NY",
        "transaction_channel": "POS",
        "device_type": "Mobile",
        "browser": "Chrome",
        "email_domain": "gmail.com",
    }

    # Call FastAPI /predict
    print("\n[STEP 3] CALLING FASTAPI POST /predict:")
    api_url = "http://localhost:8000/predict"
    req_data = json.dumps(test_payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_code = resp.getcode()
            resp_body = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ❌ API call failed: {e}")
        return False

    print(f"  ✓ API Response Code:          {resp_code} OK")
    print(f"  • Returned Transaction UUID:  {resp_body.get('transaction_id')}")
    print(f"  • Fraud Probability:          {resp_body.get('fraud_probability') * 100:.2f}%")
    print(f"  • Risk Level:                 {resp_body.get('risk_level')}")
    print(f"  • Is Flagged:                 {resp_body.get('is_flagged')}")

    # Verify SHAP
    shap_vals = resp_body.get("shap_values", {})
    top_contribs = resp_body.get("top_contributors", [])
    print(f"  • SHAP Attributions Generated:{len(shap_vals)} features calculated")
    print(f"  • Top Contributors:           {len(top_contribs)} key drivers extracted")

    # Verify persistence report
    sb_persisted = resp_body.get("supabase_persisted", False)
    sql_persisted = resp_body.get("sqlite_persisted", False)
    reported_source = resp_body.get("database_source", "UNKNOWN")

    print(f"\n[STEP 4] PERSISTENCE TELEMETRY FROM BACKEND:")
    print(f"  • Database Source Reported:   {reported_source}")
    print(f"  • Supabase Persisted:         {sb_persisted}")
    print(f"  • SQLite Persisted:           {sql_persisted}")

    # Verify direct query to Supabase
    print(f"\n[STEP 5] DIRECT SUPABASE TABLE QUERY BY UUID ({test_uuid}):")
    found_in_supabase = False
    if client:
        try:
            sb_query = client.table("transactions").select("*").eq("id", test_uuid).execute()
            if sb_query.data and len(sb_query.data) > 0:
                found_in_supabase = True
                print("  ✓ SUCCESS: Record verified directly in Supabase public.transactions!")
                print(f"    Supabase record: {sb_query.data[0]}")
            else:
                print("  ❌ NOT FOUND in Supabase public.transactions table (0 rows matching UUID).")
        except Exception as e:
            print(f"  ❌ Supabase SELECT failed: {e}")

    # Verify GET /transactions/{id}
    print(f"\n[STEP 6] DASHBOARD API RETRIEVAL (GET /transactions/{test_uuid}):")
    try:
        get_req = urllib.request.Request(f"http://localhost:8000/transactions/{test_uuid}")
        with urllib.request.urlopen(get_req, timeout=5) as g_resp:
            get_data = json.loads(g_resp.read().decode("utf-8"))
            print(f"  ✓ Successfully fetched from API: ID={get_data.get('id')}, Amount=${get_data.get('amount')}")
    except Exception as e:
        print(f"  ❌ GET /transactions/{test_uuid} failed: {e}")

    print("\n" + "=" * 75)
    if found_in_supabase:
        print("🎉 ALL VERIFICATION CRITERIA MET: RECORD IS LIVE IN SUPABASE POSTGRESQL!")
    else:
        print("⚠️  ACTION REQUIRED: Transaction was persisted to SQLite fallback.")
        print("   To enable direct Supabase writes, provide SUPABASE_SERVICE_ROLE_KEY in backend/.env")
    print("=" * 75)
    return found_in_supabase


if __name__ == "__main__":
    run_test()

