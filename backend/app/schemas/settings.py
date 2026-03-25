"""Settings schemas."""
from pydantic import BaseModel
from typing import Literal


class DbConnectionRequest(BaseModel):
    db_type: Literal["supabase", "postgresql", "mysql", "mongodb", "rest_api"]
    label: str | None = None
    db_url: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    api_key: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_key: str | None = None


class DbConnectionResponse(BaseModel):
    db_type: str
    label: str | None
    is_connected: bool
    message: str


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float | None = None
