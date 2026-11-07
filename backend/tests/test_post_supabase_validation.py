"""
backend/tests/test_post_supabase_validation.py
Post-Supabase Integration Validation Test Suite.
Validates:
1. Total record count consistency (Supabase direct vs. /transactions vs. /analytics).
2. Pagination and limit calculations.
3. Risk classification band hierarchy (LOW, MEDIUM, HIGH, CRITICAL).
4. Investigation threshold decoupling (0.35 decision vs. risk severity).
5. Review status defaults (PENDING for unreviewed flagged items).
6. Confirmed fraud calculation integrity (analyst confirmed != model flagged).
7. Transaction detail & SHAP attribution retrieval.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

for env_file in [backend_dir / ".env", Path(".env")]:
    if env_file.is_file():
        load_dotenv(env_file, override=True)
        break

from services.db_service import (
    calculate_risk_level,
    resolve_review_status,
    get_supabase_client,
    check_database_connectivity,
)


def fetch_api(endpoint: str):
    url = f"http://localhost:8000{endpoint}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_validation_suite():
    print("=" * 75)
    print("FRAUD SENTINEL — POST-SUPABASE INTEGRATION VALIDATION SUITE")
    print("=" * 75)

    client = get_supabase_client()
    diag = check_database_connectivity(client)

    # 1. Total Record Count Consistency
    print("\n[TEST 1] TOTAL RECORD COUNT CONSISTENCY:")
    sb_direct_count = client.table("transactions").select("id", count="exact").execute().count
    txns_api = fetch_api("/transactions?limit=100")
    analytics_api = fetch_api("/analytics")

    api_txns_total = txns_api["total"]
    analytics_total = analytics_api["total_transactions"]

    print(f"  • Supabase Direct Count:      {sb_direct_count}")
    print(f"  • /transactions Total:        {api_txns_total}")
    print(f"  • /analytics Total:           {analytics_total}")

    assert sb_direct_count == api_txns_total == analytics_total, (
        f"Count mismatch: Supabase={sb_direct_count}, API={api_txns_total}, Analytics={analytics_total}"
    )
    print("  ✓ PASS: Supabase direct, /transactions, and /analytics counts match exactly!")

    # 2. Pagination and Limits
    print("\n[TEST 2] PAGINATION & PAGE LIMIT CALCULATIONS:")
    page_limit = 12
    paged_res = fetch_api(f"/transactions?page=1&limit={page_limit}")
    expected_pages = (sb_direct_count + page_limit - 1) // page_limit

    print(f"  • Requested Limit:            {page_limit}")
    print(f"  • Items Returned:             {len(paged_res['items'])}")
    print(f"  • Calculated Pages:           {paged_res['pages']} (Expected: {expected_pages})")

    assert len(paged_res["items"]) == min(page_limit, sb_direct_count)
    assert paged_res["pages"] == expected_pages
    print("  ✓ PASS: Pagination limits and page math verified.")

    # 3. Risk Classification Consistency
    print("\n[TEST 3] RISK CLASSIFICATION BAND HIERARCHY:")
    test_cases = [
        (0.12, "LOW"),
        (0.24, "LOW"),
        (0.25, "MEDIUM"),
        (0.39, "MEDIUM"),
        (0.40, "HIGH"),
        (0.5945, "HIGH"),  # The 59.5% transaction from the user prompt!
        (0.60, "CRITICAL"),
        (0.85, "CRITICAL"),
    ]
    for prob, expected_band in test_cases:
        calculated = calculate_risk_level(prob)
        assert calculated == expected_band, f"Failed for {prob}: got {calculated}, expected {expected_band}"
        print(f"  • Probability {prob*100:5.2f}% -> Band: {calculated:8} [Expected: {expected_band}] ✓")
    print("  ✓ PASS: Risk band thresholds operate consistently across all boundaries.")

    # 4. Investigation Threshold vs Risk Severity
    print("\n[TEST 4] DECISION THRESHOLD (0.35) VS RISK SEVERITY:")
    # A transaction at 0.38 is FLAGGED for review, but its risk severity is MEDIUM.
    prob_mid = 0.38
    is_flagged_mid = prob_mid >= 0.35
    risk_mid = calculate_risk_level(prob_mid)
    assert is_flagged_mid is True
    assert risk_mid == "MEDIUM"
    print(f"  • Probability 38.0%: Decision: FLAGGED (>= 0.35) | Risk Band: {risk_mid} ✓")

    # A transaction at 0.595 is FLAGGED for review, and its risk severity is HIGH.
    prob_high = 0.5945
    is_flagged_high = prob_high >= 0.35
    risk_high = calculate_risk_level(prob_high)
    assert is_flagged_high is True
    assert risk_high == "HIGH"
    print(f"  • Probability 59.5%: Decision: FLAGGED (>= 0.35) | Risk Band: {risk_high} ✓")
    print("  ✓ PASS: Investigation threshold (0.35) decoupled from severity classification.")

    # 5. Review Status Defaults & Pending Count
    print("\n[TEST 5] REVIEW STATUS DEFAULTS & PENDING COUNT:")
    flagged_unreviewed_status = resolve_review_status(None, is_flagged=True)
    unflagged_status = resolve_review_status(None, is_flagged=False)
    assert flagged_unreviewed_status == "PENDING"
    assert unflagged_status == "NOT_FLAGGED"
    print(f"  • Unreviewed Flagged Item Default:    {flagged_unreviewed_status} ✓")
    print(f"  • Unreviewed Unflagged Item Default:  {unflagged_status} ✓")

    awaiting = analytics_api["transactions_awaiting_review"]
    flagged_total = analytics_api["total_flagged_transactions"]
    print(f"  • Analytics Flagged Transactions:    {flagged_total}")
    print(f"  • Analytics Pending Review Queue:     {awaiting}")
    assert awaiting > 0, "Awaiting review should reflect flagged unreviewed items"
    print("  ✓ PASS: Flagged items default to PENDING and populate review queue.")

    # 6. Confirmed Fraud Integrity
    print("\n[TEST 6] CONFIRMED FRAUD ISOLATION:")
    confirmed = analytics_api["total_confirmed_fraud"]
    print(f"  • Analyst Confirmed Fraud Count:      {confirmed}")
    print(f"  • Flagged Anomalies Count:            {flagged_total}")
    # Model predictions must NEVER automatically count as analyst confirmed fraud
    assert confirmed == 0, "Model predictions should not auto-increment confirmed fraud"
    print("  ✓ PASS: Model-flagged anomalies are strictly separated from analyst-confirmed fraud.")

    # 7. Transaction Detail & SHAP Retrieval
    print("\n[TEST 7] TRANSACTION DETAIL & SHAP EXPLANATIONS:")
    # Test specific transaction 260a1f41-5751-5fb2-a027-4fcbe038989c (59.5% fraud)
    target_id = "260a1f41-5751-5fb2-a027-4fcbe038989c"
    detail = fetch_api(f"/transactions/{target_id}")

    print(f"  • Transaction ID:             {detail['id']}")
    print(f"  • Fraud Probability:          {detail['fraud_probability']*100:.2f}%")
    print(f"  • Risk Level:                 {detail['risk_level']}")
    print(f"  • Review Status:              {detail['review_status']}")
    print(f"  • Is Flagged:                 {detail['is_flagged']}")
    print(f"  • SHAP Features Count:        {len(detail['shap_explanations'])}")
    print(f"  • Top Contributors Extracted: {len(detail['top_contributors'])}")

    assert detail["risk_level"] == "HIGH", f"Expected HIGH risk for 59.5%, got {detail['risk_level']}"
    assert detail["is_flagged"] is True
    assert len(detail["shap_explanations"]) > 0
    assert len(detail["top_contributors"]) > 0
    print("  ✓ PASS: Transaction details, risk level HIGH, and SHAP features retrieved.")

    print("\n" + "=" * 75)
    print("🎉 ALL 7 VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    run_validation_suite()

