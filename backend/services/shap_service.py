import logging
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np
import shap

logger = logging.getLogger("fraud_backend.shap_service")


def format_feature_name(feature: str) -> str:
    """Converts machine-learning feature column names to human-readable names."""
    if feature.startswith("merchant_category_"):
        return f"Merchant Category ({feature.replace('merchant_category_', '')})"
    if feature.startswith("merchant_country_"):
        return f"Merchant Country ({feature.replace('merchant_country_', '')})"
    if feature.startswith("transaction_channel_"):
        return f"Channel ({feature.replace('transaction_channel_', '')})"
    if feature.startswith("device_type_"):
        return f"Device Type ({feature.replace('device_type_', '')})"
    if feature.startswith("browser_"):
        return f"Browser ({feature.replace('browser_', '')})"
    if feature.startswith("email_domain_"):
        return f"Email Domain ({feature.replace('email_domain_', '')})"
    if feature.startswith("customer_state_"):
        return f"Customer State ({feature.replace('customer_state_', '')})"
    if feature.startswith("transaction_day_of_week_"):
        return f"Day of Week ({feature.replace('transaction_day_of_week_', '')})"

    name_map = {
        "transaction_amount": "Transaction Amount",
        "amount_vs_avg_ratio": "Spend vs. Historical Average Ratio",
        "distance_from_home_km": "Distance from Home (km)",
        "distance_from_last_tx_km": "Distance from Prior Transaction (km)",
        "transactions_last_1h": "Transaction Velocity (Past 1 Hour)",
        "transactions_last_24h": "Transaction Velocity (Past 24 Hours)",
        "transactions_last_7d": "Transaction Velocity (Past 7 Days)",
        "amount_last_1h": "Spend Cumulative (Past 1 Hour)",
        "amount_last_24h": "Spend Cumulative (Past 24 Hours)",
        "international_transaction": "International Cross-Border Payment",
        "high_risk_country": "High-Risk Merchant Jurisdiction",
        "num_declined_last_30d": "Declined Authorizations (Last 30 Days)",
        "num_chargebacks_ever": "Historical Chargeback Incidents",
        "card_present": "Card-Present POS Authorization",
        "used_chip": "EMV Cryptographic Chip Authentication",
        "used_pin": "PIN Verification Verified",
        "account_age_days": "Account Age / Tenure (Days)",
        "credit_score": "Cardholder Credit Score",
        "credit_limit": "Assigned Credit Limit",
        "days_since_last_transaction": "Inactivity Period Before Transaction (Days)",
        "transaction_hour": "Time of Day (Local Hour)",
        "customer_age": "Cardholder Age",
        "is_weekend": "Weekend Transaction Flag",
    }
    return name_map.get(feature, feature.replace("_", " ").title())


