"""Service layer for ML model registry operations."""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml import model_registry
from app.models.ml_model import MLModel
from app.schemas.ml_model import MLModelListResponse, MLModelResponse, ModelCompareResponse

logger = structlog.get_logger()


async def list_models(
    db: AsyncSession,
    *,
    model_type: str | None = None,
    status: str | None = None,
) -> MLModelListResponse:
    models = await model_registry.list_models(db, model_type=model_type, status=status)
    return MLModelListResponse(
        total=len(models),
        items=[MLModelResponse.model_validate(m) for m in models],
    )


async def get_model(db: AsyncSession, model_id: uuid.UUID) -> MLModelResponse:
    model = await model_registry.get_model(db, model_id)
    return MLModelResponse.model_validate(model)


async def promote_model(db: AsyncSession, model_id: uuid.UUID, user_id: uuid.UUID) -> MLModelResponse:
    model = await model_registry.promote_model(db, model_id, user_id)
    return MLModelResponse.model_validate(model)


async def retire_model(db: AsyncSession, model_id: uuid.UUID) -> MLModelResponse:
    model = await model_registry.retire_model(db, model_id)
    return MLModelResponse.model_validate(model)


async def compare_models(db: AsyncSession, model_ids: list[uuid.UUID]) -> ModelCompareResponse:
    models: list[MLModel] = []
    for mid in model_ids:
        m = await model_registry.get_model(db, mid)
        models.append(m)

    metric_keys = set()
    for m in models:
        if m.metrics:
            metric_keys.update(m.metrics.keys())

    comparison: dict[str, dict[str, float | None]] = {}
    for key in sorted(metric_keys):
        comparison[key] = {}
        for m in models:
            comparison[key][str(m.id)] = m.metrics.get(key) if m.metrics else None

    return ModelCompareResponse(
        models=[MLModelResponse.model_validate(m) for m in models],
        metric_comparison=comparison,
    )
