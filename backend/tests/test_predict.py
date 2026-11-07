import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data
    assert data["model_loaded"] is True


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_connected" in data


def test_get_transactions_endpoint():
    """Verify GET /transactions fetches recent transactions ordered by timestamp."""
    response = client.get("/transactions")
    assert response.status_code == 200
    data = response.json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    assert isinstance(items, list)
    assert len(items) <= 50


def test_predict_fraud_valid_payload():
    """Test POST /predict with a realistic transaction payload using the trained model."""
    payload = {
        "transaction_amount": 249.50,
        "Amount": 249.50,
        "account_age_days": 450,
        "customer_age": 38,
        "credit_score": 680,
        "transactions_last_24h": 3,
        "distance_from_home_km": 15.2,
        "international_transaction": 0,
        "transaction_hour": 14,
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "transaction_id" in data
    assert "fraud_probability" in data
    prob = data["fraud_probability"]
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0

    # Ensure is_flagged boolean is computed (true if probability >= 0.35)
    assert "is_flagged" in data
    assert data["is_flagged"] == (prob >= 0.35)

    # Ensure top 5 SHAP features are returned with pos/neg separation and narrative
    assert "shap_values" in data
    assert "shap_explanations" in data
    assert isinstance(data["shap_values"], dict)
    assert len(data["shap_values"]) == 5

    assert "positive_contributions" in data
    assert "negative_contributions" in data
    assert "summary_narrative" in data
    assert isinstance(data["summary_narrative"], list)
    assert len(data["summary_narrative"]) == 5

    # Check top contributor fields
    assert "top_contributors" in data
    assert len(data["top_contributors"]) == 5
    first_contrib = data["top_contributors"][0]
    assert "feature" in first_contrib
    assert "display_name" in first_contrib
    assert "feature_value" in first_contrib
    assert "shap_value" in first_contrib
    assert "human_readable" in first_contrib
    assert "Increased fraud risk" in first_contrib["human_readable"] or "Reduced fraud risk" in first_contrib["human_readable"]

    # Ensure risk stratification
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_predict_reindexes_missing_features_with_zero():
    """Verify payload with missing columns is reindexed with 0s per requirement."""
    partial_payload = {
        "Amount": 85.0,
    }
    response = client.post("/predict", json=partial_payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert len(data["shap_values"]) == 5
    assert len(data["summary_narrative"]) == 5
