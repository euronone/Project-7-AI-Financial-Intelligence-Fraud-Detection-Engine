"""
Customer analytics endpoints.

Provides:
  GET /api/v1/customers/stats              – totals, fraud count, high-risk count
  GET /api/v1/customers/charts/risk-dist   – risk score distribution buckets
  GET /api/v1/customers/charts/fraud-legit – fraud vs legitimate per customer tier
  GET /api/v1/customers/charts/activity    – daily transaction activity over N days
  GET /api/v1/customers/top-risky          – paginated table of riskiest profiles
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert
from app.models.payment_method import CustomerPaymentMethod

router = APIRouter(prefix="/customers", tags=["Customers"])


# ---------------------------------------------------------------------------
# 1. Stats card
# ---------------------------------------------------------------------------


@router.get("/stats")
async def get_customer_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns headline KPI numbers for the Customers dashboard:
    total customers, customers with at least one fraudulent transaction,
    high-risk customers (risk_score >= 0.70), and average risk score.
    """
    tid = current_user.tenant_id

    total_res = await db.execute(select(func.count(Customer.id)).where(Customer.tenant_id == tid))
    total = total_res.scalar_one() or 0

    # Customers who have had at least one fraudulent transaction
    fraud_sub = (
        select(Transaction.customer_id)
        .where(
            Transaction.tenant_id == tid,
            Transaction.fraud_category == "fraudulent",
            Transaction.is_test == False,  # noqa: E712
        )
        .distinct()
        .subquery()
    )
    fraud_cust_res = await db.execute(
        select(func.count(Customer.id)).where(Customer.id.in_(select(fraud_sub)))
    )
    fraud_customer_count = fraud_cust_res.scalar_one() or 0

    # High-risk: risk_score >= 0.70
    high_risk_res = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.tenant_id == tid,
            Customer.risk_score >= 0.70,
        )
    )
    high_risk_count = high_risk_res.scalar_one() or 0

    # Average risk score
    avg_res = await db.execute(
        select(func.avg(Customer.risk_score)).where(Customer.tenant_id == tid)
    )
    avg_risk = round(float(avg_res.scalar_one() or 0), 4)

    return {
        "total_customers": total,
        "fraud_customers": fraud_customer_count,
        "high_risk_customers": high_risk_count,
        "avg_risk_score": avg_risk,
    }


# ---------------------------------------------------------------------------
# 2. Chart: risk score distribution
# ---------------------------------------------------------------------------


@router.get("/charts/risk-dist")
async def get_risk_distribution(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns customer counts bucketed into 5 risk bands.
    Use this data for a pie/donut or bar chart on the frontend.

    Bands:
      low      0.00 – 0.20   (green)
      guarded  0.20 – 0.40   (yellow-green)
      medium   0.40 – 0.60   (yellow)
      high     0.60 – 0.80   (orange)
      critical 0.80 – 1.00   (red)
    """
    tid = current_user.tenant_id

    bands = [
        ("low", 0.00, 0.20, "#22C55E"),
        ("guarded", 0.20, 0.40, "#84CC16"),
        ("medium", 0.40, 0.60, "#EAB308"),
        ("high", 0.60, 0.80, "#F97316"),
        ("critical", 0.80, 1.01, "#EF4444"),
    ]

    result = []
    for label, lo, hi, color in bands:
        res = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.tenant_id == tid,
                Customer.risk_score >= lo,
                Customer.risk_score < hi,
            )
        )
        result.append(
            {
                "band": label,
                "min": lo,
                "max": hi,
                "count": res.scalar_one() or 0,
                "color": color,
            }
        )

    return {"distribution": result}


# ---------------------------------------------------------------------------
# 3. Chart: fraud vs legitimate breakdown per account tier
# ---------------------------------------------------------------------------


@router.get("/charts/fraud-legit")
async def get_fraud_vs_legit(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns fraud vs legitimate transaction counts broken down by
    customer_tier (standard / premium / vip).
    """
    tid = current_user.tenant_id

    rows = await db.execute(
        select(
            Customer.customer_tier,
            func.count(Transaction.id).label("total"),
            func.sum(case((Transaction.fraud_category == "fraudulent", 1), else_=0)).label("fraud"),
            func.sum(case((Transaction.fraud_category == "legitimate", 1), else_=0)).label(
                "legitimate"
            ),
        )
        .join(Transaction, Transaction.customer_id == Customer.id)
        .where(
            Customer.tenant_id == tid,
            Transaction.tenant_id == tid,
            Transaction.is_test == False,  # noqa: E712
        )
        .group_by(Customer.customer_tier)
    )

    data = []
    for row in rows.all():
        data.append(
            {
                "tier": row.customer_tier or "unknown",
                "total": row.total,
                "fraud": int(row.fraud or 0),
                "legitimate": int(row.legitimate or 0),
            }
        )

    return {"breakdown": data}


# ---------------------------------------------------------------------------
# 4. Chart: transaction activity over time
# ---------------------------------------------------------------------------


@router.get("/charts/activity")
async def get_activity_over_time(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=7, le=180),
):
    """
    Returns daily transaction counts (total + fraud) for the last N days.
    Suitable for a line or area chart.
    """
    tid = current_user.tenant_id
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = await db.execute(
        select(
            func.date(Transaction.transaction_timestamp).label("date"),
            func.count(Transaction.id).label("total"),
            func.sum(case((Transaction.fraud_category == "fraudulent", 1), else_=0)).label("fraud"),
        )
        .where(
            Transaction.tenant_id == tid,
            Transaction.transaction_timestamp >= since,
            Transaction.is_test == False,  # noqa: E712
        )
        .group_by(func.date(Transaction.transaction_timestamp))
        .order_by(func.date(Transaction.transaction_timestamp))
    )

    data = [
        {
            "date": str(row.date),
            "total": row.total,
            "fraud": int(row.fraud or 0),
        }
        for row in rows.all()
    ]

    return {"period_days": days, "activity": data}


