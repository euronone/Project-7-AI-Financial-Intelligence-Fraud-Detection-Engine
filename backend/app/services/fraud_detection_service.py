"""Wires ML pipeline output to alert creation."""

import math
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.fraud_alert import AlertSeverity, AlertStatus, AlertType, FraudAlert
from app.schemas.fraud_alert import (
    AlertAssign,
    AlertListResponse,
    AlertResponse,
    AlertStatistics,
    AlertStatusUpdate,
)

logger = structlog.get_logger()

SEVERITY_THRESHOLDS = [
    (0.8, AlertSeverity.CRITICAL),
    (0.6, AlertSeverity.HIGH),
    (0.4, AlertSeverity.MEDIUM),
    (0.0, AlertSeverity.LOW),
]


def _score_to_severity(score: float) -> AlertSeverity:
    for threshold, severity in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return severity
    return AlertSeverity.LOW


async def create_alert_from_pipeline(
    db: AsyncSession,
    *,
    transaction_id: uuid.UUID,
    entity_id: uuid.UUID | None,
    pipeline_result: dict,
) -> FraudAlert:
    """Create an alert from ML pipeline results when risk is elevated."""
    score = pipeline_result.get("overall_score", 0)
    severity = _score_to_severity(score)
    explanation = pipeline_result.get("explanation", {})

    alert = FraudAlert(
        transaction_id=transaction_id,
        entity_id=entity_id,
        alert_type=AlertType.ML_DETECTION,
        severity=severity,
        status=AlertStatus.OPEN,
        title=f"Fraud risk detected (score: {score:.1%})",
        description=explanation.get("summary", "ML pipeline flagged this transaction."),
        confidence_score=score,
        evidence={
            "component_scores": pipeline_result.get("component_scores"),
            "risk_factors": pipeline_result.get("risk_factors"),
            "explanation": explanation,
        },
    )
    db.add(alert)
    await db.flush()
    logger.info("alert_created_from_pipeline", alert_id=str(alert.id), score=score)
    return alert


async def list_alerts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    severity: str | None = None,
    alert_type: str | None = None,
) -> AlertListResponse:
    query = select(FraudAlert)
    count_q = select(func.count()).select_from(FraudAlert)

    if status:
        query = query.where(FraudAlert.status == status)
        count_q = count_q.where(FraudAlert.status == status)
    if severity:
        query = query.where(FraudAlert.severity == severity)
        count_q = count_q.where(FraudAlert.severity == severity)
    if alert_type:
        query = query.where(FraudAlert.alert_type == alert_type)
        count_q = count_q.where(FraudAlert.alert_type == alert_type)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(FraudAlert.created_at.desc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return AlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[AlertResponse.model_validate(a) for a in items],
    )


async def get_alert(db: AsyncSession, alert_id: uuid.UUID) -> FraudAlert:
    result = await db.execute(select(FraudAlert).where(FraudAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise NotFoundException("FraudAlert", str(alert_id))
    return alert


async def update_alert_status(
    db: AsyncSession,
    alert_id: uuid.UUID,
    data: AlertStatusUpdate,
    user_id: uuid.UUID,
) -> FraudAlert:
    alert = await get_alert(db, alert_id)
    alert.status = data.status

    if data.status in (AlertStatus.RESOLVED_FRAUD, AlertStatus.RESOLVED_FALSE_POSITIVE, AlertStatus.DISMISSED):
        alert.resolved_by = user_id
        alert.resolved_at = datetime.now(timezone.utc)
        if data.resolution_notes:
            alert.resolution_notes = data.resolution_notes

    await db.flush()
    await db.refresh(alert)
    logger.info("alert_status_updated", alert_id=str(alert_id), status=data.status.value)
    return alert


async def assign_alert(db: AsyncSession, alert_id: uuid.UUID, data: AlertAssign) -> FraudAlert:
    alert = await get_alert(db, alert_id)
    alert.assigned_to = data.assigned_to
    if alert.status == AlertStatus.OPEN:
        alert.status = AlertStatus.INVESTIGATING
    await db.flush()
    await db.refresh(alert)
    logger.info("alert_assigned", alert_id=str(alert_id), assigned_to=str(data.assigned_to))
    return alert


async def escalate_alert(db: AsyncSession, alert_id: uuid.UUID) -> FraudAlert:
    alert = await get_alert(db, alert_id)
    alert.status = AlertStatus.ESCALATED
    await db.flush()
    await db.refresh(alert)
    logger.info("alert_escalated", alert_id=str(alert_id))
    return alert


async def get_alert_statistics(db: AsyncSession) -> AlertStatistics:
    total = (await db.execute(select(func.count()).select_from(FraudAlert))).scalar() or 0

    status_counts: dict[str, int] = {}
    for s in AlertStatus:
        count = (await db.execute(
            select(func.count()).select_from(FraudAlert).where(FraudAlert.status == s)
        )).scalar() or 0
        status_counts[s.value] = count

    sev_counts: dict[str, int] = {}
    for s in AlertSeverity:
        count = (await db.execute(
            select(func.count()).select_from(FraudAlert).where(FraudAlert.severity == s)
        )).scalar() or 0
        sev_counts[s.value] = count

    type_counts: dict[str, int] = {}
    for t in AlertType:
        count = (await db.execute(
            select(func.count()).select_from(FraudAlert).where(FraudAlert.alert_type == t)
        )).scalar() or 0
        type_counts[t.value] = count

    return AlertStatistics(
        total=total,
        open=status_counts.get("open", 0),
        investigating=status_counts.get("investigating", 0),
        escalated=status_counts.get("escalated", 0),
        resolved_fraud=status_counts.get("resolved_fraud", 0),
        resolved_false_positive=status_counts.get("resolved_false_positive", 0),
        dismissed=status_counts.get("dismissed", 0),
        by_severity=sev_counts,
        by_type=type_counts,
    )
