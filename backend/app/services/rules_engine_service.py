import math
import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.rule import Rule
from app.rules.engine import evaluate_single_rule, evaluate_transaction
from app.rules.templates import get_templates
from app.schemas.rule import (
    RuleCreate,
    RuleListResponse,
    RulePerformance,
    RuleResponse,
    RuleTestResult,
    RuleUpdate,
)

logger = structlog.get_logger()


async def list_rules(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    is_active: bool | None = None,
    category: str | None = None,
) -> RuleListResponse:
    query = select(Rule)
    count_query = select(func.count()).select_from(Rule)

    if is_active is not None:
        query = query.where(Rule.is_active == is_active)
        count_query = count_query.where(Rule.is_active == is_active)
    if category:
        query = query.where(Rule.category == category)
        count_query = count_query.where(Rule.category == category)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Rule.priority.asc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return RuleListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[RuleResponse.model_validate(r) for r in items],
    )


async def get_rule(db: AsyncSession, rule_id: uuid.UUID) -> Rule:
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise NotFoundException("Rule", str(rule_id))
    return rule


async def create_rule(db: AsyncSession, data: RuleCreate, user_id: uuid.UUID) -> Rule:
    rule = Rule(
        name=data.name,
        description=data.description,
        category=data.category,
        conditions=data.conditions,
        actions=data.actions,
        severity=data.severity,
        priority=data.priority,
        is_active=data.is_active,
        created_by=user_id,
    )
    db.add(rule)
    await db.flush()
    logger.info("rule_created", rule_id=str(rule.id), name=rule.name)
    return rule


async def update_rule(db: AsyncSession, rule_id: uuid.UUID, data: RuleUpdate) -> Rule:
    rule = await get_rule(db, rule_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    await db.flush()
    logger.info("rule_updated", rule_id=str(rule.id), fields=list(update_data.keys()))
    return rule


async def toggle_rule(db: AsyncSession, rule_id: uuid.UUID, is_active: bool) -> Rule:
    rule = await get_rule(db, rule_id)
    rule.is_active = is_active
    await db.flush()
    logger.info("rule_toggled", rule_id=str(rule.id), is_active=is_active)
    return rule


async def delete_rule(db: AsyncSession, rule_id: uuid.UUID) -> None:
    rule = await get_rule(db, rule_id)
    await db.delete(rule)
    await db.flush()
    logger.info("rule_deleted", rule_id=str(rule_id))


async def test_rule(db: AsyncSession, rule_id: uuid.UUID, transaction: dict) -> RuleTestResult:
    result = await evaluate_single_rule(db, rule_id, transaction)
    return RuleTestResult(
        rule_id=str(result.rule_id),
        rule_name=result.rule_name,
        matched=result.matched,
        severity=result.severity,
        priority=result.priority,
        conditions=result.condition_results,
        actions=result.action_results,
    )


async def get_rule_performance(db: AsyncSession, rule_id: uuid.UUID) -> RulePerformance:
    rule = await get_rule(db, rule_id)
    return RulePerformance(
        rule_id=str(rule.id),
        rule_name=rule.name,
        hit_count=rule.hit_count,
        false_positive_rate=float(rule.false_positive_rate) if rule.false_positive_rate else None,
        is_active=rule.is_active,
        severity=rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
    )


def get_rule_templates() -> list[dict]:
    return get_templates()