def generate_human_readable_explanation(
    feature: str,
    shap_val: float,
    raw_val: Any,
) -> str:
    """
    Generates plain-language, contextual fraud explanation for an individual feature attribution.
    Examples:
      - 'High transaction velocity (3 in 1 hour): Increased fraud risk.'
      - 'Familiar device fingerprint: Reduced fraud risk.'
    """
    is_risk_increasing = shap_val > 0
    risk_suffix = "Increased fraud risk." if is_risk_increasing else "Reduced fraud risk."

    try:
        val_float = float(raw_val) if raw_val is not None else 0.0
    except (ValueError, TypeError):
        val_float = 0.0

    # 1. Transaction Amount & Deviation
    if feature in ("transaction_amount", "amount", "Amount"):
        if is_risk_increasing:
            return f"Unusual transaction amount (${val_float:,.2f}): {risk_suffix}"
        return f"Transaction amount (${val_float:,.2f}) aligns with cardholder baseline: {risk_suffix}"

    if feature == "amount_vs_avg_ratio":
        if is_risk_increasing:
            return f"Transaction size is {val_float:.1f}x higher than 30-day average: {risk_suffix}"
        return f"Transaction size is normal relative to historical average: {risk_suffix}"

    # 2. Location & Geovelocity
    if feature == "distance_from_home_km":
        if is_risk_increasing:
            return f"Unusual transaction location ({val_float:,.0f} km from home): {risk_suffix}"
        return f"Transaction originating in familiar local perimeter: {risk_suffix}"

    if feature == "distance_from_last_tx_km":
        if is_risk_increasing:
            return f"Geographical velocity anomaly ({val_float:,.0f} km since last transaction): {risk_suffix}"
        return f"Geographic continuity with previous transaction location: {risk_suffix}"

    if feature == "high_risk_country":
        if is_risk_increasing and val_float >= 1:
            return f"Merchant terminal located in flagged high-risk jurisdiction: {risk_suffix}"
        return f"Merchant operating in standard-risk international jurisdiction: {risk_suffix}"

    if feature == "international_transaction":
        if is_risk_increasing and val_float >= 1:
            return f"Cross-border payment executed outside cardholder home nation: {risk_suffix}"
        return f"Domestic payment transaction in home country: {risk_suffix}"

    # 3. Transaction Velocity
    if feature in ("transactions_last_1h", "transactions_last_24h"):
        window = "past 1 hour" if "1h" in feature else "past 24 hours"
        if is_risk_increasing:
            return f"High transaction velocity ({int(val_float)} transactions in {window}): {risk_suffix}"
        return f"Normal transaction frequency in {window}: {risk_suffix}"

    if feature in ("amount_last_1h", "amount_last_24h"):
        window = "past 1 hour" if "1h" in feature else "past 24 hours"
        if is_risk_increasing:
            return f"Rapid cumulative spending (${val_float:,.2f} in {window}): {risk_suffix}"
        return f"Cumulative spend in {window} within safe spending thresholds: {risk_suffix}"

    # 4. Authentication & Security Signals
    if feature in ("card_present",):
        if is_risk_increasing and val_float == 0:
            return f"Card-not-present online transaction: {risk_suffix}"
        return f"Physical card present at merchant terminal: {risk_suffix}"

    if feature in ("used_chip", "used_pin"):
        if not is_risk_increasing and val_float == 1:
            return f"EMV cryptographic chip & PIN authentication verified: {risk_suffix}"
        return f"Non-chip authorization fallback detected: {risk_suffix}"

    # 5. Risk History & Chargebacks
    if feature == "num_declined_last_30d":
        if is_risk_increasing and val_float > 0:
            return f"Elevated authorization failure history ({int(val_float)} declined recently): {risk_suffix}"
        return f"Zero declined authorizations in recent history: {risk_suffix}"

    if feature == "num_chargebacks_ever":
        if is_risk_increasing and val_float > 0:
            return f"Historical chargeback record ({int(val_float)} disputes filed on account): {risk_suffix}"
        return f"Clean chargeback history on account: {risk_suffix}"

    # 6. Device, Browser & Channel
    if feature.startswith("device_type_") or feature.startswith("browser_"):
        device_name = feature.split("_", 1)[1]
        if is_risk_increasing:
            return f"Unfamiliar device / browser environment ({device_name}): {risk_suffix}"
        return f"Familiar device and environment ({device_name}): {risk_suffix}"

    if feature.startswith("merchant_category_"):
        cat_name = feature.replace("merchant_category_", "")
        if is_risk_increasing:
            return f"Elevated-risk merchant category ({cat_name}): {risk_suffix}"
        return f"Established merchant category ({cat_name}): {risk_suffix}"

    if feature == "account_age_days":
        if is_risk_increasing and val_float < 90:
            return f"New account tenure ({int(val_float)} days old): {risk_suffix}"
        return f"Mature account tenure ({int(val_float)} days old): {risk_suffix}"

    if feature == "credit_score":
        if is_risk_increasing and val_float < 600:
            return f"Below-average cardholder credit score ({int(val_float)}): {risk_suffix}"
        return f"Strong cardholder credit score ({int(val_float)}): {risk_suffix}"

    # Default fallback
    readable_name = format_feature_name(feature)
    if is_risk_increasing:
        return f"Unusual {readable_name} (value: {raw_val}): {risk_suffix}"
    return f"{readable_name} (value: {raw_val}) consistent with safe transactions: {risk_suffix}"


