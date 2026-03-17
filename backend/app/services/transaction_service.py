import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionListResponse,
    TransactionResponse,
)

logger = structlog.get_logger()


async def get_transaction(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    txn = result.scalar_one_or_none()
    if txn is None:
        raise NotFoundException("Transaction", str(transaction_id))
    return txn


async def list_transactions(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    filters: TransactionFilters | None = None,
) -> TransactionListResponse:
    query = select(Transaction)
    count_query = select(func.count()).select_from(Transaction)

    if filters:
        conditions = _build_filter_conditions(filters)
        if conditions:
            combined = and_(*conditions)
            query = query.where(combined)
            count_query = count_query.where(combined)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Transaction.processed_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[TransactionResponse.model_validate(t) for t in items],
    )


async def ingest_transaction(db: AsyncSession, data: TransactionCreate) -> Transaction:
    existing = await db.execute(
        select(Transaction).where(Transaction.external_id == data.external_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Transaction '{data.external_id}' already exists")

    txn = Transaction(
        external_id=data.external_id,
        source_entity_id=data.source_entity_id,
        destination_entity_id=data.destination_entity_id,
        amount=data.amount,
        currency=data.currency,
        transaction_type=data.transaction_type,
        channel=data.channel,
        status=TransactionStatus.PENDING,
        merchant_category_code=data.merchant_category_code,
        description=data.description,
        ip_address=data.ip_address,
        device_fingerprint=data.device_fingerprint,
        country_code=data.country_code,
        card_present=data.card_present,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(txn)
    await db.flush()
    logger.info("transaction_ingested", txn_id=str(txn.id), external_id=txn.external_id)
    return txn


async def batch_ingest(db: AsyncSession, items: list[TransactionCreate]) -> list[Transaction]:
    transactions = []
    for data in items:
        txn = Transaction(
            external_id=data.external_id,
            source_entity_id=data.source_entity_id,
            destination_entity_id=data.destination_entity_id,
            amount=data.amount,
            currency=data.currency,
            transaction_type=data.transaction_type,
            channel=data.channel,
            status=TransactionStatus.PENDING,
            merchant_category_code=data.merchant_category_code,
            description=data.description,
            ip_address=data.ip_address,
            device_fingerprint=data.device_fingerprint,
            country_code=data.country_code,
            card_present=data.card_present,
            processed_at=datetime.now(timezone.utc),
        )
        db.add(txn)
        transactions.append(txn)
    await db.flush()
    logger.info("batch_ingested", count=len(transactions))
    return transactions


def _build_filter_conditions(filters: TransactionFilters) -> list:
    conditions = []
    if filters.status:
        conditions.append(Transaction.status == filters.status)
    if filters.transaction_type:
        conditions.append(Transaction.transaction_type == filters.transaction_type)
    if filters.channel:
        conditions.append(Transaction.channel == filters.channel)
    if filters.risk_level:
        conditions.append(Transaction.risk_level == filters.risk_level)
    if filters.currency:
        conditions.append(Transaction.currency == filters.currency)
    if filters.country_code:
        conditions.append(Transaction.country_code == filters.country_code)
    if filters.min_amount is not None:
        conditions.append(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        conditions.append(Transaction.amount <= filters.max_amount)
    if filters.date_from:
        conditions.append(Transaction.processed_at >= filters.date_from)
    if filters.date_to:
        conditions.append(Transaction.processed_at <= filters.date_to)
    if filters.source_entity_id:
        conditions.append(Transaction.source_entity_id == filters.source_entity_id)
    if filters.search:
        conditions.append(Transaction.external_id.ilike(f"%{filters.search}%"))
    return conditions
