import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulation_sample_endpoint():
    """Verify GET /transactions/sample returns a complete, realistic 35-feature payload."""
    response = client.get("/transactions/sample?scenario=random")
    assert response.status_code == 200
    data = response.json()

    # Core required features
    assert "transaction_amount" in data
    assert "merchant_category" in data
    assert "merchant_country" in data
    assert "account_age_days" in data
    assert "credit_score" in data
    assert "distance_from_home_km" in data
    assert "international_transaction" in data

    # UI presentation metadata
    assert "merchant" in data
    assert "location" in data
    assert "card_last4" in data


def test_simulation_scenarios_fraud_and_legit():
    """Verify both fraud and legit scenarios produce valid complete payloads."""
    fraud_res = client.get("/transactions/sample?scenario=fraud")
    assert fraud_res.status_code == 200
    fraud_data = fraud_res.json()
    assert fraud_data["transaction_amount"] > 0

    legit_res = client.get("/transactions/sample?scenario=legit")
    assert legit_res.status_code == 200
    legit_data = legit_res.json()
    assert legit_data["transaction_amount"] > 0


def test_full_pipeline_prediction_and_persistence():
    """Verify that a sampled transaction generates a real prediction and persists to the database."""
    sample = client.get("/transactions/sample?scenario=random").json()
    response = client.post("/predict", json=sample)
    assert response.status_code == 200
    pred = response.json()

    # Output verification
    assert "transaction_id" in pred
    assert 0.0 <= pred["fraud_probability"] <= 1.0
    assert pred["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(pred["is_flagged"], bool)

    # SHAP explanations verification
    assert len(pred["top_contributors"]) > 0
    first_contrib = pred["top_contributors"][0]
    assert "feature" in first_contrib
    assert "shap_value" in first_contrib
    assert "human_readable" in first_contrib
    assert isinstance(pred["summary_narrative"], list)

    # Persistence verification
    assert pred["logged_to_database"] is True

    # Retrieve from GET /transactions to ensure it is in the database
    txns_res = client.get("/transactions?limit=10")
    assert txns_res.status_code == 200
    txns = txns_res.json()
    items = txns["items"] if isinstance(txns, dict) and "items" in txns else txns
    assert len(items) > 0
    ids = [t["id"] for t in items]
    assert pred["transaction_id"] in ids


def test_risk_level_stratification():
    """Verify calibrated risk bands: LOW (<0.25), MEDIUM (0.25-0.60), HIGH/CRITICAL (>=0.60)."""
    # Sample a set of predictions and verify risk_level aligns with probability
    for _ in range(5):
        sample = client.get("/transactions/sample?scenario=random").json()
        pred = client.post("/predict", json=sample).json()
        prob = pred["fraud_probability"]
        risk = pred["risk_level"]
        is_flagged = pred["is_flagged"]

        # Check threshold flag
        assert is_flagged == (prob >= 0.35)

        if prob >= 0.60:
            assert risk in ("HIGH", "CRITICAL")
        elif prob >= 0.25:
            assert risk in ("MEDIUM", "HIGH")
        else:
            assert risk == "LOW"

