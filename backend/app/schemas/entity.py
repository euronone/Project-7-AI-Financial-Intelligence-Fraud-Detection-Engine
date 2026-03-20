import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.entity import EntityType, KYCStatus, RiskLevel


class EntityFilters(BaseModel):
    entity_type: EntityType | None = None
    risk_level: RiskLevel | None = None
    kyc_status: KYCStatus | None = None
    country_code: str | None = None
    is_watchlisted: bool | None = None
    search: str | None = None


class EntityCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=255)
    entity_type: EntityType
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    country_code: str | None = Field(default=None, max_length=2)


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    country_code: str | None = Field(default=None, max_length=2)
    kyc_status: KYCStatus | None = None


class EntityResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    entity_type: EntityType
    name: str
    email: str | None
    phone: str | None
    country_code: str | None
    risk_score: Decimal
    risk_level: RiskLevel
    is_watchlisted: bool
    kyc_status: KYCStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[EntityResponse]


class EntityDetailResponse(EntityResponse):
    """Extended entity response with aggregated stats for the Entity 360 view."""
    transaction_count: int = 0
    total_transaction_amount: Decimal = Decimal("0")
    alert_count: int = 0
    open_case_count: int = 0
