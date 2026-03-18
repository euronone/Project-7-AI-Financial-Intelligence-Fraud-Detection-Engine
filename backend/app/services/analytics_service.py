from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.entity import Entity
from app.models.fraud_alert import FraudAlert
from app.models.ml_model import MLModel, ModelStatus
from app.models.rule import Rule
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.analytics import (
    FraudTrendPoint,
    FraudTrendsResponse,
    GeoDataPoint,
    GeoResponse,
    ModelPerformancePoint,
    ModelPerformanceResponse,
    OverviewStats,
    ReportRequest,
    ReportResponse,
    RiskDistributionResponse,
    TopPattern,
    TopPatternsResponse,
    TransactionVolumePoint,
    TransactionVolumeResponse,
)

logger = structlog.get_logger()

_PERIOD_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


def _period_start(period: str) -> datetime:
    days = _PERIOD_DAYS.get(period, 30)
    return datetime.now(timezone.utc) - timedelta(days=days)


async def get_overview_stats(db: AsyncSession) -> OverviewStats:
    """Aggregate high-level counts across core tables."""
    total_tx = (
        await db.execute(select(func.count()).select_from(Transaction))
    ).scalar() or 0

    total_alerts = (
        await db.execute(select(func.count()).select_from(FraudAlert))
    ).scalar() or 0

    total_cases = (
        await db.execute(select(func.count()).select_from(Case))
    ).scalar() or 0

    total_entities = (
        await db.execute(select(func.count()).select_from(Entity))
    ).scalar() or 0

    active_rules = (
        await db.execute(
            select(func.count()).select_from(Rule).where(Rule.is_active.is_(True))
        )
    ).scalar() or 0

    flagged_or_fraud = (
        await db.execute(
            select(func.count())
            .select_from(Transaction)
            .where(
                Transaction.status.in_([
                    TransactionStatus.FLAGGED,
                    TransactionStatus.BLOCKED,
                ])
            )
        )
    ).scalar() or 0

    fraud_rate = (flagged_or_fraud / total_tx) if total_tx > 0 else 0.0

    total_amount = (
        await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)))
    ).scalar() or 0.0

    avg_risk = (
        await db.execute(
            select(func.coalesce(func.avg(Entity.risk_score), 0))
        )
    ).scalar() or 0.0

    logger.info("overview_stats_fetched", total_transactions=total_tx)

    return OverviewStats(
        total_transactions=total_tx,
        total_alerts=total_alerts,
        total_cases=total_cases,
        total_entities=total_entities,
        fraud_rate=round(float(fraud_rate), 6),
        avg_risk_score=round(float(avg_risk), 4),
        total_amount_processed=float(total_amount),
        active_rules=active_rules,
    )


