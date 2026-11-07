import math
from typing import Dict, List, Tuple
from backend.models.schemas import TransactionPayload, FeatureImpact
from backend.config import settings


# Domain-specific feature context descriptions for explainability
FEATURE_DESCRIPTIONS = {
    "V14": "Latent merchant-category anomaly vector",
    "V12": "Cardholder behavioral distance metric",
    "V10": "Historical spending pattern consistency",
    "V4": "Transaction frequency & velocity signature",
    "V11": "Location-velocity anomaly coefficient",
    "V17": "Cross-border & device identity divergence",
    "V7": "Terminal authorization pattern vector",
    "V3": "Historical chargeback correlation component",
    "Amount": "Monetary deviation from account baseline",
    "Time": "Circadian transaction rhythm divergence",
}


class FraudDetectionModelScaffold:
    """
    ML Integration Scaffold simulating an enterprise-grade XGBoost / LightGBM
    fraud classification model with TreeSHAP feature attributions.

    Empirically reflects the characteristics of PCA features derived from
    financial credit card fraud distributions (e.g., V14, V12, V10, V4, V11).
    """

    def __init__(self, threshold: float = 0.70):
        self.threshold = threshold
        # Base weights calibrated against standard Credit Card Fraud PCA importances
        self.weights = {
            "V14": -0.85,
            "V12": -0.65,
            "V10": -0.55,
            "V4": 0.60,
            "V11": 0.45,
            "V17": -0.40,
            "V7": -0.30,
            "V3": -0.25,
            "V16": -0.20,
            "V2": 0.15,
            "V8": 0.10,
        }
        self.base_intercept = -1.8  # Unbalanced class prior (fraud is rare)

    def predict(self, transaction: TransactionPayload) -> Tuple[float, str, bool, Dict[str, float], List[FeatureImpact]]:
        """
        Calculates:
        1. Fraud Probability Score (float between 0 and 1)
        2. Categorical Risk Level
        3. Binary flag (is_fraud)
        4. Mock dictionary of SHAP values for all features
        5. Ranked list of top impactful features
        """
        pca_dict = transaction.get_pca_dict()
        amount = transaction.Amount
        time_val = transaction.Time

        # 1. Compute linear logit response z
        z = self.base_intercept

        # Add contributions from weighted PCA features
        shap_raw: Dict[str, float] = {}
        for feat, weight in self.weights.items():
            val = pca_dict.get(feat, 0.0)
            contrib = weight * val
            z += contrib
            shap_raw[feat] = contrib

        # High amount non-linear contribution
        amount_contrib = 0.0
        if amount > 1000.0:
            amount_contrib = round(math.log10(amount) * 0.25, 4)
        elif amount > 300.0:
            amount_contrib = round(0.12, 4)
        else:
            amount_contrib = round(-0.08, 4)
        z += amount_contrib
        shap_raw["Amount"] = amount_contrib

        # Time of day contribution (simulated off-peak risk)
        time_contrib = round(math.sin(time_val / 3600.0) * 0.08, 4)
        z += time_contrib
        shap_raw["Time"] = time_contrib

        # Populate minor SHAP values for remaining PCA features (V1..V28)
        for i in range(1, 29):
            key = f"V{i}"
            if key not in shap_raw:
                val = pca_dict.get(key, 0.0)
                # Small residual impact
                minor_impact = round(val * 0.015, 4)
                shap_raw[key] = minor_impact
                z += minor_impact

        # 2. Sigmoid activation -> Probability strictly in [0.0, 1.0]
        # Clamping z between -15 and 15 to prevent numerical overflow
        clamped_z = max(min(z, 15.0), -15.0)
        probability = round(1.0 / (1.0 + math.exp(-clamped_z)), 4)

        # 3. Stratify Risk Level
        if probability >= 0.85:
            risk_level = "CRITICAL"
        elif probability >= 0.65:
            risk_level = "HIGH"
        elif probability >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_fraud = probability >= self.threshold

        # 4. Normalize & round SHAP dictionary
        shap_values: Dict[str, float] = {k: round(v, 4) for k, v in shap_raw.items()}

        # 5. Extract top contributors ranked by absolute impact
        sorted_feats = sorted(shap_values.items(), key=lambda item: abs(item[1]), reverse=True)
        top_contributors: List[FeatureImpact] = []
        for feat, val in sorted_feats[:6]:
            direction = "RISK_INCREASING" if val > 0 else "RISK_DECREASING"
            desc = FEATURE_DESCRIPTIONS.get(
                feat,
                f"Principal component {feat} contribution to overall fraud classification"
            )
            top_contributors.append(
                FeatureImpact(
                    feature=feat,
                    shap_value=val,
                    direction=direction,
                    description=desc
                )
            )

        return probability, risk_level, is_fraud, shap_values, top_contributors


# Global singleton instance
fraud_model = FraudDetectionModelScaffold(threshold=settings.FRAUD_THRESHOLD)

