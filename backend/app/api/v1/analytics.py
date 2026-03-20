from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.analytics import (
    FraudTrendsResponse,
    GeoResponse,
    ModelPerformanceResponse,
    OverviewStats,
    ReportRequest,
    ReportResponse,
    RiskDistributionResponse,
    TopPatternsResponse,
    TransactionVolumeResponse,
)
from app.services import analytics_service

logger = structlog.get_logger()

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
async def overview(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> OverviewStats:
    return await analytics_service.get_overview_stats(db)


@router.get("/fraud-trends", response_model=FraudTrendsResponse)
async def fraud_trends(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> FraudTrendsResponse:
    return await analytics_service.get_fraud_trends(db, period=period)


@router.get("/transaction-volume", response_model=TransactionVolumeResponse)
async def transaction_volume(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> TransactionVolumeResponse:
    return await analytics_service.get_transaction_volume(db, period=period)


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
async def risk_distribution(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RiskDistributionResponse:
    return await analytics_service.get_risk_distribution(db)


@router.get("/top-patterns", response_model=TopPatternsResponse)
async def top_patterns(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> TopPatternsResponse:
    return await analytics_service.get_top_patterns(db)


@router.get("/geographic", response_model=GeoResponse)
async def geographic(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> GeoResponse:
    return await analytics_service.get_geo_data(db)


@router.get("/model-performance", response_model=ModelPerformanceResponse)
async def model_performance(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> ModelPerformanceResponse:
    return await analytics_service.get_model_performance(db)


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def create_report(
    body: ReportRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> ReportResponse:
    return await analytics_service.generate_report(db, body)