def compute_shap_explanations(
    explainer: shap.TreeExplainer,
    scaled_array: np.ndarray,
    model_columns: List[str],
    raw_payload: Dict[str, Any],
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Computes exact TreeSHAP feature attributions, validates output dimensions,
    extracts the top K features, separates positive (risk-increasing) and negative
    (risk-reducing) contributions, and generates human-readable narratives.
    """
    # 1. Compute raw SHAP values
    shap_raw = explainer.shap_values(scaled_array)

    # 2. Validate SHAP output dimensions and class selection
    if isinstance(shap_raw, list):
        # Multi-class output: class 1 is fraud
        vals = shap_raw[1] if len(shap_raw) > 1 else shap_raw[0]
        sv = np.array(vals[0]).flatten()
    elif hasattr(shap_raw, "ndim") and shap_raw.ndim == 3:
        # (samples, features, classes) -> positive class (index 1)
        sv = shap_raw[0, :, 1].flatten()
    elif hasattr(shap_raw, "ndim") and shap_raw.ndim == 2:
        # (samples, features)
        sv = shap_raw[0].flatten()
    else:
        sv = np.array(shap_raw).flatten()[:len(model_columns)]

    # 3. Extract Base Value (Expected Model Output)
    base_val = explainer.expected_value
    if isinstance(base_val, (list, np.ndarray)):
        expected_base = float(base_val[1] if len(base_val) > 1 else base_val[0])
    else:
        expected_base = float(base_val) if base_val is not None else 0.0

    # 4. Map feature attributions and look up actual raw values
    feature_attributions: List[Dict[str, Any]] = []
    positive_features: List[Dict[str, Any]] = []
    negative_features: List[Dict[str, Any]] = []

    for col, shap_v in zip(model_columns, sv):
        shap_float = float(round(float(shap_v), 4))
        if abs(shap_float) < 1e-6:
            continue

        # Look up raw value from payload (support direct name or one-hot categorical)
        raw_val = raw_payload.get(col)
        if raw_val is None:
            # Check for categorical prefix (e.g. merchant_category="Electronics")
            for prefix in ("merchant_category_", "merchant_country_", "device_type_", "browser_", "email_domain_", "transaction_channel_"):
                if col.startswith(prefix):
                    cat_field = prefix[:-1]
                    cat_val = col.replace(prefix, "")
                    if raw_payload.get(cat_field) == cat_val:
                        raw_val = cat_val
                    else:
                        raw_val = 0
                    break
        if raw_val is None:
            raw_val = 0

        human_text = generate_human_readable_explanation(col, shap_float, raw_val)
        impact_type = "INCREASED_RISK" if shap_float > 0 else "REDUCED_RISK"

        item = {
            "feature": col,
            "display_name": format_feature_name(col),
            "shap_value": shap_float,
            "feature_value": raw_val,
            "impact": impact_type,
            "human_readable": human_text,
        }

        feature_attributions.append(item)
        if shap_float > 0:
            positive_features.append(item)
        else:
            negative_features.append(item)

    # Sort by absolute impact
    feature_attributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    positive_features.sort(key=lambda x: x["shap_value"], reverse=True)
    negative_features.sort(key=lambda x: x["shap_value"])  # Most negative first

    # Top K most influential features
    top_features = feature_attributions[:top_k]

    # Compact dictionary for backward-compatibility with existing feeds
    top_shap_dict = {f["feature"]: f["shap_value"] for f in top_features}

    # Summary narrative lines (Human-readable explanations for top features)
    summary_narrative = [f["human_readable"] for f in top_features]

    return {
        "base_value": round(expected_base, 4),
        "top_features": top_features,
        "positive_contributions": positive_features[:top_k],
        "negative_contributions": negative_features[:top_k],
        "top_shap_dict": top_shap_dict,
        "summary_narrative": summary_narrative,
    }

