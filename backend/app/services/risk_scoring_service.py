"""Service layer for risk scoring and ML pipeline execution."""

import math
import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.ml.pipeline import run_pipeline
from app.models.entity import Entity
from app.models.risk_score import RiskScore
from app.models.transaction import Transaction
from app.schemas.ml_model import (
    PipelineResultResponse,
    RiskDistribution,
    RiskScoreListResponse,
    RiskScoreResponse,
    TopRiskEntity,
)

logger = structlog.get_logger()


async def score_transaction(
    db: AsyncSession,
    transaction_id: uuid.UUID,
) -> PipelineResultResponse:
    """Run the full ML pipeline on a transaction and persist the risk score."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    txn = result.scalar_one_or_none()
    if txn is None:
        raise NotFoundException("Transaction", str(transaction_id))

    txn_dict = _txn_to_dict(txn)

    history = await _get_entity_history(db, txn.source_entity_id, limit=50)
    network_txns = await _get_network_transactions(db, txn.source_entity_id, limit=100)

    pipeline_result = run_pipeline(
        txn_dict,
        entity_history=history,
        network_transactions=network_txns,
    )

    risk_score = RiskScore(
        entity_id=txn.source_entity_id,
        transaction_id=txn.id,
        overall_score=pipeline_result["overall_score"],
        component_scores=pipeline_result["component_scores"],
        risk_factors={"factors": pipeline_result["risk_factors"]},
        model_version="dev-1.0",
        explanation=pipeline_result["explanation"]["summary"],
    )
    db.add(risk_score)

    txn.fraud_score = pipeline_result["overall_score"]
    txn.risk_level = pipeline_result["risk_level"]

    await db.flush()

    logger.info(
        "transaction_scored",
        txn_id=str(transaction_id),
        score=pipeline_result["overall_score"],
        level=pipeline_result["risk_level"],
    )

    return PipelineResultResponse(**pipeline_result)


async def calculate_entity_risk(db: AsyncSession, entity_id: uuid.UUID) -> PipelineResultResponse:
    """Calculate risk score for an entity based on their latest transaction."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.source_entity_id == entity_id)
        .order_by(Transaction.processed_at.desc())
        .limit(1)
    )
    txn = result.scalar_one_or_none()
    if txn is None:
        raise NotFoundException("Transaction for entity", str(entity_id))

    return await score_transaction(db, txn.id)


async def get_entity_risk_history(
    db: AsyncSession,
    entity_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
) -> RiskScoreListResponse:
    count_q = select(func.count()).select_from(RiskScore).where(RiskScore.entity_id == entity_id)
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    q = (
        select(RiskScore)
        .where(RiskScore.entity_id == entity_id)
        .order_by(RiskScore.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(q)
    items = result.scalars().all()

    return RiskScoreListResponse(
        total=total,
        items=[RiskScoreResponse.model_validate(r) for r in items],
    )


async def get_risk_distribution(db: AsyncSession) -> RiskDistribution:
    """Get distribution of latest risk scores across all entities."""
    subq = (
        select(
            RiskScore.entity_id,
            func.max(RiskScore.created_at).label("latest"),
        )
        .group_by(RiskScore.entity_id)
        .subquery()
    )

    q = select(RiskScore.overall_score).join(
        subq,
        (RiskScore.entity_id == subq.c.entity_id) & (RiskScore.created_at == subq.c.latest),
    )
    result = await db.execute(q)
    scores = [float(r[0]) for r in result.all()]

    dist = {"low": 0, "medium_low": 0, "medium": 0, "high": 0, "critical": 0}
    for s in scores:
        if s < 0.2:
            dist["low"] += 1
        elif s < 0.4:
            dist["medium_low"] += 1
        elif s < 0.6:
            dist["medium"] += 1
        elif s < 0.8:
            dist["high"] += 1
        else:
            dist["critical"] += 1

    return RiskDistribution(**dist, total=len(scores))


async def get_top_risk_entities(
    db: AsyncSession, *, limit: int = 10
) -> list[TopRiskEntity]:
    subq = (
        select(
            RiskScore.entity_id,
            func.max(RiskScore.created_at).label("latest"),
        )
        .group_by(RiskScore.entity_id)
        .subquery()
    )

    q = (
        select(RiskScore, Entity.name)
        .join(subq, (RiskScore.entity_id == subq.c.entity_id) & (RiskScore.created_at == subq.c.latest))
        .outerjoin(Entity, Entity.id == RiskScore.entity_id)
        .order_by(RiskScore.overall_score.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()

    return [
        TopRiskEntity(
            entity_id=str(rs.entity_id),
            entity_name=name,
            risk_score=float(rs.overall_score),
            risk_level=_level(float(rs.overall_score)),
            last_scored=rs.created_at,
        )
        for rs, name in rows
    ]


def _level(score: float) -> str:
    if score < 0.2:
        return "low"
    if score < 0.4:
        return "medium_low"
    if score < 0.6:
        return "medium"
    if score < 0.8:
        return "high"
    return "critical"


def _txn_to_dict(txn: Transaction) -> dict:
    return {
        "id": str(txn.id),
        "amount": float(txn.amount) if txn.amount else 0,
        "currency": txn.currency,
        "transaction_type": txn.transaction_type.value if hasattr(txn.transaction_type, "value") else str(txn.transaction_type),
        "channel": txn.channel.value if hasattr(txn.channel, "value") else str(txn.channel),
        "status": txn.status.value if hasattr(txn.status, "value") else str(txn.status),
        "country_code": txn.country_code,
        "ip_address": str(txn.ip_address) if txn.ip_address else None,
        "device_fingerprint": txn.device_fingerprint,
        "geolocation_lat": float(txn.geolocation_lat) if txn.geolocation_lat else None,
        "geolocation_lng": float(txn.geolocation_lng) if txn.geolocation_lng else None,
        "card_present": txn.card_present,
        "source_entity_id": str(txn.source_entity_id),
        "destination_entity_id": str(txn.destination_entity_id) if txn.destination_entity_id else None,
        "processed_at": txn.processed_at.isoformat() if hasattr(txn.processed_at, "isoformat") else str(txn.processed_at),
    }


async def _get_entity_history(db: AsyncSession, entity_id: uuid.UUID, limit: int = 50) -> list[dict]:
    q = (
        select(Transaction)
        .where(Transaction.source_entity_id == entity_id)
        .order_by(Transaction.processed_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return [_txn_to_dict(t) for t in result.scalars().all()]


async def _get_network_transactions(db: AsyncSession, entity_id: uuid.UUID, limit: int = 100) -> list[dict]:
    q = (
        select(Transaction)
        .where(
            (Transaction.source_entity_id == entity_id)
            | (Transaction.destination_entity_id == entity_id)
        )
        .order_by(Transaction.processed_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return [_txn_to_dict(t) for t in result.scalars().all()]
