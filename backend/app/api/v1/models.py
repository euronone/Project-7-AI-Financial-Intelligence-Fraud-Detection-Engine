"""
Phase 3 — #15: ML Model Registry API Router (F2.7 / F2.8 / F2.9)

Endpoints:
  GET    /models                     List all registered models
  GET    /models/{id}                Get model details
  GET    /models/{id}/metrics        Get model metrics
  POST   /models/register            Register a new model
  POST   /models/{id}/promote        Promote model to active (F2.7)
  POST   /models/{id}/retire         Retire model (F2.7)
  PATCH  /models/{id}/metrics        Update model metrics
  POST   /models/retrain             Trigger retraining (F2.8)
  POST   /models/{id}/infer          Run inference (F2.9)
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.ml_models import (
    InferenceRequest,
    InferenceResponse,
    RegisteredModelResponse,
    RegisterModelRequest,
    RetrainRequest,
    RetrainResponse,
    UpdateMetricsRequest,
)
from app.services.model_registry_service import ModelRegistryService

router = APIRouter(prefix="/models", tags=["ML Model Registry"])

_svc = ModelRegistryService()


# ── GET /models ───────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[RegisteredModelResponse],
    summary="List all registered models (F2.7)",
)
def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> List[RegisteredModelResponse]:
    return _svc.list_models(model_type=model_type, status=status)


# ── GET /models/{id} ─────────────────────────────────────────────────────────

@router.get(
    "/{model_id}",
    response_model=RegisteredModelResponse,
    summary="Get model details (F2.7)",
)
def get_model(model_id: str) -> RegisteredModelResponse:
    m = _svc.get_model(model_id)
    if m is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return m


# ── GET /models/{id}/metrics ─────────────────────────────────────────────────

@router.get(
    "/{model_id}/metrics",
    summary="Get model performance metrics (F2.7)",
)
def get_metrics(model_id: str):
    metrics = _svc.get_metrics(model_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return {"model_id": model_id, "metrics": metrics}


# ── POST /models/register ─────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisteredModelResponse,
    status_code=201,
    summary="Register a new model (F2.7)",
)
def register_model(body: RegisterModelRequest) -> RegisteredModelResponse:
    return _svc.register_model(
        name=body.name,
        model_type=body.model_type,
        version=body.version,
        description=body.description,
        metrics=body.metrics,
        artifact_path=body.artifact_path,
        training_dataset_info=body.training_dataset_info,
    )


# ── POST /models/{id}/promote ────────────────────────────────────────────────

@router.post(
    "/{model_id}/promote",
    response_model=RegisteredModelResponse,
    summary="Promote model to active (F2.7)",
)
def promote_model(model_id: str) -> RegisteredModelResponse:
    m = _svc.promote_model(model_id)
    if m is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return m


# ── POST /models/{id}/retire ─────────────────────────────────────────────────

@router.post(
    "/{model_id}/retire",
    response_model=RegisteredModelResponse,
    summary="Retire a model (F2.7)",
)
def retire_model(model_id: str) -> RegisteredModelResponse:
    m = _svc.retire_model(model_id)
    if m is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return m


# ── PATCH /models/{id}/metrics ───────────────────────────────────────────────

@router.patch(
    "/{model_id}/metrics",
    response_model=RegisteredModelResponse,
    summary="Update model metrics (F2.7)",
)
def update_metrics(model_id: str, body: UpdateMetricsRequest) -> RegisteredModelResponse:
    m = _svc.update_metrics(model_id, body.metrics)
    if m is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return m


# ── POST /models/retrain ─────────────────────────────────────────────────────

@router.post(
    "/retrain",
    response_model=RetrainResponse,
    summary="Trigger model retraining (F2.8)",
)
def retrain_model(body: RetrainRequest) -> RetrainResponse:
    return _svc.trigger_retraining(
        model_type=body.model_type,
        n_samples=body.n_samples,
        reason=body.reason,
    )


# ── POST /models/{id}/infer ──────────────────────────────────────────────────

@router.post(
    "/{model_id}/infer",
    response_model=InferenceResponse,
    summary="Run model inference via ONNX pipeline (F2.9)",
)
def run_inference(model_id: str, body: InferenceRequest) -> InferenceResponse:
    try:
        return _svc.run_inference(model_id, body.features)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
