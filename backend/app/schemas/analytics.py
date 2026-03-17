from __future__ import annotations

from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    total_transactions: int = 0
    total_alerts: int = 0
    total_cases: int = 0
    total_entities: int = 0
    fraud_rate: float = 0.0
    avg_risk_score: float = 0.0
    total_amount_processed: float = 0.0
    active_rules: int = 0


class FraudTrendPoint(BaseModel):
    date: str
    count: int
    amount: float
    avg_score: float


class FraudTrendsResponse(BaseModel):
    period: str
    data_points: list[FraudTrendPoint]


class TransactionVolumePoint(BaseModel):
    date: str
    count: int
    amount: float
    by_channel: dict[str, int] = Field(default_factory=dict)


class TransactionVolumeResponse(BaseModel):
    period: str
    data_points: list[TransactionVolumePoint]


class RiskDistributionResponse(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    total: int = 0


class TopPattern(BaseModel):
    pattern_name: str
    count: int
    percentage: float
    trend: str = "stable"


class TopPatternsResponse(BaseModel):
    patterns: list[TopPattern]


class GeoDataPoint(BaseModel):
    country_code: str
    count: int
    fraud_count: int
    total_amount: float
    fraud_rate: float


class GeoResponse(BaseModel):
    data: list[GeoDataPoint]


class ModelPerformancePoint(BaseModel):
    model_name: str
    model_type: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    auc_roc: float = 0.0


class ModelPerformanceResponse(BaseModel):
    models: list[ModelPerformancePoint]


class ReportRequest(BaseModel):
    report_type: str
    date_from: str | None = None
    date_to: str | None = None
    filters: dict | None = None


class ReportResponse(BaseModel):
    report_id: str
    status: str
    download_url: str | None = None
    created_at: str
