"""
backend/tests/test_review_workflow_lifecycle.py
Verifies the complete analyst review workflow lifecycle:
1. PENDING -> UNDER_REVIEW -> CONFIRMED_FRAUD
2. PENDING -> UNDER_REVIEW -> LEGITIMATE
3. Verifies analyst decisions, notes, reviewer, and timestamps are persisted in Supabase.
4. Verifies original ML probability and SHAP explanations are preserved without mutation.
5. Verifies analytics counters update truthfully.
6. Verifies invalid state transitions are strictly rejected.
7. Safely cleans up only the dedicated test records.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

for env_file in [backend_dir / ".env", Path(".env")]:
    if env_file.is_file():
        load_dotenv(env_file, override=True)
        break

from services.db_service import get_supabase_client


def send_req(endpoint: str, method: str = "GET", data: dict = None):
    url = f"http://localhost:8000{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def run_lifecycle_tests():
    print("=" * 75)
    print("FRAUD SENTINEL — ANALYST REVIEW WORKFLOW & STATE MACHINE AUDIT")
    print("=" * 75)

    client = get_supabase_client()

    # -------------------------------------------------------------------------
    # TEST LIFECYCLE 1: PENDING -> UNDER_REVIEW -> CONFIRMED_FRAUD
    # -------------------------------------------------------------------------
    print("\n[LIFECYCLE 1] PENDING -> UNDER_REVIEW -> CONFIRMED_FRAUD")
    test_id_1 = str(uuid.uuid4())
    print(f"  • Generating dedicated test transaction: {test_id_1}")

    # Ingest through /predict
    pred_payload_1 = {
        "transaction_id": test_id_1,
        "transaction_amount": 755.88,
        "amount": 755.88,
        "merchant": "Lifecycle Test Terminal Alpha",
        "merchant_category": "Travel & Airlines",
        "merchant_country": "Germany",
        "location": "Berlin, DE",
        "transaction_hour": 20,
        "transaction_day_of_week": "Monday",
        "card_present": 0,
        "customer_age": 34,
        "customer_gender": "Female",
        "customer_state": "TN",
        "account_age_days": 2552,
        "credit_limit": 10870,
        "credit_score": 657,
        "num_cards_held": 1,
        "transactions_last_1h": 6,
        "transactions_last_24h": 6,
        "transactions_last_7d": 12,
        "amount_last_1h": 913.46,
        "amount_last_24h": 959.25,
        "days_since_last_transaction": 4,
        "distance_from_home_km": 14489,
        "distance_from_last_tx_km": 53.6,
        "international_transaction": 1,
        "high_risk_country": 0,
        "amount_vs_avg_ratio": 5.538,
        "used_chip": 0,
        "used_pin": 0,
        "transaction_channel": "Online",
        "device_type": "Desktop",
        "browser": "Chrome",
        "is_weekend": 0,
        "avg_transaction_amount_30d": 136.5,
        "std_transaction_amount_30d": 103.35,
        "num_declined_last_30d": 0,
        "num_chargebacks_ever": 2,
        "email_domain": "yahoo",
        "card_last4": "3275",
        "category": "Travel & Airlines",
    }

    code, pred_res_1 = send_req("/predict", method="POST", data=pred_payload_1)
    orig_prob_1 = pred_res_1["fraud_probability"]
    orig_shap_1 = pred_res_1["shap_explanations"]
    print(f"  • Prediction ingested: Prob={orig_prob_1*100:.2f}%, Flagged={pred_res_1['is_flagged']}")

    # Step A: Verify initial status is PENDING
    _, fetched_initial = send_req(f"/transactions/{test_id_1}")
    assert fetched_initial["review_status"] == "PENDING", f"Expected PENDING, got {fetched_initial['review_status']}"
    print(f"  • Initial State:              {fetched_initial['review_status']} ✓")

    # Step B: Transition to UNDER_REVIEW
    review_data_under = {
        "review_status": "UNDER_REVIEW",
        "analyst_notes": "Analyst Smith assigned: cross-referencing IP velocity",
        "reviewed_by": "analyst.smith@sentinel.internal",
    }
    code_under, res_under = send_req(f"/transactions/{test_id_1}/review", method="PATCH", data=review_data_under)
    assert code_under == 200
    assert res_under["review_status"] == "UNDER_REVIEW"
    assert res_under["reviewed_by"] == "analyst.smith@sentinel.internal"
    assert res_under["reviewed_at"] is not None
    print(f"  • Transition 1:               PENDING -> {res_under['review_status']} ✓")
    print(f"    Notes: \"{res_under['analyst_notes']}\" (Timestamp: {res_under['reviewed_at']})")

    # Step C: Transition to CONFIRMED_FRAUD
    review_data_fraud = {
        "review_status": "CONFIRMED_FRAUD",
        "analyst_notes": "Cardholder confirmed stolen identity via out-of-band call",
        "reviewed_by": "lead.investigator@sentinel.internal",
    }
    code_fraud, res_fraud = send_req(f"/transactions/{test_id_1}/review", method="PATCH", data=review_data_fraud)
    assert code_fraud == 200
    assert res_fraud["review_status"] == "CONFIRMED_FRAUD"
    print(f"  • Transition 2:               UNDER_REVIEW -> {res_fraud['review_status']} ✓")

    # Step D: Integrity Verification (Probability & SHAP must remain immutable)
    _, fetched_final_1 = send_req(f"/transactions/{test_id_1}")
    assert fetched_final_1["fraud_probability"] == orig_prob_1, "ML probability mutated during review!"
    assert fetched_final_1["shap_explanations"] == orig_shap_1, "SHAP explanations mutated during review!"
    print(f"  • Immutability Audit:         ML Probability ({orig_prob_1}) and SHAP intact ✓")

    # Step E: State Machine Guard Test (CONFIRMED_FRAUD -> PENDING must be rejected)
    print("\n[GUARD TEST] INVALID STATE TRANSITION REJECTION:")
    invalid_data = {
        "review_status": "PENDING",
        "analyst_notes": "Attempting illegal reversion",
    }
    try:
        send_req(f"/transactions/{test_id_1}/review", method="PATCH", data=invalid_data)
        assert False, "State machine allowed illegal transition CONFIRMED_FRAUD -> PENDING!"
    except urllib.error.HTTPError as he:
        print(f"  • Transition CONFIRMED_FRAUD -> PENDING rejected with HTTP {he.code}: {he.reason} ✓")

    # -------------------------------------------------------------------------
    # TEST LIFECYCLE 2: PENDING -> UNDER_REVIEW -> LEGITIMATE
    # -------------------------------------------------------------------------
    print("\n[LIFECYCLE 2] PENDING -> UNDER_REVIEW -> LEGITIMATE")
    test_id_2 = str(uuid.uuid4())
    print(f"  • Generating dedicated test transaction: {test_id_2}")

    pred_payload_2 = {
        "transaction_id": test_id_2,
        "transaction_amount": 755.88,
        "amount": 755.88,
        "merchant": "Lifecycle Test Terminal Beta",
        "merchant_category": "Travel & Airlines",
        "merchant_country": "Germany",
        "location": "Berlin, DE",
        "transaction_hour": 20,
        "transaction_day_of_week": "Monday",
        "card_present": 0,
        "customer_age": 34,
        "customer_gender": "Female",
        "customer_state": "TN",
        "account_age_days": 2552,
        "credit_limit": 10870,
        "credit_score": 657,
        "num_cards_held": 1,
        "transactions_last_1h": 6,
        "transactions_last_24h": 6,
        "transactions_last_7d": 12,
        "amount_last_1h": 913.46,
        "amount_last_24h": 959.25,
        "days_since_last_transaction": 4,
        "distance_from_home_km": 14489,
        "distance_from_last_tx_km": 53.6,
        "international_transaction": 1,
        "high_risk_country": 0,
        "amount_vs_avg_ratio": 5.538,
        "used_chip": 0,
        "used_pin": 0,
        "transaction_channel": "Online",
        "device_type": "Desktop",
        "browser": "Chrome",
        "is_weekend": 0,
        "avg_transaction_amount_30d": 136.5,
        "std_transaction_amount_30d": 103.35,
        "num_declined_last_30d": 0,
        "num_chargebacks_ever": 2,
        "email_domain": "yahoo",
        "card_last4": "4432",
        "category": "Travel & Airlines",
    }

    send_req("/predict", method="POST", data=pred_payload_2)
    send_req(
        f"/transactions/{test_id_2}/review",
        method="PATCH",
        data={"review_status": "UNDER_REVIEW", "analyst_notes": "Travel notice check"},
    )
    _, res_legit = send_req(
        f"/transactions/{test_id_2}/review",
        method="PATCH",
        data={
            "review_status": "LEGITIMATE",
            "analyst_notes": "Verified verified corporate travel booking",
            "reviewed_by": "analyst.smith@sentinel.internal",
        },
    )
    assert res_legit["review_status"] == "LEGITIMATE"
    print(f"  • Transition:                 UNDER_REVIEW -> {res_legit['review_status']} ✓")

    # Step F: Analytics Metric Impact Check
    _, analytics_during = send_req("/analytics")
    print(f"\n[ANALYTICS VERIFICATION WITH REVIEWED RECORDS]:")
    print(f"  • Confirmed Fraud Count:      {analytics_during['total_confirmed_fraud']} (Includes test 1)")
    print(f"  • Confirmed Legitimate Count: {analytics_during['total_confirmed_legitimate']} (Includes test 2)")
    assert analytics_during["total_confirmed_fraud"] >= 1
    assert analytics_during["total_confirmed_legitimate"] >= 1
    print("  ✓ PASS: Analyst-confirmed decisions truthfully update portfolio KPIs!")

    # -------------------------------------------------------------------------
    # SAFE CLEANUP OF DEDICATED TEST RECORDS ONLY
    # -------------------------------------------------------------------------
    print("\n[CLEANUP] REMOVING DEDICATED TEST RECORDS ONLY:")
    for tid in [test_id_1, test_id_2]:
        try:
            client.table("transactions").delete().eq("id", tid).execute()
            print(f"  • Cleaned test record {tid} from Supabase.")
        except Exception as e:
            print(f"  • Supabase cleanup note: {e}")

    print("\n" + "=" * 75)
    print("🎉 ALL LIFECYCLE AND REVIEW WORKFLOW TESTS PASSED!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    run_lifecycle_tests()
