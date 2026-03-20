"""Training orchestrator script.

Seeds dev-mode model entries in the database so the model registry
and risk scoring API have data to work with.

Usage: poetry run python scripts/train_models.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.config import get_settings
from app.db.session import async_session_factory
from app.models.ml_model import MLModel, ModelStatus, ModelType


SEED_MODELS = [
    {
        "name": "FraudClassifier-XGB",
        "model_type": ModelType.FRAUD_CLASSIFIER,
        "version": "1.0.0",
        "framework": "xgboost",
        "metrics": {
            "accuracy": 0.9642,
            "precision": 0.8710,
            "recall": 0.8125,
            "f1_score": 0.8407,
            "auc_roc": 0.9531,
            "total_samples": 50000,
            "fraud_rate": 0.048,
        },
        "artifact_path": "models/fraud_classifier_v1.0.0.onnx",
        "parameters": {"n_estimators": 500, "max_depth": 8, "learning_rate": 0.05},
        "status": ModelStatus.ACTIVE,
    },
    {
        "name": "AnomalyDetector-IF",
        "model_type": ModelType.ANOMALY_DETECTOR,
        "version": "1.0.0",
        "framework": "sklearn",
        "metrics": {
            "accuracy": 0.9380,
            "precision": 0.7920,
            "recall": 0.7640,
            "f1_score": 0.7778,
            "auc_roc": 0.9210,
            "total_samples": 50000,
        },
        "artifact_path": "models/anomaly_detector_v1.0.0.onnx",
        "parameters": {"n_estimators": 200, "contamination": 0.05},
        "status": ModelStatus.ACTIVE,
    },
    {
        "name": "RiskScorer-Ensemble",
        "model_type": ModelType.RISK_SCORER,
        "version": "1.0.0",
        "framework": "ensemble",
        "metrics": {
            "accuracy": 0.9510,
            "precision": 0.8450,
            "recall": 0.8290,
            "f1_score": 0.8369,
            "auc_roc": 0.9440,
            "total_samples": 50000,
        },
        "artifact_path": "models/risk_scorer_v1.0.0.pkl",
        "parameters": {
            "weights": {
                "fraud_classifier": 0.35,
                "anomaly_detector": 0.25,
                "behavioral_profiler": 0.20,
                "network_analyzer": 0.10,
                "rules_engine": 0.10,
            }
        },
        "status": ModelStatus.ACTIVE,
    },
    {
        "name": "BehavioralProfiler",
        "model_type": ModelType.BEHAVIORAL_PROFILER,
        "version": "1.0.0",
        "framework": "statistical",
        "metrics": {
            "accuracy": 0.9120,
            "precision": 0.7560,
            "recall": 0.7230,
            "f1_score": 0.7391,
            "auc_roc": 0.8920,
            "total_samples": 35000,
        },
        "artifact_path": "models/behavioral_profiler_v1.0.0.pkl",
        "parameters": {"profile_window_days": 90, "min_txn_count": 10},
        "status": ModelStatus.ACTIVE,
    },
]


async def seed_models() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(MLModel))
        existing = result.scalars().all()
        if existing:
            print(f"  {len(existing)} models already exist — skipping seed.")
            return

        from datetime import datetime, timezone

        for m in SEED_MODELS:
            model = MLModel(
                name=m["name"],
                model_type=m["model_type"],
                version=m["version"],
                status=m["status"],
                framework=m["framework"],
                metrics=m["metrics"],
                parameters=m.get("parameters"),
                artifact_path=m["artifact_path"],
                promoted_at=datetime.now(timezone.utc) if m["status"] == ModelStatus.ACTIVE else None,
            )
            session.add(model)
            print(f"  + {m['name']} v{m['version']} ({m['model_type'].value})")

        await session.commit()
        print(f"\n  Seeded {len(SEED_MODELS)} ML models.")


if __name__ == "__main__":
    asyncio.run(seed_models())
