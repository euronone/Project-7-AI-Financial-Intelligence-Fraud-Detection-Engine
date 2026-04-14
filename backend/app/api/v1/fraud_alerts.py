"""Fraud alert endpoints — list, detail, update, report-fraud, freeze account."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.models.customer import Customer
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

    query = (
        query.order_by(FraudAlert.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
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


# ---------------------------------------------------------------------------
# POST /alerts/{alert_id}/report-fraud
# Customer / analyst marks an alert as confirmed fraud
# ---------------------------------------------------------------------------


class ReportFraudRequest(BaseModel):
    notes: str | None = None
    freeze_account: bool = False  # If True, freeze the customer's account (admin action)


@router.post("/{alert_id}/report-fraud")
async def report_fraud(
    alert_id: str,
    body: ReportFraudRequest,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm an alert as fraud.
    - Sets alert status to 'confirmed_fraud'
    - Marks the linked transaction as fraudulent + blocked
    - Optionally freezes the customer account (admin-only action)
    """
    result = await db.execute(
        select(FraudAlert).where(
            FraudAlert.id == alert_id,
            FraudAlert.tenant_id == current_user.tenant_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundException("Alert")

    # Update alert
    alert.status = "confirmed_fraud"
    alert.is_confirmed = True
    alert.analyst_id = current_user.id
    alert.resolution_notes = body.notes or "Reported as confirmed fraud"
    alert.resolved_at = datetime.now(timezone.utc)

    # Update linked transaction
    if alert.transaction_id:
        txn_result = await db.execute(
            select(Transaction).where(Transaction.id == alert.transaction_id)
        )
        txn = txn_result.scalar_one_or_none()
        if txn:
            txn.fraud_category = "fraudulent"
            txn.is_flagged = True
            txn.is_blocked = True
            txn.status = "blocked"

    # Optionally freeze customer account (admin-only)
    customer_frozen = False
    if body.freeze_account and current_user.role == "admin" and alert.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == alert.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer.account_status = "suspended"
            customer_frozen = True

    await db.commit()
    await db.refresh(alert)

    return {
        "message": "Fraud confirmed",
        "alert_id": alert_id,
        "transaction_blocked": True,
        "customer_frozen": customer_frozen,
    }


# ---------------------------------------------------------------------------
# GET /alerts/summary — fraud stats summary (for dashboard)
# ---------------------------------------------------------------------------


@router.get("/summary")
async def alert_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return quick count of alerts by severity and status."""
    result = await db.execute(
        select(FraudAlert).where(FraudAlert.tenant_id == current_user.tenant_id)
    )
    all_alerts = result.scalars().all()

    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_status = {
        "open": 0,
        "under_review": 0,
        "confirmed_fraud": 0,
        "false_positive": 0,
        "closed": 0,
    }

    for a in all_alerts:
        if a.severity in by_severity:
            by_severity[a.severity] += 1
        if a.status in by_status:
            by_status[a.status] += 1

    return {
        "total": len(all_alerts),
        "by_severity": by_severity,
        "by_status": by_status,
    }
