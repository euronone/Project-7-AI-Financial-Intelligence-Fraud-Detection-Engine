"""Anomaly detection via Isolation Forest + Autoencoder placeholder.

In production this would use trained sklearn/PyTorch models. The dev
implementation uses a z-score-based heuristic that highlights outliers.
"""

from typing import Any

import structlog

logger = structlog.get_logger()

ANOMALY_FEATURES = [
    "amount_zscore",
    "amount_to_avg_ratio",
    "txn_count_1h",
    "unique_countries",
    "unique_devices",
]

THRESHOLDS: dict[str, float] = {
    "amount_zscore": 2.5,
    "amount_to_avg_ratio": 5.0,
    "txn_count_1h": 8.0,
    "unique_countries": 4.0,
    "unique_devices": 4.0,
}


class AnomalyDetector:
    """Isolation Forest + Autoencoder anomaly detector (dev placeholder)."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("anomaly_detector_loaded", model_path=self.model_path or "builtin")

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        anomaly_signals = 0
        details: dict[str, float] = {}

        for feat in ANOMALY_FEATURES:
            val = abs(features.get(feat, 0.0))
            threshold = THRESHOLDS.get(feat, 3.0)
            if val > threshold:
                anomaly_signals += 1
            details[feat] = round(val, 4)

        score = min(anomaly_signals / len(ANOMALY_FEATURES), 1.0)

        return {
            "anomaly_score": round(score, 4),
            "is_anomaly": score >= 0.4,
            "anomaly_signals": anomaly_signals,
            "feature_deviations": details,
            "model_type": "anomaly_detector",
            "model_version": "dev-1.0",
        }
