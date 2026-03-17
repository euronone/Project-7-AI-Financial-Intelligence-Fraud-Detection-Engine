import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user, require_admin, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.ml_model import MLModelListResponse, MLModelResponse, ModelCompareResponse
from app.services import ml_service

router = APIRouter()


@router.get("", response_model=MLModelListResponse)
async def list_models(
    model_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> MLModelListResponse:
    return await ml_service.list_models(db, model_type=model_type, status=status)


@router.get("/{model_id}", response_model=MLModelResponse)
async def get_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> MLModelResponse:
    return await ml_service.get_model(db, model_id)


@router.post("/{model_id}/promote", response_model=MLModelResponse)
async def promote_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> MLModelResponse:
    return await ml_service.promote_model(db, model_id, user.id)


@router.post("/{model_id}/retire", response_model=MLModelResponse)
async def retire_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> MLModelResponse:
    return await ml_service.retire_model(db, model_id)


@router.post("/compare", response_model=ModelCompareResponse)
async def compare_models(
    model_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> ModelCompareResponse:
    return await ml_service.compare_models(db, model_ids)
