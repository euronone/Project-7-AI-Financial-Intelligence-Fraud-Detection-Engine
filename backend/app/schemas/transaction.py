import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionChannel, TransactionStatus, TransactionType


class TransactionFilters(BaseModel):
    status: TransactionStatus | None = None
    transaction_type: TransactionType | None = None
    channel: TransactionChannel | None = None
    risk_level: str | None = None
    currency: str | None = None
    country_code: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    source_entity_id: uuid.UUID | None = None
    search: str | None = None


class TransactionCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=255)
    source_entity_id: uuid.UUID
    destination_entity_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    transaction_type: TransactionType
    channel: TransactionChannel
    merchant_category_code: str | None = Field(default=None, max_length=4)
    description: str | None = None
    ip_address: str | None = None
    device_fingerprint: str | None = None
    country_code: str | None = Field(default=None, max_length=2)
    card_present: bool | None = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    source_entity_id: uuid.UUID
    destination_entity_id: uuid.UUID | None
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    channel: TransactionChannel
    status: TransactionStatus
    merchant_category_code: str | None
    description: str | None
    ip_address: str | None
    country_code: str | None
    card_present: bool | None
    fraud_score: Decimal | None
    risk_level: str | None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("ip_address", mode="before")
    @classmethod
    def coerce_ip_to_str(cls, v):
        return str(v) if v is not None else v


class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[TransactionResponse]
