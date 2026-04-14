"""Analytics endpoints — KPI dashboard data."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert
from app.dependencies import CurrentUser

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """KPI overview for the dashboard."""
    tenant_id = current_user.tenant_id
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total transactions today
    today_txn = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == tenant_id,
            Transaction.transaction_timestamp >= today_start,
            Transaction.is_test == False,  # noqa: E712
        )
    )

    # All-time fraud count
    fraud_count = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == tenant_id,
            Transaction.fraud_category == "fraudulent",
            Transaction.is_test == False,  # noqa: E712
        )
    )

    # Total all-time
    total_count = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == tenant_id,
            Transaction.is_test == False,  # noqa: E712
        )
    )

    # Open alerts
    open_alerts = await db.execute(
        select(func.count(FraudAlert.id)).where(
            FraudAlert.tenant_id == tenant_id,
            FraudAlert.status == "open",
        )
    )

    # Critical alerts
    critical_alerts = await db.execute(
        select(func.count(FraudAlert.id)).where(
            FraudAlert.tenant_id == tenant_id,
            FraudAlert.status == "open",
            FraudAlert.severity == "critical",
        )
    )

    total = total_count.scalar_one() or 0
    fraud = fraud_count.scalar_one() or 0
    fraud_rate = round((fraud / total * 100), 2) if total > 0 else 0.0

    return {
        "transactions_today": today_txn.scalar_one() or 0,
        "total_transactions": total,
        "fraud_count": fraud,
        "fraud_rate_percent": fraud_rate,
        "open_alerts": open_alerts.scalar_one() or 0,
        "critical_alerts": critical_alerts.scalar_one() or 0,
    }


@router.get("/fraud-rate")
async def get_fraud_rate(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Daily fraud rate over N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Transaction.transaction_timestamp).label("date"),
            func.count(Transaction.id).label("total"),
            func.sum(func.cast(Transaction.fraud_category == "fraudulent", int)).label("fraud"),
        )
        .where(
            Transaction.tenant_id == current_user.tenant_id,
            Transaction.transaction_timestamp >= since,
            Transaction.is_test == False,  # noqa: E712
        )
        .group_by(func.date(Transaction.transaction_timestamp))
        .order_by(func.date(Transaction.transaction_timestamp))
    )

    rows = result.all()
    return {
        "period_days": days,
        "data": [
            {
                "date": str(r.date),
                "total": r.total,
                "fraud": int(r.fraud or 0),
                "fraud_rate": round(int(r.fraud or 0) / r.total * 100, 2) if r.total > 0 else 0,
            }
            for r in rows
        ],
    }
