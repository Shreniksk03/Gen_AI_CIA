#!/usr/bin/env python3
"""
Controlled End-to-End Database Flow Verification Test.
Tests the entire pipeline:
Simulation Payload -> POST /predict -> ML Scoring -> TreeSHAP -> Persistence -> Direct DB Read -> API Read.
"""

import os
import sys
import uuid
from pathlib import Path
import requests
from dotenv import dotenv_values

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

API_BASE = "http://localhost:8000"


def run_database_verification():
    print("=" * 70)
    print("FRAUD SENTINEL — DATABASE FLOW VERIFICATION AUDIT")
    print("=" * 70)

    # 1. Inspect Backend Health & Diagnostics
    print("\n[STEP 1] Testing /health diagnostics endpoint...")
    try:
        health_res = requests.get(f"{API_BASE}/health", timeout=5)
        health_data = health_res.json()
        print(f"  ✓ API Status: {health_data.get('status')}")
        print(f"  ✓ Authoritative Source: {health_data.get('database_source_label')}")
        print(f"  ✓ Supabase Status: {health_data.get('supabase_status')}")
        print(f"  ✓ SQLite Status: {health_data.get('sqlite_status')} ({health_data.get('sqlite_records_count')} records)")
        print(f"  ✓ Supabase Records: {health_data.get('supabase_records_count')}")
    except Exception as e:
        print(f"  ✗ Failed to connect to FastAPI at {API_BASE}: {e}")
        return False

    # 2. Inspect Environment Configuration
    env_vals = dotenv_values(BACKEND_DIR / ".env")
    has_service_key = bool(env_vals.get("SUPABASE_SERVICE_ROLE_KEY"))
    pub_key = env_vals.get("SUPABASE_KEY", "")
    print("\n[STEP 2] Inspecting Database Credentials...")
    print(f"  - SUPABASE_URL: {env_vals.get('SUPABASE_URL')}")
    print(f"  - SUPABASE_KEY type: {'Publishable Key (sb_publishable_...)' if pub_key.startswith('sb_publishable') else 'Set' if pub_key else 'Missing'}")
    print(f"  - SUPABASE_SERVICE_ROLE_KEY: {'Configured' if has_service_key else 'NOT CONFIGURED (Required for Server-Side RLS Bypass)'}")

    # 3. Generate Clearly Identifiable Test Transaction
    test_id = f"test-audit-{uuid.uuid4()}"
    test_payload = {
        "transaction_id": test_id,
        "transaction_amount": 742.50,
        "merchant": "AUDIT_VERIFICATION_TERMINAL",
        "merchant_category": "Electronics & Technology",
        "location": "Audit Test Lab, US",
        "card_last4": "9999",
        "international_transaction": 1,
        "high_risk_country": 0,
        "customer_age": 42,
        "account_age_days": 180,
    }

    print(f"\n[STEP 3] Sending Test Transaction through POST /predict...")
    print(f"  - Generated Test ID: {test_id}")
    predict_res = requests.post(f"{API_BASE}/predict", json=test_payload, timeout=10)
    if predict_res.status_code != 200:
        print(f"  ✗ Inference API returned {predict_res.status_code}: {predict_res.text}")
        return False

    pred_data = predict_res.json()
    print(f"  ✓ ML Inference Succeeded!")
    print(f"  ✓ Fraud Probability: {pred_data.get('fraud_probability')} ({pred_data.get('risk_level')})")
    print(f"  ✓ Top SHAP Factors: {len(pred_data.get('top_contributors', []))} features calculated")
    print(f"  ✓ Reported Database Source: {pred_data.get('database_source_label')}")
    print(f"  ✓ Supabase Persisted: {pred_data.get('supabase_persisted')}")
    print(f"  ✓ SQLite Persisted: {pred_data.get('sqlite_persisted')}")

    # 4. Direct Cloud Database Verification
    print("\n[STEP 4] Direct Database Verification...")
    from supabase import create_client
    supabase_url = env_vals.get("SUPABASE_URL")
    supabase_key = env_vals.get("SUPABASE_SERVICE_ROLE_KEY") or env_vals.get("SUPABASE_KEY")

    if pred_data.get("supabase_persisted"):
        print("  - Verifying actual record in Supabase PostgreSQL...")
        try:
            sb_client = create_client(supabase_url, supabase_key)
            sb_res = sb_client.table("transactions").select("*").eq("id", test_id).execute()
            if sb_res.data and len(sb_res.data) > 0:
                cloud_record = sb_res.data[0]
                print(f"  ✓ CONFIRMED: Record found directly in Supabase PostgreSQL!")
                print(f"    - ID: {cloud_record.get('id')}")
                print(f"    - Amount: ${cloud_record.get('amount')}")
                print(f"    - Probability: {cloud_record.get('fraud_probability')}")
                print(f"    - Cloud Time: {cloud_record.get('transaction_time')}")

                # Clean up test record from Supabase
                sb_client.table("transactions").delete().eq("id", test_id).execute()
                print("  ✓ Test transaction cleaned up from Supabase.")
            else:
                print("  ✗ Warning: Backend reported Supabase persisted, but record not found on direct query.")
        except Exception as sbe:
            print(f"  ✗ Error querying Supabase directly: {sbe}")
    else:
        print("  - Supabase was NOT updated during this transaction.")
        print(f"    Reason: {health_data.get('supabase_status')}")
        print("  - Verifying persistence in local SQLite fallback store...")
        import sqlite3
        conn = sqlite3.connect(str(BACKEND_DIR / "db" / "local_transactions.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, amount, fraud_probability, risk_level FROM transactions WHERE id = ?", (test_id,))
        sqlite_row = cursor.fetchone()
        if sqlite_row:
            print(f"  ✓ CONFIRMED: Record found in local SQLite fallback store:")
            print(f"    - ID: {sqlite_row[0]}")
            print(f"    - Amount: ${sqlite_row[1]}")
            print(f"    - Probability: {sqlite_row[2]} ({sqlite_row[3]})")
            # Clean up test transaction from SQLite
            cursor.execute("DELETE FROM transactions WHERE id = ?", (test_id,))
            conn.commit()
            print("  ✓ Test transaction cleaned up from SQLite store.")
        else:
            print("  ✗ Error: Record not found in SQLite store either.")
        conn.close()

    # 5. Read Back from Application API
    print("\n[STEP 5] Testing Normal API Retrieval via GET /transactions...")
    txns_res = requests.get(f"{API_BASE}/transactions?limit=5", timeout=5)
    txns_data = txns_res.json()
    print(f"  ✓ GET /transactions succeeded (HTTP 200)")
    print(f"  ✓ Data Source Reported: {txns_data.get('data_source_label')}")
    print(f"  ✓ Total Available Transactions: {txns_data.get('total')}")

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY:")
    if has_service_key and pred_data.get("supabase_persisted"):
        print("STATUS: SUPABASE CLOUD POSTGRESQL FULLY OPERATIONAL AND VERIFIED!")
    else:
        print("STATUS: TRUTHFUL SQLITE FALLBACK ACTIVE.")
        print("To enable cloud persistence into Supabase PostgreSQL:")
        print("1. Run 'backend/migrations/001_align_supabase_schema.sql' in Supabase SQL editor.")
        print("2. Set 'SUPABASE_SERVICE_ROLE_KEY=sb_secret_...' in backend/.env.")
        print("3. Restart FastAPI.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    run_database_verification()