async def get_fraud_trends(
    db: AsyncSession, period: str = "30d"
) -> FraudTrendsResponse:
    """Group fraud alerts by day for the requested period. Falls back to flagged transactions if no alerts."""
    start = _period_start(period)

    date_col = func.date_trunc("day", FraudAlert.created_at).label("day")
    stmt = (
        select(
            date_col,
            func.count().label("cnt"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.coalesce(func.avg(FraudAlert.confidence_score), 0).label("avg_conf"),
        )
        .join(Transaction, FraudAlert.transaction_id == Transaction.id)
        .where(FraudAlert.created_at >= start)
        .group_by(date_col)
        .order_by(date_col)
    )

    rows = (await db.execute(stmt)).all()
    data_points = [
        FraudTrendPoint(
            date=row.day.strftime("%Y-%m-%d"),
            count=row.cnt,
            amount=float(row.total_amount),
            avg_score=round(float(row.avg_conf), 4),
        )
        for row in rows
    ]

    # Fallback: if no alert-based trends, use flagged transactions by day
    if not data_points:
        tx_date_col = func.date_trunc("day", Transaction.processed_at).label("day")
        tx_stmt = (
            select(
                tx_date_col,
                func.count().label("cnt"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
                func.coalesce(func.avg(Transaction.fraud_score), 0).label("avg_conf"),
            )
            .where(
                Transaction.processed_at >= start,
                Transaction.status.in_([TransactionStatus.FLAGGED, TransactionStatus.BLOCKED]),
            )
            .group_by(tx_date_col)
            .order_by(tx_date_col)
        )
        tx_rows = (await db.execute(tx_stmt)).all()
        data_points = [
            FraudTrendPoint(
                date=row.day.strftime("%Y-%m-%d"),
                count=row.cnt,
                amount=float(row.total_amount),
                avg_score=round(float(row.avg_conf or 0), 4),
            )
            for row in tx_rows
        ]

    return FraudTrendsResponse(period=period, data_points=data_points)


async def get_transaction_volume(
    db: AsyncSession, period: str = "30d"
) -> TransactionVolumeResponse:
    """Group transactions by day with per-channel breakdown."""
    start = _period_start(period)

    date_col = func.date_trunc("day", Transaction.processed_at).label("day")
    stmt = (
        select(
            date_col,
            func.count().label("cnt"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(Transaction.processed_at >= start)
        .group_by(date_col)
        .order_by(date_col)
    )
    daily_rows = (await db.execute(stmt)).all()

    channel_stmt = (
        select(
            date_col,
            Transaction.channel,
            func.count().label("cnt"),
        )
        .where(Transaction.processed_at >= start)
        .group_by(date_col, Transaction.channel)
    )
    channel_rows = (await db.execute(channel_stmt)).all()

    channel_map: dict[str, dict[str, int]] = {}
    for row in channel_rows:
        day_key = row.day.strftime("%Y-%m-%d")
        channel_map.setdefault(day_key, {})[row.channel.value if hasattr(row.channel, "value") else str(row.channel)] = row.cnt

    data_points = [
        TransactionVolumePoint(
            date=row.day.strftime("%Y-%m-%d"),
            count=row.cnt,
            amount=float(row.total_amount),
            by_channel=channel_map.get(row.day.strftime("%Y-%m-%d"), {}),
        )
        for row in daily_rows
    ]

    return TransactionVolumeResponse(period=period, data_points=data_points)


async def get_risk_distribution(db: AsyncSession) -> RiskDistributionResponse:
    """Count entities by risk_level bucket."""
    stmt = select(Entity.risk_level, func.count().label("cnt")).group_by(
        Entity.risk_level
    )
    rows = (await db.execute(stmt)).all()

    dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for row in rows:
        level = row.risk_level.value if hasattr(row.risk_level, "value") else str(row.risk_level)
        if level in dist:
            dist[level] = row.cnt

    total = sum(dist.values())
    return RiskDistributionResponse(**dist, total=total)


async def get_top_patterns(db: AsyncSession) -> TopPatternsResponse:
    """Aggregate rule hit counts by category and compute percentages."""
    stmt = (
        select(
            Rule.category,
            func.sum(Rule.hit_count).label("total_hits"),
        )
        .where(Rule.is_active.is_(True))
        .group_by(Rule.category)
        .order_by(func.sum(Rule.hit_count).desc())
    )
    rows = (await db.execute(stmt)).all()

    grand_total = sum(row.total_hits for row in rows) or 1

    patterns = [
        TopPattern(
            pattern_name=row.category.value if hasattr(row.category, "value") else str(row.category),
            count=int(row.total_hits),
            percentage=round(float(row.total_hits) / grand_total * 100, 2),
            trend="stable",
        )
        for row in rows
    ]

    return TopPatternsResponse(patterns=patterns)


async def get_geo_data(db: AsyncSession) -> GeoResponse:
    """Group transactions by country_code, counting fraud per country."""
    fraud_case = case(
        (
            Transaction.status.in_([
                TransactionStatus.FLAGGED,
                TransactionStatus.BLOCKED,
            ]),
            1,
        ),
        else_=0,
    )

    stmt = (
        select(
            Transaction.country_code,
            func.count().label("cnt"),
            func.sum(fraud_case).label("fraud_cnt"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(Transaction.country_code.isnot(None))
        .group_by(Transaction.country_code)
        .order_by(func.count().desc())
    )
    rows = (await db.execute(stmt)).all()

    data = [
        GeoDataPoint(
            country_code=row.country_code,
            count=row.cnt,
            fraud_count=int(row.fraud_cnt),
            total_amount=float(row.total_amount),
            fraud_rate=round(float(row.fraud_cnt) / row.cnt, 6) if row.cnt > 0 else 0.0,
        )
        for row in rows
    ]

    return GeoResponse(data=data)


async def get_model_performance(db: AsyncSession) -> ModelPerformanceResponse:
    """Query ML models with active or training status and extract stored metrics."""
    stmt = (
        select(MLModel)
        .where(MLModel.status.in_([ModelStatus.ACTIVE, ModelStatus.TRAINING, ModelStatus.VALIDATING]))
        .order_by(MLModel.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    points = []
    for m in rows:
        metrics: dict = m.metrics or {}
        points.append(
            ModelPerformancePoint(
                model_name=m.name,
                model_type=m.model_type.value if hasattr(m.model_type, "value") else str(m.model_type),
                accuracy=float(metrics.get("accuracy", 0)),
                precision=float(metrics.get("precision", 0)),
                recall=float(metrics.get("recall", 0)),
                f1=float(metrics.get("f1", 0)),
                auc_roc=float(metrics.get("auc_roc", 0)),
            )
        )

    return ModelPerformanceResponse(models=points)


async def generate_report(
    db: AsyncSession, request: ReportRequest
) -> ReportResponse:
    """Create a report record and return a processing handle.

    Full report generation would be offloaded to a Celery task;
    this returns the initial tracking record.
    """
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    logger.info(
        "report_requested",
        report_id=report_id,
        report_type=request.report_type,
    )

    return ReportResponse(
        report_id=report_id,
        status="processing",
        download_url=None,
        created_at=now,
    )
