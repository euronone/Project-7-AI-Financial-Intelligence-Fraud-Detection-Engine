"""Prediction explainability via feature contribution analysis.

Provides SHAP-style explanations for fraud predictions by identifying
the top contributing features and their impact direction.
"""

from typing import Any

FRAUD_FEATURE_DESCRIPTIONS: dict[str, str] = {
    "amount_zscore": "Transaction amount significantly deviates from history",
    "is_large_amount": "Large transaction amount (>$10,000)",
    "is_high_risk_country": "Transaction originates from high-risk country",
    "country_change": "Transaction from a new country not seen before",
    "is_new_device": "Transaction from an unrecognized device",
    "is_night": "Transaction outside normal business hours",
    "is_weekend": "Transaction on a weekend",
    "is_new_account": "Recently opened account (<30 days)",
    "amount_to_avg_ratio": "Amount much higher than average for this entity",
    "is_micro_amount": "Very small amount (potential card testing)",
    "recent_info_change": "Recent account information change",
    "device_seen_before": "Device previously used (reduces risk)",
    "is_round_amount": "Rounded transaction amount",
    "card_present": "Physical card was present",
    "unique_countries": "High number of unique countries",
    "unique_devices": "High number of unique devices",
    "txn_count_1h": "High transaction velocity in last hour",
}


def explain_prediction(
    features: dict[str, float],
    fraud_result: dict[str, Any],
    anomaly_result: dict[str, Any],
    behavioral_result: dict[str, Any],
) -> dict[str, Any]:
    """Generate a human-readable explanation of the prediction."""
    contributions = _compute_contributions(features)

    top_positive = sorted(
        [c for c in contributions if c["impact"] > 0],
        key=lambda x: abs(x["impact"]),
        reverse=True,
    )[:5]

    top_negative = sorted(
        [c for c in contributions if c["impact"] < 0],
        key=lambda x: abs(x["impact"]),
        reverse=True,
    )[:3]

    summary = _build_summary(
        fraud_result, anomaly_result, behavioral_result, top_positive
    )

    return {
        "summary": summary,
        "top_risk_factors": top_positive,
        "top_mitigating_factors": top_negative,
        "all_contributions": contributions,
    }


def _compute_contributions(features: dict[str, float]) -> list[dict[str, Any]]:
    from app.ml.fraud_classifier import FRAUD_SIGNAL_WEIGHTS

    contributions: list[dict[str, Any]] = []

    for feat, weight in FRAUD_SIGNAL_WEIGHTS.items():
        val = features.get(feat, 0.0)
        impact = val * weight
        if abs(impact) < 0.001:
            continue
        contributions.append({
            "feature": feat,
            "value": round(val, 4),
            "weight": weight,
            "impact": round(impact, 4),
            "direction": "increases_risk" if impact > 0 else "decreases_risk",
            "description": FRAUD_FEATURE_DESCRIPTIONS.get(feat, feat),
        })

    return contributions


def _build_summary(
    fraud: dict, anomaly: dict, behavioral: dict, top_factors: list[dict]
) -> str:
    prob = fraud.get("fraud_probability", 0)
    parts: list[str] = []

    if prob >= 0.8:
        parts.append("Very high fraud probability detected.")
    elif prob >= 0.5:
        parts.append("Elevated fraud probability detected.")
    elif prob >= 0.3:
        parts.append("Moderate fraud risk indicators present.")
    else:
        parts.append("Low fraud risk.")

    if anomaly.get("is_anomaly"):
        parts.append("Anomalous transaction pattern identified.")

    beh_score = behavioral.get("behavioral_score", 0)
    if beh_score > 0.5:
        parts.append("Significant deviation from entity's behavioral profile.")

    if top_factors:
        factor_names = [f["description"] for f in top_factors[:3]]
        parts.append("Key factors: " + "; ".join(factor_names) + ".")

    return " ".join(parts)
