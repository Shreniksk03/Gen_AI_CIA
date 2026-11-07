import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.db_service import calculate_analytics

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_transactions():
    """Seed test transactions into database for robust test coverage."""
    for scenario in ["fraud", "legit", "fraud", "legit", "legit"]:
        sample = client.get(f"/transactions/sample?scenario={scenario}").json()
        client.post("/predict", json=sample)


def test_transaction_pagination():
    """Verify pagination returns limit, page, pages, total, and items slice."""
    res = client.get("/transactions?page=1&limit=3")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert len(data["items"]) <= 3
    assert data["page"] == 1
    assert data["limit"] == 3
    assert data["total"] >= 5


def test_transaction_filters():
    """Verify filtering by risk_level, is_flagged, and search."""
    # Filter by is_flagged=true
    flagged_res = client.get("/transactions?is_flagged=true&limit=10")
    assert flagged_res.status_code == 200
    flagged_data = flagged_res.json()
    for item in flagged_data["items"]:
        assert item["is_flagged"] is True

    # Filter by risk_level
    risk_res = client.get("/transactions?risk_level=CRITICAL&limit=10")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    for item in risk_data["items"]:
        assert item["risk_level"] == "CRITICAL"


def test_transaction_search():
    """Verify search filter by merchant or ID substring."""
    all_res = client.get("/transactions?limit=1").json()
    if all_res["items"]:
        target_merchant = all_res["items"][0]["merchant"]
        query_word = target_merchant.split()[0]
        search_res = client.get(f"/transactions?search={query_word}")
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert len(search_data["items"]) >= 1


def test_transaction_detail_retrieval():
    """Verify GET /transactions/{id} retrieves complete record with SHAP explanation."""
    txns = client.get("/transactions?limit=1").json()["items"]
    assert len(txns) > 0
    target_id = txns[0]["id"]

    detail_res = client.get(f"/transactions/{target_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["id"] == target_id
    assert "fraud_probability" in detail
    assert "risk_level" in detail
    assert "review_status" in detail
    assert "shap_explanations" in detail
    assert "model_version" in detail


def test_missing_transaction_404():
    """Verify non-existent transaction ID returns 404 with structured error."""
    res = client.get("/transactions/non-existent-uuid-99999")
    assert res.status_code == 404
    err_body = res.json()
    assert "error" in err_body
    assert err_body["error"]["code"] == 404


def test_analytics_aggregation():
    """Verify GET /analytics computes totals, confirmed fraud, and time-series points."""
    res = client.get("/analytics?time_range=7d")
    assert res.status_code == 200
    analytics = res.json()

    assert "total_transactions" in analytics
    assert "total_flagged_transactions" in analytics
    assert "total_confirmed_fraud" in analytics
    assert "total_legitimate" in analytics
    assert "transactions_awaiting_review" in analytics
    assert "risk_distribution" in analytics
    assert "volume_over_time" in analytics
    assert "fraud_volume_over_time" in analytics

    assert analytics["total_transactions"] >= 5
    assert isinstance(analytics["risk_distribution"]["LOW"], int)
    assert isinstance(analytics["risk_distribution"]["CRITICAL"], int)


def test_analytics_empty_window():
    """Verify analytics handles time ranges with no records gracefully (zero-safe)."""
    # Test 24h vs 90d
    res = client.get("/analytics?time_range=24h")
    assert res.status_code == 200
    data = res.json()
    assert data["total_transactions"] >= 0
    assert isinstance(data["fraud_detection_rate"], float)


def test_analyst_review_status_update():
    """Verify PATCH /transactions/{id}/review updates status and audit history."""
    txns = client.get("/transactions?limit=1").json()["items"]
    assert len(txns) > 0
    tx_id = txns[0]["id"]

    update_payload = {
        "review_status": "UNDER_REVIEW",
        "analyst_notes": "Suspicious international transaction under inspection.",
        "reviewed_by": "lead.investigator@sentinel.ai",
    }

    patch_res = client.patch(f"/transactions/{tx_id}/review", json=update_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()

    assert updated["review_status"] == "UNDER_REVIEW"
    assert updated["analyst_notes"] == "Suspicious international transaction under inspection."
    assert updated["reviewed_by"] == "lead.investigator@sentinel.ai"
    assert updated["reviewed_at"] is not None

    # Verify review audit history is appended
    assert len(updated["review_history"]) >= 1
    assert updated["review_history"][0]["new_status"] == "UNDER_REVIEW"

    # Subsequent update to CONFIRMED_FRAUD
    second_update = {
        "review_status": "CONFIRMED_FRAUD",
        "analyst_notes": "Cardholder confirmed unauthorized remote payment.",
        "reviewed_by": "lead.investigator@sentinel.ai",
    }
    patch_res_2 = client.patch(f"/transactions/{tx_id}/review", json=second_update)
    assert patch_res_2.status_code == 200
    assert patch_res_2.json()["review_status"] == "CONFIRMED_FRAUD"


def test_invalid_review_status():
    """Verify invalid review status is rejected with 422 or 400."""
    txns = client.get("/transactions?limit=1").json()["items"]
    tx_id = txns[0]["id"]

    res = client.patch(f"/transactions/{tx_id}/review", json={"review_status": "INVALID_STATE"})
    assert res.status_code in (400, 422)


def test_model_metrics_endpoint():
    """Verify GET /model/metrics returns verified benchmarks and holdout test metrics."""
    res = client.get("/model/metrics")
    assert res.status_code == 200
    metrics = res.json()

    assert "best_model" in metrics
    assert "algorithm_comparison" in metrics
    assert "XGBoost" in metrics["algorithm_comparison"]

    xgb = metrics["algorithm_comparison"]["XGBoost"]
    assert "accuracy" in xgb
    assert "precision" in xgb
    assert "recall" in xgb
    assert "f1_score" in xgb
    assert "roc_auc" in xgb
    assert "pr_auc" in xgb
    assert "confusion_matrix" in xgb
    assert xgb["confusion_matrix"]["true_positive"] > 0


def test_model_info_endpoint():
    """Verify GET /model/info returns architecture, threshold, and risk band configuration."""
    res = client.get("/model/info")
    assert res.status_code == 200
    info = res.json()

    assert info["model_name"] == "XGBoost Financial Fraud Classifier"
    assert info["version"] == "2.1.0-production"
    assert info["selected_threshold"] == 0.35
    assert info["number_of_features"] == 35
    assert info["number_of_encoded_features"] == 131
    assert "risk_band_configuration" in info
    assert "LOW" in info["risk_band_configuration"]

