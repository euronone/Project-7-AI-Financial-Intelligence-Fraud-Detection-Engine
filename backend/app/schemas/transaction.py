"""Transaction schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    customer_id: str | None = None
    amount: float
    currency: str = "INR"
    transaction_type: str = "purchase"
    channel: str = "online"
    merchant_name: str | None = None
    merchant_category_code: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    country_code: str | None = None
    city: str | None = None
    ip_address: str | None = None
    device_fingerprint: str | None = None
    device_type: str | None = None
    transaction_timestamp: datetime | None = None
    is_test: bool = False


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str | None
    amount: float
    currency: str
    transaction_type: str
    channel: str
    merchant_name: str | None
    status: str
    fraud_score: float | None
    fraud_risk_level: str | None
    fraud_category: str
    is_flagged: bool
    is_blocked: bool
    is_test: bool
    triggered_rule_ids: list | None
    transaction_timestamp: datetime
    created_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    per_page: int
