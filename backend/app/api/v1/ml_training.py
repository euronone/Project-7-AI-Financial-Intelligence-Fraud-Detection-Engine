"""
ML Training API — Custom model building endpoints.

Routes (all under /api/v1/ml/training/):
  GET    /algorithms                  — list available algorithms + availability flags
  POST   /start                       — launch a new training job
  GET    /jobs                        — list all jobs for current tenant
  GET    /jobs/{job_id}               — poll a single job (progress + results)
  POST   /jobs/{job_id}/reoptimize    — re-run with an expanded data window
  POST   /jobs/{job_id}/promote       — promote completed job → active MLModel
  POST   /upload-pickle               — register an uploaded .pkl model file
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser, AdminUser
from app.services.ml_training_service import (
    ALGORITHM_CATALOGUE,
    MLTrainingService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml/training", tags=["ML Training"])

_MAX_PICKLE_MB = 200  # maximum upload size for pickle files


# ── Request / Response schemas ─────────────────────────────────────────────────


class StartTrainingRequest(BaseModel):
    algorithms: list[str] = Field(
        default=["xgboost", "isolation_forest"],
        description="List of algorithm IDs to include in this training run.",
        min_length=1,
    )
    data_window_days: int = Field(
        default=90,
        ge=0,
        le=3650,
        description="How many days of historical transactions to train on. 0 = all time.",
    )
    auto_optimize: bool = Field(
        default=True,
        description="Whether to run hyperparameter tuning after initial training.",
    )
    use_custom_columns: bool = Field(
        default=True,
        description="Apply enabled/disabled column flags from the Schema Mapping page.",
    )
    test_size: float = Field(
        default=0.20,
        ge=0.05,
        le=0.40,
        description="Fraction of data held out for evaluation (0.20 = 80/20 split, 0.10 = 90/10).",
    )


class ReoptimizeRequest(BaseModel):
    new_window_days: int = Field(
        ge=1,
        le=3650,
        description="New (wider) data window for the re-optimization run.",
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/algorithms")
async def get_algorithms(_: CurrentUser):
    """
    Return the full algorithm catalogue with availability flags.

    Each entry indicates:
      - id, name, description, library
      - available: whether the required package is installed
      - recommended: whether FinShield recommends this for most use-cases
      - tunable: whether auto-optimize will search hyperparameters for this algo
    """
    return {
        "clustering": ALGORITHM_CATALOGUE["clustering"],
        "supervised": ALGORITHM_CATALOGUE["supervised"],
        "total": (len(ALGORITHM_CATALOGUE["clustering"]) + len(ALGORITHM_CATALOGUE["supervised"])),
    }


@router.post("/start", status_code=202)
async def start_training(
    body: StartTrainingRequest,
    current_user: CurrentUser,
):
    """
    Launch a new ML training job for the current tenant.

    Returns immediately with 202 Accepted + job_id.
    Poll GET /jobs/{job_id} for progress.
    """
    # Validate algorithm IDs
    valid_ids = {a["id"] for group in ALGORITHM_CATALOGUE.values() for a in group}
    bad = [a for a in body.algorithms if a not in valid_ids]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown algorithm IDs: {bad}. Valid IDs: {sorted(valid_ids)}",
        )

    # Must have at least one algorithm that is available
    available_ids = {
        a["id"] for group in ALGORITHM_CATALOGUE.values() for a in group if a.get("available", True)
    }
    usable = [a for a in body.algorithms if a in available_ids]
    if not usable:
        raise HTTPException(
            status_code=422,
            detail=(
                "None of the selected algorithms are available in this environment. "
                "Install xgboost / lightgbm as needed, or choose scikit-learn algorithms."
            ),
        )

    try:
        job = await MLTrainingService.start_job(
            tenant_id=current_user.tenant_id,
            algorithms=usable,
            data_window_days=body.data_window_days,
            auto_optimize=body.auto_optimize,
            use_custom_columns=body.use_custom_columns,
            test_size=body.test_size,
        )
    except Exception as exc:
        logger.exception("Failed to start training job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "job_id": job.id,
        "status": job.status,
        "algorithms": usable,
        "data_window_days": body.data_window_days,
        "auto_optimize": body.auto_optimize,
        "message": "Training job queued. Poll /jobs/{job_id} for progress.",
    }


@router.get("/jobs")
async def list_jobs(current_user: CurrentUser):
    """List all training jobs for the current tenant (most recent first)."""
    jobs = await MLTrainingService.list_jobs(current_user.tenant_id)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, current_user: CurrentUser):
    """
    Poll a training job for live progress.

    While running, reads from the in-memory cache for low latency.
    Once completed/failed, reads from the database.

    Response includes:
      - status, progress_pct, current_stage
      - log_lines: [{ts, msg}]
      - metrics: {algo_id: {precision, recall, f1_score, auc_roc, ...}, ensemble: {...}}
      - best_algorithm
      - result_model_id (set after promote)
    """
    try:
        return await MLTrainingService.get_job_status(job_id, current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/reoptimize", status_code=202)
async def reoptimize_job(
    job_id: str,
    body: ReoptimizeRequest,
    current_user: CurrentUser,
):
    """
    Spawn a re-optimization child job using the same algorithm selection
    but a wider data window.

    The parent job must be in 'completed' or 'failed' status.
    Returns the new child job_id immediately (202 Accepted).
    """
    # Validate parent job belongs to this tenant
    try:
        parent_status = await MLTrainingService.get_job_status(job_id, current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if parent_status["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Parent job is still {parent_status['status']}. "
                "Wait for it to finish before re-optimizing."
            ),
        )

    try:
        new_job = await MLTrainingService.reoptimize_job(
            parent_job_id=job_id,
            tenant_id=current_user.tenant_id,
            new_window_days=body.new_window_days,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "job_id": new_job.id,
        "parent_job_id": job_id,
        "status": new_job.status,
        "new_window_days": body.new_window_days,
        "message": (
            f"Re-optimization job queued with {body.new_window_days}-day window. "
            "Poll /jobs/{job_id} for progress."
        ).replace("{job_id}", new_job.id),
    }


@router.post("/jobs/{job_id}/promote")
async def promote_job(
    job_id: str,
    current_user: AdminUser,
):
    """
    Promote a completed training job to the active MLModel for this tenant.

    Only admins can promote. The previous active model is retired.
    Returns the newly created MLModel record.
    """
    try:
        model = await MLTrainingService.promote_job(job_id, current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to promote job %s", job_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "model_id": model.id,
        "model_name": model.model_name,
        "version": model.version,
        "is_active": model.is_active,
        "precision": float(model.precision or 0),
        "recall": float(model.recall or 0),
        "f1_score": float(model.f1_score or 0),
        "auc_roc": float(model.auc_roc or 0),
        "training_samples": model.training_samples,
        "promoted_at": model.promoted_at.isoformat() if model.promoted_at else None,
        "message": f"Model '{model.model_name}' is now active for fraud scoring.",
    }


@router.post("/upload-pickle")
async def upload_pickle_model(
    current_user: AdminUser,
    file: UploadFile = File(
        ..., description="Pickle file (.pkl) containing sklearn-compatible model"
    ),
    model_name: str | None = Form(default=None, description="Optional display name for the model"),
):
    """
    Upload a custom pre-trained pickle model and register it as the active model.

    Accepted formats:
      • Raw sklearn / XGBoost model object
      • Dict with keys: {"model": <estimator>, "scaler": <StandardScaler>}
      • Dict with multiple models: {"xgboost": <model>, "random_forest": <model>, ...}

    The file is validated (must have a .predict() method), saved to disk,
    and registered as an active MLModel entry.
    Max upload size: 200 MB.
    """
    if not file.filename or not file.filename.endswith(".pkl"):
        raise HTTPException(
            status_code=422,
            detail="Only .pkl (pickle) files are accepted.",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > _MAX_PICKLE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {_MAX_PICKLE_MB} MB.",
        )

    effective_name = model_name or file.filename

    try:
        result = await MLTrainingService.register_uploaded_pickle(
            file_bytes=contents,
            filename=effective_name,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Pickle upload failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {**result, "file_size_mb": round(size_mb, 2)}
