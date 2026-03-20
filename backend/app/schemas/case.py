import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.case import CasePriority, CaseStatus


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    priority: CasePriority = CasePriority.MEDIUM
    alert_ids: list[uuid.UUID] | None = None
    assigned_to: uuid.UUID | None = None


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    priority: CasePriority | None = None
    findings: str | None = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    case_number: str
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    assigned_to: uuid.UUID | None
    total_amount_at_risk: Decimal | None
    alert_ids: list[uuid.UUID] | None
    timeline: dict | None
    findings: str | None
    created_by: uuid.UUID
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[CaseResponse]


class CaseStatusUpdate(BaseModel):
    status: CaseStatus
    notes: str | None = None


class CaseAssign(BaseModel):
    assigned_to: uuid.UUID


class CaseStatistics(BaseModel):
    total: int
    open: int
    in_progress: int
    pending_review: int
    escalated: int
    closed_confirmed_fraud: int
    closed_false_positive: int
    by_priority: dict[str, int]
