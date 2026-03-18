"""Transaction API endpoints — F1.1, F1.4, F1.5, F1.6, F1.7.

Routes are intentionally thin: validation, dependency injection,
and response shaping only. Business logic lives in TransactionService.
"""
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import (
    BatchIngestRequest,
    BatchIngestResponse,
    TransactionCreate,
    TransactionDetail,
    TransactionResponse,
    TransactionSearchRequest,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = structlog.get_logger(__name__)


def get_transaction_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    """Dependency: inject TransactionService with the current DB session."""
    return TransactionService(db)


# ── Single ingest (F1.1) ──────────────────────────────────────────────────────

@router.post(
    "",
    response_model=TransactionDetail,
    status_code=201,
    summary="Ingest a single transaction",
    description=(
        "Ingest a transaction and immediately run the fraud detection pipeline. "
        "Returns the transaction with fraud score, risk level, and component breakdown. "
        "Target latency: <200ms P95 (F1.2)."
    ),
)
async def ingest_transaction(
    body: TransactionCreate,
    svc: TransactionService = Depends(get_transaction_service),
) -> TransactionDetail:
    return await svc.ingest(body)


# ── Batch ingest (F1.4) ───────────────────────────────────────────────────────

@router.post(
    "/batch",
    response_model=BatchIngestResponse,
    status_code=202,
    summary="Batch ingest transactions",
    description=(
        "Ingest up to 10,000 transactions in a single request. "
        "Transactions are processed in chunks. Partial success is supported — "
        "the response lists accepted and rejected counts with per-item errors."
    ),
)
async def batch_ingest_transactions(
    body: BatchIngestRequest,
    svc: TransactionService = Depends(get_transaction_service),
) -> BatchIngestResponse:
    return await svc.batch_ingest(body)


# ── List / filter (F1.5) ──────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[TransactionResponse],
    summary="List transactions",
    description=(
        "Paginated, filtered, and sorted transaction list. "
        "Supports all filter dimensions: status, risk level, amount, date, "
        "entity, channel, country, fraud score."
    ),
)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort_by: str = Query(default="processed_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    status: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, ge=0),
    max_amount: Optional[float] = Query(default=None, ge=0),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    entity_id: Optional[uuid.UUID] = Query(default=None),
    channel: Optional[str] = Query(default=None),
    country_code: Optional[str] = Query(default=None, min_length=2, max_length=2),
    query: Optional[str] = Query(default=None),
    svc: TransactionService = Depends(get_transaction_service),
) -> PaginatedResponse[TransactionResponse]:
    from app.models.transaction import (
        TransactionChannel,
        TransactionRiskLevel,
        TransactionStatus,
    )
    from datetime import datetime
    from decimal import Decimal

    search = TransactionSearchRequest(
        query=query,
        status=[TransactionStatus(s) for s in status.split(",") if s] if status else None,
        risk_level=[TransactionRiskLevel(r) for r in risk_level.split(",") if r] if risk_level else None,
        channel=[TransactionChannel(c) for c in channel.split(",") if c] if channel else None,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        entity_id=entity_id,
        country_code=country_code,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    items, total = await svc.search(search)
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


# ── Advanced search (F1.5) ────────────────────────────────────────────────────

@router.post(
    "/search",
    response_model=PaginatedResponse[TransactionResponse],
    summary="Advanced transaction search",
    description=(
        "Complex search with multi-value filters. Accepts a JSON body instead of "
        "query parameters, allowing combinations not expressible as GET params."
    ),
)
async def search_transactions(
    body: TransactionSearchRequest,
    svc: TransactionService = Depends(get_transaction_service),
) -> PaginatedResponse[TransactionResponse]:
    items, total = await svc.search(body)
    return PaginatedResponse.build(
        items=items,
        total=total,
        page=body.page,
        page_size=body.page_size,
    )


# ── Export (F1.7) ─────────────────────────────────────────────────────────────

@router.get(
    "/export",
    summary="Export transactions",
    description=(
        "Export all transactions matching the current filters as CSV or JSON. "
        "Returns a file download response."
    ),
)
async def export_transactions(
    fmt: str = Query(default="csv", pattern="^(csv|json)$"),
    status: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, ge=0),
    max_amount: Optional[float] = Query(default=None, ge=0),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    entity_id: Optional[uuid.UUID] = Query(default=None),
    channel: Optional[str] = Query(default=None),
    country_code: Optional[str] = Query(default=None),
    query: Optional[str] = Query(default=None),
    svc: TransactionService = Depends(get_transaction_service),
) -> Response:
    from app.models.transaction import (
        TransactionChannel,
        TransactionRiskLevel,
        TransactionStatus,
    )
    from datetime import datetime
    from decimal import Decimal

    search = TransactionSearchRequest(
        query=query,
        status=[TransactionStatus(s) for s in status.split(",") if s] if status else None,
        risk_level=[TransactionRiskLevel(r) for r in risk_level.split(",") if r] if risk_level else None,
        channel=[TransactionChannel(c) for c in channel.split(",") if c] if channel else None,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        entity_id=entity_id,
        country_code=country_code,
        page=1,
        page_size=10000,
    )

    data = await svc.export(search, fmt=fmt)
    media_type = "text/csv" if fmt == "csv" else "application/json"
    filename = f"transactions_export.{fmt}"

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Detail (F1.6) ─────────────────────────────────────────────────────────────

@router.get(
    "/{transaction_id}",
    response_model=TransactionDetail,
    summary="Get transaction detail",
    description=(
        "Full transaction detail: raw fields, fraud score with component breakdown, "
        "entity context, and related counts."
    ),
)
async def get_transaction(
    transaction_id: uuid.UUID,
    svc: TransactionService = Depends(get_transaction_service),
) -> TransactionDetail:
    return await svc.get_by_id(transaction_id)


@router.get(
    "/{transaction_id}/similar",
    response_model=list[TransactionResponse],
    summary="Find similar transactions",
    description=(
        "Returns transactions with similar entity, channel, and amount characteristics. "
        "Full ML-powered similarity scoring is available in F2."
    ),
)
async def get_similar_transactions(
    transaction_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=50),
    svc: TransactionService = Depends(get_transaction_service),
) -> list[TransactionResponse]:
    return await svc.find_similar(transaction_id, limit=limit)
