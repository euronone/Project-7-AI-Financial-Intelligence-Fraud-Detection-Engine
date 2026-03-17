import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    details: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("ip_address", mode="before")
    @classmethod
    def coerce_ip(cls, v):
        return str(v) if v is not None else v


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[AuditLogResponse]


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool
    metadata_: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    total: int
    unread: int
    items: list[NotificationResponse]
