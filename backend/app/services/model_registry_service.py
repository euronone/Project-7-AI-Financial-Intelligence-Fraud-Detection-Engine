"""
Phase 3 — #15: Model Registry Service (F2.7 / F2.8)

Business logic layer:
  - List / get / register models
  - Promote (make active, retire previous)
  - Retire
  - Update metrics
  - Trigger retraining (F2.8) — runs training pipeline in-process
  - Run inference via ONNX pipeline (F2.9)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from app.ml.registry import MLModelRegistry, RegisteredModel, registry as _global_registry
from app.schemas.ml_models import (
    InferenceResponse,
    ModelType,
    RegisteredModelResponse,
    RetrainResponse,
)


def _to_response(m: RegisteredModel) -> RegisteredModelResponse:
    return RegisteredModelResponse(
        id=m.id,
        name=m.name,
        model_type=m.model_type,
        version=m.version,
        status=m.status,
        metrics=m.metrics,
        artifact_path=m.artifact_path,
        training_dataset_info=m.training_dataset_info,
        description=m.description,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class ModelRegistryService:
    def __init__(self, reg: Optional[MLModelRegistry] = None):
        self._reg = reg or _global_registry

    # ── F2.7: List / get ─────────────────────────────────────────────────

    def list_models(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[RegisteredModelResponse]:
        return [_to_response(m) for m in self._reg.list_models(model_type, status)]

    def get_model(self, model_id: str) -> Optional[RegisteredModelResponse]:
        m = self._reg.get_model(model_id)
        return _to_response(m) if m else None

    def get_metrics(self, model_id: str) -> Optional[Dict]:
        m = self._reg.get_model(model_id)
        return m.metrics if m else None

    # ── F2.7: Register ───────────────────────────────────────────────────

    def register_model(
        self,
        name: str,
        model_type: str,
        version: str,
        description: str = "",
        metrics: Optional[Dict] = None,
        artifact_path: str = "",
        training_dataset_info: Optional[Dict] = None,
    ) -> RegisteredModelResponse:
        model = RegisteredModel(
            id=str(uuid.uuid4()),
            name=name,
            model_type=model_type,
            version=version,
            status="validating",
            description=description,
            metrics=metrics or {},
            artifact_path=artifact_path,
            training_dataset_info=training_dataset_info or {},
        )
        self._reg.register(model)
        return _to_response(model)

    # ── F2.7: Promote / Retire ───────────────────────────────────────────

    def promote_model(self, model_id: str) -> Optional[RegisteredModelResponse]:
        m = self._reg.promote(model_id)
        return _to_response(m) if m else None

    def retire_model(self, model_id: str) -> Optional[RegisteredModelResponse]:
        m = self._reg.retire(model_id)
        return _to_response(m) if m else None

    def update_metrics(self, model_id: str, metrics: Dict) -> Optional[RegisteredModelResponse]:
        m = self._reg.update_metrics(model_id, metrics)
        return _to_response(m) if m else None

    # ── F2.8: Automated Retraining ───────────────────────────────────────

    def trigger_retraining(
        self,
        model_type: str,
        n_samples: int = 10_000,
        reason: str = "",
    ) -> RetrainResponse:
        """
        Run the appropriate training pipeline synchronously.
        In production this would dispatch a Celery task / Azure ML job.
        """
        job_id = str(uuid.uuid4())

        if model_type == "fraud_classifier":
            from app.ml.training.train_classifier import run_training
            metrics = run_training(output_dir="models/", n_samples=n_samples)
            model_name = "XGBoost Fraud Classifier (retrained)"
            version = metrics.get("version", "v_retrained")

        elif model_type == "anomaly_detector":
            from app.ml.training.train_anomaly_model import run_training
            n_anomaly = max(100, n_samples // 10)
            metrics = run_training(
                output_dir="models/",
                n_normal=n_samples - n_anomaly,
                n_anomaly=n_anomaly,
            )
            model_name = "Isolation Forest Anomaly Detector (retrained)"
            version = metrics.get("version", "v_retrained")

        else:
            return RetrainResponse(
                job_id=job_id,
                model_type=model_type,
                status="skipped",
                message=f"No training pipeline defined for model_type='{model_type}'",
                metrics={},
            )

        # Register the newly-trained model
        artifact_path = metrics.pop("artifact_path", "")
        new_model = RegisteredModel(
            name=model_name,
            model_type=model_type,
            version=version,
            status="validating",
            metrics=metrics,
            artifact_path=artifact_path,
            training_dataset_info={"n_samples": n_samples, "reason": reason},
        )
        self._reg.register(new_model)

        return RetrainResponse(
            job_id=job_id,
            model_type=model_type,
            status="completed",
            message=f"Model retrained and registered as '{new_model.id}' (status=validating). Promote when validated.",
            metrics=new_model.metrics,
        )

    # ── F2.9: Inference ──────────────────────────────────────────────────

    def run_inference(self, model_id: str, features: list) -> InferenceResponse:
        X = np.array(features, dtype=np.float32)
        result = self._reg.predict(model_id, X)
        return InferenceResponse(**result)
