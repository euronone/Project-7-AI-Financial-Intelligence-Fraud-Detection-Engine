import math
import uuid
from decimal import Decimal

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.entity import Entity
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.schemas.entity import (
    EntityCreate,
    EntityDetailResponse,
    EntityFilters,
    EntityListResponse,
    EntityResponse,
    EntityUpdate,
)

logger = structlog.get_logger()


async def get_entity(db: AsyncSession, entity_id: uuid.UUID) -> Entity:
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    if entity is None:
        raise NotFoundError("Entity", str(entity_id))
    return entity


async def get_entity_detail(db: AsyncSession, entity_id: uuid.UUID) -> EntityDetailResponse:
    """Entity 360 view with aggregated stats."""
    entity = await get_entity(db, entity_id)

    txn_count_result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.source_entity_id == entity_id)
    )
    txn_count = txn_count_result.scalar() or 0

    txn_sum_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .select_from(Transaction)
        .where(Transaction.source_entity_id == entity_id)
    )
    txn_sum = txn_sum_result.scalar() or Decimal("0")

    alert_count_result = await db.execute(
        select(func.count()).select_from(FraudAlert).where(FraudAlert.entity_id == entity_id)
    )
    alert_count = alert_count_result.scalar() or 0

    base = EntityResponse.model_validate(entity)
    return EntityDetailResponse(
        **base.model_dump(),
        transaction_count=txn_count,
        total_transaction_amount=Decimal(str(txn_sum)),
        alert_count=alert_count,
        open_case_count=0,
    )


async def list_entities(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    filters: EntityFilters | None = None,
) -> EntityListResponse:
    query = select(Entity)
    count_query = select(func.count()).select_from(Entity)

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
        query.order_by(Entity.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return EntityListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[EntityResponse.model_validate(e) for e in items],
    )


async def create_entity(db: AsyncSession, data: EntityCreate) -> Entity:
    existing = await db.execute(
        select(Entity).where(Entity.external_id == data.external_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Entity '{data.external_id}' already exists")

    entity = Entity(
        external_id=data.external_id,
        entity_type=data.entity_type,
        name=data.name,
        email=data.email,
        phone=data.phone,
        country_code=data.country_code,
    )
    db.add(entity)
    await db.flush()
    logger.info("entity_created", entity_id=str(entity.id), external_id=entity.external_id)
    return entity


async def update_entity(db: AsyncSession, entity_id: uuid.UUID, data: EntityUpdate) -> Entity:
    entity = await get_entity(db, entity_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)
    await db.flush()
    logger.info("entity_updated", entity_id=str(entity.id), fields=list(update_data.keys()))
    return entity


def _build_filter_conditions(filters: EntityFilters) -> list:
    conditions = []
    if filters.entity_type:
        conditions.append(Entity.entity_type == filters.entity_type)
    if filters.risk_level:
        conditions.append(Entity.risk_level == filters.risk_level)
    if filters.kyc_status:
        conditions.append(Entity.kyc_status == filters.kyc_status)
    if filters.country_code:
        conditions.append(Entity.country_code == filters.country_code)
    if filters.is_watchlisted is not None:
        conditions.append(Entity.is_watchlisted == filters.is_watchlisted)
    if filters.search:
        conditions.append(
            Entity.name.ilike(f"%{filters.search}%") | Entity.external_id.ilike(f"%{filters.search}%")
        )
    return conditions
