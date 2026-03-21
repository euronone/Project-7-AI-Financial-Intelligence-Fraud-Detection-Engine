from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SystemSettings(BaseModel):
    app_name: str = "FinShield AI"
    app_env: str = "development"
    fraud_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    auto_block_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    alert_retention_days: int = Field(default=90, ge=1)
    max_batch_size: int = Field(default=1000, ge=1)
    enable_real_time: bool = True
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False


class SystemSettingsUpdate(BaseModel):
    app_name: str | None = None
    app_env: str | None = None
    fraud_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_block_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    alert_retention_days: int | None = Field(default=None, ge=1)
    max_batch_size: int | None = Field(default=None, ge=1)
    enable_real_time: bool | None = None
    enable_email_notifications: bool | None = None
    enable_sms_notifications: bool | None = None


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    last_login_at: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> str:
        return str(v)

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    @field_validator("last_login_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str | None:
        if v is None:
            return None
        return str(v) if not isinstance(v, str) else v


class TeamListResponse(BaseModel):
    members: list[TeamMember]
    total: int


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    expires_in_days: int = Field(default=90, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: str
    expires_at: str
    is_active: bool


class ApiKeyFullResponse(ApiKeyResponse):
    api_key: str
