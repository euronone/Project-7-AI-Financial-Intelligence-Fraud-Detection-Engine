import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.rule import RuleCategory, RuleSeverity


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: RuleCategory
    conditions: dict = Field(default_factory=dict)
    actions: dict = Field(default_factory=dict)
    severity: RuleSeverity = RuleSeverity.MEDIUM
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = True


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: RuleCategory | None = None
    conditions: dict | None = None
    actions: dict | None = None
    severity: RuleSeverity | None = None
    priority: int | None = Field(default=None, ge=1, le=1000)


class RuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: RuleCategory
    conditions: dict
    actions: dict
    severity: RuleSeverity
    is_active: bool
    priority: int
    hit_count: int
    false_positive_rate: Decimal | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[RuleResponse]


class RuleToggleRequest(BaseModel):
    is_active: bool


class RuleTestRequest(BaseModel):
    """Sample transaction data to test a rule against."""
    transaction: dict


class RuleTestResult(BaseModel):
    rule_id: str
    rule_name: str
    matched: bool
    severity: str
    priority: int
    conditions: list[dict]
    actions: list[dict]


class RulePerformance(BaseModel):
    rule_id: str
    rule_name: str
    hit_count: int
    false_positive_rate: float | None
    is_active: bool
    severity: str
