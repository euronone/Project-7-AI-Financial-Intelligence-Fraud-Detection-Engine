"""Fraud alert schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    transaction_id: str
    customer_id: str | None
    alert_type: str
    severity: str
    status: str
    is_confirmed: bool
    created_at: datetime
    resolved_at: datetime | None


class AlertUpdateRequest(BaseModel):
    status: str  # open|under_review|confirmed_fraud|false_positive|closed
    resolution_notes: str | None = None


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    per_page: int
