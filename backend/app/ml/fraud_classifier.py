"""Fraud classifier using XGBoost + shallow NN ensemble.

In production this loads ONNX models. For development, a lightweight
statistical model is used as a drop-in placeholder that produces realistic
scores from the extracted feature vector.
"""

import math
from typing import Any

import structlog

logger = structlog.get_logger()

FRAUD_SIGNAL_WEIGHTS: dict[str, float] = {
    "amount_zscore": 0.15,
    "is_large_amount": 0.10,
    "is_high_risk_country": 0.15,
    "country_change": 0.10,
    "is_new_device": 0.08,
    "is_night": 0.06,
    "is_weekend": 0.04,
    "is_new_account": 0.08,
    "amount_to_avg_ratio": 0.08,
    "is_micro_amount": 0.06,
    "recent_info_change": 0.05,
    "device_seen_before": -0.05,
}


class FraudClassifier:
    """Ensemble fraud classifier (XGBoost + NN placeholder)."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("fraud_classifier_loaded", model_path=self.model_path or "builtin")

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Return fraud probability and label."""
        raw = sum(
            features.get(feat, 0.0) * weight
            for feat, weight in FRAUD_SIGNAL_WEIGHTS.items()
        )
        prob = _sigmoid(raw * 4)

        return {
            "fraud_probability": round(prob, 4),
            "fraud_label": "fraud" if prob >= 0.5 else "legitimate",
            "model_type": "fraud_classifier",
            "model_version": "dev-1.0",
        }


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(x, 20), -20)))
