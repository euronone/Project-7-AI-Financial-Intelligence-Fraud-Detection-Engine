"""ML pipeline orchestrator.

Coordinates the full scoring pipeline:
  Transaction → Features → [Fraud Classifier, Anomaly Detector, Behavioral Profiler,
                             Network Analyzer, Rules Engine] → Risk Score → Explanation
"""

from typing import Any

import structlog

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.behavioral_profiler import BehavioralProfiler
from app.ml.explainability import explain_prediction
from app.ml.feature_engineering import extract_features
from app.ml.fraud_classifier import FraudClassifier
from app.ml.network_analyzer import NetworkAnalyzer
from app.ml.risk_scorer import compute_risk_score

logger = structlog.get_logger()

_fraud_classifier = FraudClassifier()
_anomaly_detector = AnomalyDetector()
_behavioral_profiler = BehavioralProfiler()
_network_analyzer = NetworkAnalyzer()


def load_models() -> None:
    """Pre-load all models (called at startup)."""
    _fraud_classifier.load()
    _anomaly_detector.load()
    _behavioral_profiler.load()
    _network_analyzer.load()
    logger.info("ml_pipeline_models_loaded")


def run_pipeline(
    transaction: dict,
    *,
    entity_history: list[dict] | None = None,
    network_transactions: list[dict] | None = None,
    rules_hit_count: int = 0,
) -> dict[str, Any]:
    """Run the full ML pipeline on a single transaction.

    Returns a dict with overall_score, risk_level, component scores,
    risk factors, and SHAP-style explanation.
    """
    features = extract_features(transaction, history=entity_history)

    fraud_result = _fraud_classifier.predict(features)
    anomaly_result = _anomaly_detector.predict(features)

    profile = _behavioral_profiler.build_profile(entity_history or [])
    behavioral_result = _behavioral_profiler.score_deviation(features, profile)

    entity_id = str(transaction.get("source_entity_id", ""))
    network_result = _network_analyzer.analyze(entity_id, network_transactions or [])

    risk = compute_risk_score(
        fraud_result,
        anomaly_result,
        behavioral_result,
        network_result,
        rules_hit_count=rules_hit_count,
    )

    explanation = explain_prediction(features, fraud_result, anomaly_result, behavioral_result)

    return {
        "overall_score": risk["overall_score"],
        "risk_level": risk["risk_level"],
        "component_scores": risk["component_scores"],
        "risk_factors": risk["risk_factors"],
        "fraud_result": fraud_result,
        "anomaly_result": anomaly_result,
        "behavioral_result": behavioral_result,
        "network_result": network_result,
        "explanation": explanation,
        "feature_count": len(features),
    }
