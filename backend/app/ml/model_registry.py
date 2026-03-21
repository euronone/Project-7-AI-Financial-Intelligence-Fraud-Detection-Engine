"""Model registry for versioning, loading, promoting, and retiring ML models."""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.ml_model import MLModel, ModelStatus, ModelType

logger = structlog.get_logger()


async def list_models(
    db: AsyncSession,
    *,
    model_type: str | None = None,
    status: str | None = None,
) -> list[MLModel]:
    query = select(MLModel).order_by(MLModel.created_at.desc())
    if model_type:
        query = query.where(MLModel.model_type == model_type)
    if status:
        query = query.where(MLModel.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_model(db: AsyncSession, model_id: uuid.UUID) -> MLModel:
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise NotFoundException("MLModel", str(model_id))
    return model


async def get_active_model(db: AsyncSession, model_type: ModelType) -> MLModel | None:
    result = await db.execute(
        select(MLModel)
        .where(MLModel.model_type == model_type, MLModel.status == ModelStatus.ACTIVE)
        .order_by(MLModel.promoted_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def register_model(
    db: AsyncSession,
    *,
    name: str,
    model_type: ModelType,
    version: str,
    framework: str,
    metrics: dict,
    artifact_path: str,
    parameters: dict | None = None,
    training_dataset_info: dict | None = None,
) -> MLModel:
    model = MLModel(
        name=name,
        model_type=model_type,
        version=version,
        status=ModelStatus.VALIDATING,
        framework=framework,
        metrics=metrics,
        parameters=parameters,
        artifact_path=artifact_path,
        training_dataset_info=training_dataset_info,
    )
    db.add(model)
    await db.flush()
    logger.info("model_registered", model_id=str(model.id), name=name, version=version)
    return model


async def promote_model(
    db: AsyncSession,
    model_id: uuid.UUID,
    user_id: uuid.UUID,
) -> MLModel:
    model = await get_model(db, model_id)
    if model.status == ModelStatus.ACTIVE:
        return model

    await db.execute(
        update(MLModel)
        .where(MLModel.model_type == model.model_type, MLModel.status == ModelStatus.ACTIVE)
        .values(status=ModelStatus.RETIRED)
    )

    model.status = ModelStatus.ACTIVE
    model.promoted_at = datetime.now(timezone.utc)
    model.promoted_by = user_id
    await db.flush()
    logger.info("model_promoted", model_id=str(model.id), name=model.name)
    return model


async def retire_model(db: AsyncSession, model_id: uuid.UUID) -> MLModel:
    model = await get_model(db, model_id)
    model.status = ModelStatus.RETIRED
    await db.flush()
    logger.info("model_retired", model_id=str(model.id))
    return model
