import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionListResponse,
    TransactionResponse,
)
from app.services import transaction_service

router = APIRouter()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    risk_level: str | None = None,
    currency: str | None = None,
    country_code: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> TransactionListResponse:
    filters = TransactionFilters(
        status=status,
        transaction_type=transaction_type,
        channel=channel,
        risk_level=risk_level,
        currency=currency,
        country_code=country_code,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )
    return await transaction_service.list_transactions(db, page=page, page_size=page_size, filters=filters)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> TransactionResponse:
    txn = await transaction_service.get_transaction(db, transaction_id)
    return TransactionResponse.model_validate(txn)


@router.post("", response_model=TransactionResponse, status_code=201)
async def ingest_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionResponse:
    txn = await transaction_service.ingest_transaction(db, data)
    return TransactionResponse.model_validate(txn)


@router.post("/batch", response_model=MessageResponse, status_code=201)
async def batch_ingest(
    items: list[TransactionCreate],
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> MessageResponse:
    created = await transaction_service.batch_ingest(db, items)
    return MessageResponse(message=f"{len(created)} transactions ingested")
