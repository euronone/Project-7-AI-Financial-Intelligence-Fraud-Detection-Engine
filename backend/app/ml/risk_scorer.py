"""Risk score aggregator.

Combines fraud classifier, anomaly detector, behavioral profiler,
and network analyzer scores into a single weighted risk score.
"""

from typing import Any

import structlog

logger = structlog.get_logger()

DEFAULT_WEIGHTS = {
    "fraud_classifier": 0.35,
    "anomaly_detector": 0.25,
    "behavioral_profiler": 0.20,
    "network_analyzer": 0.10,
    "rules_engine": 0.10,
}

RISK_LEVELS = [
    (0.0, 0.2, "low"),
    (0.2, 0.4, "medium_low"),
    (0.4, 0.6, "medium"),
    (0.6, 0.8, "high"),
    (0.8, 1.01, "critical"),
]


def compute_risk_score(
    fraud_result: dict[str, Any],
    anomaly_result: dict[str, Any],
    behavioral_result: dict[str, Any],
    network_result: dict[str, Any],
    rules_hit_count: int = 0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute the aggregate risk score from all model outputs."""
    w = weights or DEFAULT_WEIGHTS

    component_scores = {
        "fraud_classifier": fraud_result.get("fraud_probability", 0.0),
        "anomaly_detector": anomaly_result.get("anomaly_score", 0.0),
        "behavioral_profiler": behavioral_result.get("behavioral_score", 0.0),
        "network_analyzer": network_result.get("network_score", 0.0),
        "rules_engine": min(rules_hit_count / 3.0, 1.0),
    }

    overall = sum(component_scores.get(k, 0) * w.get(k, 0) for k in w)
    overall = round(min(max(overall, 0.0), 1.0), 4)

    risk_level = _get_risk_level(overall)

    risk_factors = _build_risk_factors(
        fraud_result, anomaly_result, behavioral_result, network_result, rules_hit_count
    )

    return {
        "overall_score": overall,
        "risk_level": risk_level,
        "component_scores": {k: round(v, 4) for k, v in component_scores.items()},
        "risk_factors": risk_factors,
        "weights_used": w,
    }


def _get_risk_level(score: float) -> str:
    for low, high, level in RISK_LEVELS:
        if low <= score < high:
            return level
    return "critical"


def _build_risk_factors(
    fraud: dict, anomaly: dict, behavioral: dict, network: dict, rules_hits: int
) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []

    prob = fraud.get("fraud_probability", 0)
    if prob >= 0.5:
        factors.append({"factor": "High fraud probability", "score": prob, "source": "fraud_classifier"})

    if anomaly.get("is_anomaly"):
        factors.append({
            "factor": "Anomalous transaction pattern",
            "score": anomaly.get("anomaly_score", 0),
            "source": "anomaly_detector",
        })

    beh_score = behavioral.get("behavioral_score", 0)
    if beh_score > 0.5:
        devs = behavioral.get("deviations", {})
        factors.append({
            "factor": "Significant behavioral deviation",
            "score": beh_score,
            "source": "behavioral_profiler",
            "details": devs,
        })

    net_score = network.get("network_score", 0)
    if net_score > 0.3:
        factors.append({
            "factor": "Suspicious network activity",
            "score": net_score,
            "source": "network_analyzer",
        })

    if rules_hits > 0:
        factors.append({
            "factor": f"Matched {rules_hits} rule(s)",
            "score": min(rules_hits / 3.0, 1.0),
            "source": "rules_engine",
        })

    return factors
