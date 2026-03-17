import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.entity import (
    EntityCreate,
    EntityDetailResponse,
    EntityFilters,
    EntityListResponse,
    EntityResponse,
    EntityUpdate,
)
from app.schemas.transaction import TransactionFilters, TransactionListResponse
from app.services import entity_service, transaction_service

router = APIRouter()


@router.get("", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    entity_type: str | None = None,
    risk_level: str | None = None,
    kyc_status: str | None = None,
    country_code: str | None = None,
    is_watchlisted: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> EntityListResponse:
    filters = EntityFilters(
        entity_type=entity_type,
        risk_level=risk_level,
        kyc_status=kyc_status,
        country_code=country_code,
        is_watchlisted=is_watchlisted,
        search=search,
    )
    return await entity_service.list_entities(db, page=page, page_size=page_size, filters=filters)


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> EntityDetailResponse:
    return await entity_service.get_entity_detail(db, entity_id)


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(
    data: EntityCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EntityResponse:
    entity = await entity_service.create_entity(db, data)
    return EntityResponse.model_validate(entity)


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: uuid.UUID,
    data: EntityUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EntityResponse:
    entity = await entity_service.update_entity(db, entity_id, data)
    return EntityResponse.model_validate(entity)


@router.get("/{entity_id}/transactions", response_model=TransactionListResponse)
async def get_entity_transactions(
    entity_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> TransactionListResponse:
    await entity_service.get_entity(db, entity_id)
    filters = TransactionFilters(source_entity_id=entity_id)
    return await transaction_service.list_transactions(db, page=page, page_size=page_size, filters=filters)
