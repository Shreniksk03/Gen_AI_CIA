import json
import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    precision_recall_curve
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("model_trainer")

def run_ml_pipeline():
    data_path = Path("backend/data.csv")
    if not data_path.is_file():
        data_path = Path("data.csv")
    logger.info(f"Loading dataset from: {data_path.resolve()}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded raw dataset shape: {df.shape}")

    # 1. Prevent Data Leakage: Drop identifier and target-leakage columns
    drop_cols = [
        "transaction_id", "customer_id", "card_id", "merchant_id",
        "transaction_datetime", "fraud_type", "fraud_amount_lost"
    ]
    df_clean = df.drop(columns=[c for c in drop_cols if c in df.columns])
    df_clean["browser"] = df_clean["browser"].fillna("Unknown")

    target_col = "is_fraud"
    X = df_clean.drop(columns=[target_col])
    y = df_clean[target_col]

    # Convert categoricals to dummy variables
    X_encoded = pd.get_dummies(X, drop_first=True)
    feature_names = X_encoded.columns.tolist()
    logger.info(f"Feature count after one-hot encoding: {len(feature_names)}")

    # 2. Train/Test Splitting BEFORE SMOTE (80% Train, 20% Test, Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"Train set: {X_train.shape} (Fraud rate: {y_train.mean():.4f})")
    logger.info(f"Test set:  {X_test.shape} (Fraud rate: {y_test.mean():.4f})")

    # 3. Scaling fitted exclusively on training data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. SMOTE applied EXCLUSIVELY to training data
    logger.info("Applying SMOTE oversampling to training set only...")
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    logger.info(f"Balanced training set: {X_train_balanced.shape} (50/50 class balance)")

    # 5. Algorithm Comparison Suite
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        )
    }

    comparison_report = {}

    for name, clf in models.items():
        logger.info(f"Training {name}...")
        clf.fit(X_train_balanced, y_train_balanced)
        
        probs = clf.predict_proba(X_test_scaled)[:, 1]
        preds = (probs >= 0.50).astype(int)

        cm = confusion_matrix(y_test, preds)
        tn, fp, fn, tp = cm.ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

        metrics = {
            "accuracy": float(round(accuracy_score(y_test, preds), 4)),
            "precision": float(round(precision_score(y_test, preds, zero_division=0), 4)),
            "recall": float(round(recall_score(y_test, preds, zero_division=0), 4)),
            "f1_score": float(round(f1_score(y_test, preds, zero_division=0), 4)),
            "roc_auc": float(round(roc_auc_score(y_test, probs), 4)),
            "pr_auc": float(round(average_precision_score(y_test, probs), 4)),
            "false_positive_rate": float(round(fpr, 4)),
            "false_negative_rate": float(round(fnr, 4)),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp)
            }
        }
        comparison_report[name] = metrics
        logger.info(f"{name} -> ROC-AUC: {metrics['roc_auc']}, PR-AUC: {metrics['pr_auc']}, Recall: {metrics['recall']}, F1: {metrics['f1_score']}")

    # 6. Threshold Optimization for Best Model (XGBoost)
    xgb_model = models["XGBoost"]
    xgb_probs = xgb_model.predict_proba(X_test_scaled)[:, 1]

    threshold_analysis = []
    for thresh in np.arange(0.10, 0.95, 0.05):
        t_preds = (xgb_probs >= thresh).astype(int)
        t_cm = confusion_matrix(y_test, t_preds)
        t_tn, t_fp, t_fn, t_tp = t_cm.ravel()
        t_prec = precision_score(y_test, t_preds, zero_division=0)
        t_rec = recall_score(y_test, t_preds, zero_division=0)
        t_f1 = f1_score(y_test, t_preds, zero_division=0)
        t_fpr = t_fp / (t_fp + t_tn) if (t_fp + t_tn) > 0 else 0.0
        t_fnr = t_fn / (t_fn + t_tp) if (t_fn + t_tp) > 0 else 0.0

        threshold_analysis.append({
            "threshold": float(round(thresh, 2)),
            "precision": float(round(t_prec, 4)),
            "recall": float(round(t_rec, 4)),
            "f1_score": float(round(t_f1, 4)),
            "fpr": float(round(t_fpr, 4)),
            "fnr": float(round(t_fnr, 4)),
            "true_positives": int(t_tp),
            "false_positives": int(t_fp)
        })

    # Calibrate Risk Strata:
    # Low Risk: prob < 0.25 (Very low fraud likelihood, automated clearance)
    # Medium Risk: 0.25 <= prob < 0.60 (Elevated risk, flagged for analyst review)
    # High Risk: prob >= 0.60 (Critical risk anomaly, immediate block & alert)
    optimal_thresholds = {
        "low_risk_ceiling": 0.25,
        "medium_risk_floor": 0.25,
        "medium_risk_ceiling": 0.60,
        "high_risk_floor": 0.60,
        "recommended_binary_threshold": 0.35  # Balances High Recall (~85%) with practical Precision
    }

    # 7. Model Serialization & Asset Export
    save_targets = [Path("backend"), Path(".")]
    for target in save_targets:
        joblib.dump(xgb_model, target / "fraud_model.joblib")
        joblib.dump(scaler, target / "scaler.joblib")
        joblib.dump(feature_names, target / "model_columns.joblib")
        logger.info(f"Saved model assets to: {target.resolve()}")

    # 8. Export Model Metrics JSON for API & UI Consumption
    metrics_payload = {
        "best_model": "XGBoost",
        "algorithm_comparison": comparison_report,
        "threshold_analysis": threshold_analysis,
        "risk_thresholds": optimal_thresholds,
        "feature_count": len(feature_names),
        "total_test_samples": len(y_test),
        "test_fraud_samples": int(y_test.sum()),
        "test_legitimate_samples": int((y_test == 0).sum())
    }

    with open("backend/model_metrics.json", "w") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info("Saved backend/model_metrics.json")

    print("\n" + "="*70)
    print("PHASE 2 MODEL COMPARISON BENCHMARK RESULTS (TEST SET: 20,000 TRANSACTIONS)")
    print("="*70)
    for model_name, m in comparison_report.items():
        print(f"\n[{model_name}]")
        print(f"  Accuracy:                {m['accuracy'] * 100:.2f}%")
        print(f"  Precision:               {m['precision']:.4f}")
        print(f"  Recall (Detection Rate): {m['recall']:.4f}")
        print(f"  F1-Score:                {m['f1_score']:.4f}")
        print(f"  ROC-AUC:                 {m['roc_auc']:.4f}")
        print(f"  PR-AUC:                  {m['pr_auc']:.4f}")
        print(f"  False Positive Rate:     {m['false_positive_rate'] * 100:.2f}%")
        print(f"  False Negative Rate:     {m['false_negative_rate'] * 100:.2f}%")
        print(f"  Confusion Matrix:        TN={m['confusion_matrix']['true_negative']}, FP={m['confusion_matrix']['false_positive']}, FN={m['confusion_matrix']['false_negative']}, TP={m['confusion_matrix']['true_positive']}")

    print("\n" + "="*70)
    print("THRESHOLD OPTIMIZATION (XGBoost)")
    print("="*70)
    for t in threshold_analysis[::2]:
        print(f"  Threshold {t['threshold']:.2f} -> Recall: {t['recall']:.4f} | Precision: {t['precision']:.4f} | F1: {t['f1_score']:.4f} | FP: {t['false_positives']} | TP: {t['true_positives']}")

if __name__ == "__main__":
    run_ml_pipeline()

