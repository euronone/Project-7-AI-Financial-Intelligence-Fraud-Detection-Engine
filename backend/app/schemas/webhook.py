from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

VALID_WEBHOOK_EVENTS = frozenset({
    "alert.created",
    "alert.updated",
    "case.created",
    "case.updated",
    "transaction.flagged",
    "risk.scored",
})


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    events: list[str] = Field(min_length=1)
    secret: str = Field(min_length=16, max_length=255)

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_WEBHOOK_EVENTS
        if invalid:
            raise ValueError(f"Invalid event types: {', '.join(sorted(invalid))}")
        return v


class WebhookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    events: list[str] | None = None
    is_active: bool | None = None

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        invalid = set(v) - VALID_WEBHOOK_EVENTS
        if invalid:
            raise ValueError(f"Invalid event types: {', '.join(sorted(invalid))}")
        return v


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: str | None
    failure_count: int
    created_at: str
    updated_at: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> str:
        return str(v)

    @field_validator("last_triggered_at", "created_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str | None:
        if v is None:
            return None
        return str(v) if not isinstance(v, str) else v


class WebhookListResponse(BaseModel):
    items: list[WebhookResponse]
    total: int


class WebhookTestRequest(BaseModel):
    event_type: str
    sample_data: dict | None = None


class WebhookTestResponse(BaseModel):
    success: bool
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str | None = None
