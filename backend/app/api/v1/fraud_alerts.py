"""Fraud alert endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.fraud_alert import FraudAlert
from app.schemas.alert import AlertResponse, AlertUpdateRequest, AlertListResponse
from app.dependencies import CurrentUser, AnalystUser
from app.core.exceptions import NotFoundException
from datetime import datetime, timezone

router = APIRouter(prefix="/alerts", tags=["Fraud Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    severity: str | None = Query(None),
    status: str | None = Query(None),
):
    query = select(FraudAlert).where(FraudAlert.tenant_id == current_user.tenant_id)

    if severity:
        query = query.where(FraudAlert.severity == severity)
    if status:
        query = query.where(FraudAlert.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(FraudAlert.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return AlertListResponse(items=list(items), total=total, page=page, per_page=per_page)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FraudAlert).where(
            FraudAlert.id == alert_id,
            FraudAlert.tenant_id == current_user.tenant_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundException("Alert")
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    body: AlertUpdateRequest,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    """Update alert status (confirm fraud, mark false positive, close, etc.)."""
    result = await db.execute(
        select(FraudAlert).where(
            FraudAlert.id == alert_id,
            FraudAlert.tenant_id == current_user.tenant_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundException("Alert")

    alert.status = body.status
    alert.analyst_id = current_user.id
    if body.resolution_notes:
        alert.resolution_notes = body.resolution_notes
    if body.status in ("confirmed_fraud", "false_positive", "closed"):
        alert.resolved_at = datetime.now(timezone.utc)
        alert.is_confirmed = body.status == "confirmed_fraud"

    await db.commit()
    await db.refresh(alert)
    return alert