# ---------------------------------------------------------------------------
# 5. Top risky profiles table
# ---------------------------------------------------------------------------


@router.get("/top-risky")
async def get_top_risky_customers(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or email"),
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    max_risk: float = Query(1.0, ge=0.0, le=1.0),
    account_type: Optional[str] = Query(None),
    kyc_status: Optional[str] = Query(None),
):
    """
    Paginated table of the most risky customer profiles.

    Returns for each customer:
      id, full_name, email, city, account_type, kyc_status,
      risk_score, transaction_count, fraud_flag_count, open_alerts
    """
    tid = current_user.tenant_id

    # Subquery: transaction counts per customer
    txn_counts = (
        select(
            Transaction.customer_id,
            func.count(Transaction.id).label("txn_total"),
            func.sum(case((Transaction.fraud_category == "fraudulent", 1), else_=0)).label(
                "txn_fraud"
            ),
        )
        .where(
            Transaction.tenant_id == tid,
            Transaction.is_test == False,  # noqa: E712
        )
        .group_by(Transaction.customer_id)
        .subquery()
    )

    # Subquery: open alert counts per customer
    alert_counts = (
        select(
            FraudAlert.customer_id,
            func.count(FraudAlert.id).label("open_alerts"),
        )
        .where(
            FraudAlert.tenant_id == tid,
            FraudAlert.status == "open",
        )
        .group_by(FraudAlert.customer_id)
        .subquery()
    )

    query = (
        select(
            Customer,
            func.coalesce(txn_counts.c.txn_total, 0).label("txn_total"),
            func.coalesce(txn_counts.c.txn_fraud, 0).label("txn_fraud"),
            func.coalesce(alert_counts.c.open_alerts, 0).label("open_alerts"),
        )
        .outerjoin(txn_counts, txn_counts.c.customer_id == Customer.id)
        .outerjoin(alert_counts, alert_counts.c.customer_id == Customer.id)
        .where(
            Customer.tenant_id == tid,
            Customer.risk_score >= min_risk,
            Customer.risk_score <= max_risk,
        )
    )

    if search:
        like_term = f"%{search}%"
        query = query.where(Customer.full_name.ilike(like_term) | Customer.email.ilike(like_term))
    if account_type:
        query = query.where(Customer.account_type == account_type)
    if kyc_status:
        query = query.where(Customer.kyc_status == kyc_status)

    # Total count for pagination
    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar_one()

    # Sorted by risk descending, then open alerts descending
    query = (
        query.order_by(
            Customer.risk_score.desc(), func.coalesce(alert_counts.c.open_alerts, 0).desc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    rows = await db.execute(query)
    raw_rows = rows.all()

    # Bulk-fetch primary payment methods for all customers in this page
    customer_ids = [row[0].id for row in raw_rows]
    pm_map: dict[str, dict] = {}
    if customer_ids:
        pm_res = await db.execute(
            select(CustomerPaymentMethod)
            .where(
                CustomerPaymentMethod.customer_id.in_(customer_ids),
                CustomerPaymentMethod.tenant_id == tid,
            )
            .order_by(
                CustomerPaymentMethod.customer_id,
                CustomerPaymentMethod.is_primary.desc(),
            )
        )
        for pm in pm_res.scalars().all():
            if pm.customer_id not in pm_map:
                pm_map[pm.customer_id] = pm.to_dict()

    items = []
    for row in raw_rows:
        cust = row[0]
        risk = float(cust.risk_score or 0)
        primary_pm = pm_map.get(cust.id)

        # Build payment_methods summary label
        payment_type = primary_pm["payment_type"] if primary_pm else None
        payment_label = primary_pm["display_label"] if primary_pm else None

        items.append(
            {
                "customer_id": cust.id,
                "full_name": cust.full_name,
                "email": cust.email,
                "phone_number": cust.phone_number,
                "city": cust.city,
                "account_type": cust.account_type,
                "kyc_status": cust.kyc_status,
                "customer_tier": cust.customer_tier,
                "risk_score": round(risk, 4),
                "risk_level": _risk_level(risk),
                "risk_color": _risk_color(risk),
                "balance_amount": float(cust.balance_amount or 0),
                "transaction_count": int(row[1]),
                "fraud_flags": int(row[2]),
                "open_alerts": int(row[3]),
                "created_at": cust.created_at.isoformat() if cust.created_at else None,
                # Payment method info
                "primary_payment_type": payment_type,
                "primary_payment_label": payment_label,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page else 1,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _risk_level(score: float) -> str:
    if score < 0.20:
        return "low"
    if score < 0.40:
        return "guarded"
    if score < 0.60:
        return "medium"
    if score < 0.80:
        return "high"
    return "critical"


def _risk_color(score: float) -> str:
    if score < 0.20:
        return "#22C55E"
    if score < 0.40:
        return "#84CC16"
    if score < 0.60:
        return "#EAB308"
    if score < 0.80:
        return "#F97316"
    return "#EF4444"
