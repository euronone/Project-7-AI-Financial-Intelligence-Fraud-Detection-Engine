import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.fraud_alert import AlertSeverity, AlertStatus, AlertType


class AlertCreate(BaseModel):
    transaction_id: uuid.UUID
    entity_id: uuid.UUID | None = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    confidence_score: float | None = None
    rule_id: uuid.UUID | None = None
    model_id: uuid.UUID | None = None
    evidence: dict | None = None


class AlertResponse(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    entity_id: uuid.UUID | None
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    confidence_score: Decimal | None
    rule_id: uuid.UUID | None
    model_id: uuid.UUID | None
    evidence: dict | None
    assigned_to: uuid.UUID | None
    resolved_by: uuid.UUID | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[AlertResponse]


class AlertStatusUpdate(BaseModel):
    status: AlertStatus
    resolution_notes: str | None = None


class AlertAssign(BaseModel):
    assigned_to: uuid.UUID


class AlertStatistics(BaseModel):
    total: int
    open: int
    investigating: int
    escalated: int
    resolved_fraud: int
    resolved_false_positive: int
    dismissed: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
