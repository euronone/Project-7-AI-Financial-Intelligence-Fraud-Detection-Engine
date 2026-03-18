"""Pydantic v2 schemas for the Transaction resource.

Covers:
- TransactionCreate — single ingest request body
- BatchIngestRequest — batch ingest (up to 10,000)
- TransactionResponse — standard list/search item
- TransactionDetail — full detail with fraud analysis
- TransactionSearchRequest — advanced search body
- TransactionExportParams — query params for export
- FraudScoreBreakdown — component scores returned with each transaction
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.transaction import (
    TransactionChannel,
    TransactionRiskLevel,
    TransactionStatus,
    TransactionType,
)


# ── Fraud pipeline output ─────────────────────────────────────────────────────

class FraudScoreBreakdown(BaseModel):
    """Component scores from the fraud detection pipeline."""

    ml_score: float = Field(ge=0.0, le=1.0)
    anomaly_score: float = Field(ge=0.0, le=1.0)
    behavioral_score: float = Field(ge=0.0, le=1.0)
    network_score: float = Field(ge=0.0, le=1.0)
    rule_score: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    decision: str  # PASS | FLAG | ALERT | BLOCK
    triggered_rules: List[str] = Field(default_factory=list)
    top_features: List[Dict[str, Any]] = Field(default_factory=list)


# ── Entity summary (embedded in transaction responses) ────────────────────────

class EntitySummary(BaseModel):
    """Lightweight entity info embedded in transaction responses."""

    id: uuid.UUID
    name: str
    entity_type: str
    risk_score: Decimal
    risk_level: str
    is_watchlisted: bool

    model_config = {"from_attributes": True}


# ── Ingest ────────────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    """Request body for POST /transactions — single transaction ingest."""

    external_id: str = Field(
        max_length=255,
        description="Unique identifier from the originating system.",
    )
    source_entity_id: uuid.UUID = Field(
        description="UUID of the sending entity (must already exist)."
    )
    destination_entity_id: Optional[uuid.UUID] = Field(
        default=None,
        description="UUID of the receiving entity.",
    )
    amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=4,
        description="Transaction amount (positive).",
    )
    currency: str = Field(
        min_length=3, max_length=3,
        description="ISO 4217 currency code.",
    )
    transaction_type: TransactionType
    channel: TransactionChannel
    status: TransactionStatus = Field(default=TransactionStatus.pending)
    merchant_category_code: Optional[str] = Field(
        default=None, max_length=4
    )
    description: Optional[str] = None
    ip_address: Optional[str] = Field(
        default=None,
        description="IPv4 or IPv6 address of the originating device.",
    )
    device_fingerprint: Optional[str] = Field(default=None, max_length=255)
    geolocation_lat: Optional[Decimal] = Field(
        default=None, ge=-90, le=90
    )
    geolocation_lng: Optional[Decimal] = Field(
        default=None, ge=-180, le=180
    )
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    card_present: Optional[bool] = None
    processed_at: datetime = Field(
        description="Transaction timestamp (UTC)."
    )

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()


class BatchIngestRequest(BaseModel):
    """Request body for POST /transactions/batch."""

    transactions: List[TransactionCreate] = Field(
        min_length=1,
        description="List of transactions to ingest (max 10,000).",
    )

    @model_validator(mode="after")
    def check_batch_size(self) -> "BatchIngestRequest":
        from app.config import get_settings
        limit = get_settings().batch_ingest_max_size
        if len(self.transactions) > limit:
            raise ValueError(
                f"Batch size {len(self.transactions)} exceeds maximum of {limit}."
            )
        return self


# ── Responses ─────────────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    """Transaction item returned in list and search endpoints."""

    id: uuid.UUID
    external_id: str
    source_entity_id: uuid.UUID
    destination_entity_id: Optional[uuid.UUID]
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    channel: TransactionChannel
    status: TransactionStatus
    fraud_score: Optional[Decimal]
    risk_level: Optional[TransactionRiskLevel]
    country_code: Optional[str]
    processed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionDetail(TransactionResponse):
    """Full transaction detail with fraud analysis and entity context."""

    merchant_category_code: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    device_fingerprint: Optional[str]
    geolocation_lat: Optional[Decimal]
    geolocation_lng: Optional[Decimal]
    card_present: Optional[bool]

    fraud_score_breakdown: Optional[FraudScoreBreakdown] = None
    source_entity: Optional[EntitySummary] = None
    destination_entity: Optional[EntitySummary] = None
    alert_count: int = 0

    model_config = {"from_attributes": True}


class BatchIngestResponse(BaseModel):
    """Response for POST /transactions/batch."""

    accepted: int
    rejected: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID for large batches processed asynchronously.",
    )


# ── Search ────────────────────────────────────────────────────────────────────

class TransactionSearchRequest(BaseModel):
    """Advanced search body for POST /transactions/search."""

    query: Optional[str] = Field(
        default=None,
        description="Full-text search across external_id and description.",
    )
    status: Optional[List[TransactionStatus]] = None
    risk_level: Optional[List[TransactionRiskLevel]] = None
    transaction_type: Optional[List[TransactionType]] = None
    channel: Optional[List[TransactionChannel]] = None
    min_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_amount: Optional[Decimal] = Field(default=None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    entity_id: Optional[uuid.UUID] = None
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    min_fraud_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_fraud_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sort_by: str = Field(default="processed_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


# ── Export ────────────────────────────────────────────────────────────────────

class ExportFormat(str):
    CSV = "csv"
    JSON = "json"
