"""
FRAUD SENTINEL — Standalone Inference Compatibility Verification Test (Task 9)
Tests loading model and preprocessing pipeline independently of training notebook.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd


def test_standalone_inference():
    print("=" * 70)
    print("RUNNING STANDALONE INFERENCE VERIFICATION (TASK 9)")
    print("=" * 70)

    # 1. Verify existence of all required production artifacts
    artifacts = [
        "final_model.joblib",
        "preprocessing_pipeline.joblib",
        "feature_schema.json",
        "model_metrics.json",
        "threshold_config.json",
        "model_metadata.json",
    ]
    for art in artifacts:
        p = Path("backend") / art
        assert p.is_file(), f"Missing required artifact: {p}"
        print(f"✓ Verified artifact: {art} ({p.stat().st_size:,} bytes)")

    # 2. Load model, pipeline, and threshold config
    model = joblib.load("backend/final_model.joblib")
    preprocessor = joblib.load("backend/preprocessing_pipeline.joblib")
    with open("backend/threshold_config.json") as f:
        threshold_config = json.load(f)
    with open("backend/feature_schema.json") as f:
        schema = json.load(f)

    decision_th = threshold_config["decision_thresholds"]["binary_decision_threshold"]

    # 3. Load dataset to extract real test samples
    df = pd.read_csv("backend/data.csv")
    drop_cols = [
        "transaction_id", "customer_id", "card_id", "merchant_id",
        "transaction_datetime", "fraud_type", "fraud_amount_lost", "is_fraud"
    ]
    features_df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Sample 1: Real Legitimate Transaction
    legit_idx = df[df["is_fraud"] == 0].index[0]
    legit_raw = features_df.iloc[legit_idx:legit_idx + 1].copy()
    legit_raw["browser"] = legit_raw["browser"].fillna("Unknown")

    legit_trans = preprocessor.transform(legit_raw)
    assert legit_trans.shape[1] == schema["total_features"], f"Feature dimension mismatch: {legit_trans.shape[1]} vs {schema['total_features']}"

    legit_prob = float(model.predict_proba(legit_trans)[0, 1])
    assert not np.isnan(legit_prob), "Legit probability is NaN"
    assert not np.isinf(legit_prob), "Legit probability is Infinite"
    assert 0.0 <= legit_prob <= 1.0, f"Probability out of bounds: {legit_prob}"

    # Sample 2: Real Fraudulent Transaction
    fraud_idx = df[df["is_fraud"] == 1].index[0]
    fraud_raw = features_df.iloc[fraud_idx:fraud_idx + 1].copy()
    fraud_raw["browser"] = fraud_raw["browser"].fillna("Unknown")

    fraud_trans = preprocessor.transform(fraud_raw)
    fraud_prob = float(model.predict_proba(fraud_trans)[0, 1])
    assert not np.isnan(fraud_prob), "Fraud probability is NaN"
    assert not np.isinf(fraud_prob), "Fraud probability is Infinite"
    assert 0.0 <= fraud_prob <= 1.0, f"Probability out of bounds: {fraud_prob}"

    # Sample 3: High-Risk International Fraud Sample
    high_risk_candidates = df[(df["is_fraud"] == 1) & (df["high_risk_country"] == 1)]
    if len(high_risk_candidates) > 0:
        hr_idx = high_risk_candidates.index[0]
        hr_raw = features_df.iloc[hr_idx:hr_idx + 1].copy()
        hr_raw["browser"] = hr_raw["browser"].fillna("Unknown")
        hr_trans = preprocessor.transform(hr_raw)
        hr_prob = float(model.predict_proba(hr_trans)[0, 1])
    else:
        hr_prob = fraud_prob

    print("\n--- INFERENCE RESULTS ---")
    print(f"Legitimate Sample (ID {df.iloc[legit_idx]['transaction_id']}):")
    print(f"  Amount: ${df.iloc[legit_idx]['transaction_amount']:.2f}")
    print(f"  Predicted Fraud Probability: {legit_prob:.4f} ({legit_prob*100:.2f}%)")
    print(f"  Decision (Threshold {decision_th}): {'FLAGGED' if legit_prob >= decision_th else 'CLEARED'}")
    print(f"  Risk Strata: {'LOW' if legit_prob < 0.25 else 'MEDIUM' if legit_prob < 0.60 else 'CRITICAL'}")

    print(f"\nFraudulent Sample (ID {df.iloc[fraud_idx]['transaction_id']}):")
    print(f"  Amount: ${df.iloc[fraud_idx]['transaction_amount']:.2f}")
    print(f"  Predicted Fraud Probability: {fraud_prob:.4f} ({fraud_prob*100:.2f}%)")
    print(f"  Decision (Threshold {decision_th}): {'FLAGGED' if fraud_prob >= decision_th else 'CLEARED'}")

    print(f"\nHigh-Risk International Fraud Sample:")
    print(f"  Predicted Fraud Probability: {hr_prob:.4f} ({hr_prob*100:.2f}%)")
    print(f"  Decision (Threshold {decision_th}): {'FLAGGED' if hr_prob >= decision_th else 'CLEARED'}")
    print(f"  Risk Strata: {'CRITICAL' if hr_prob >= 0.60 else 'HIGH' if hr_prob >= 0.40 else 'MEDIUM'}")

    print("\n" + "=" * 70)
    print("ALL STANDALONE INFERENCE CHECKS PASSED SUCCESSFULLY (0 ERRORS)")
    print("=" * 70)


if __name__ == "__main__":
    test_standalone_inference()

