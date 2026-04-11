"""Pydantic schemas for the BYOK Credentials Manager."""
from datetime import datetime
from pydantic import BaseModel, Field


class CredentialUpsert(BaseModel):
    """Request body to create or update a credential."""

    service: str = Field(..., min_length=1, max_length=64, examples=["resend"])
    key_name: str = Field(..., min_length=1, max_length=128, examples=["resend_api_key"])
    value: str = Field(..., min_length=1, description="Plaintext secret — encrypted before storage")
    label: str | None = Field(None, max_length=255, examples=["Production API Key"])


class CredentialOut(BaseModel):
    """Credential returned to the frontend — value is always masked."""

    id: str
    service: str
    key_name: str
    label: str | None
    masked_value: str = Field(description="Always '••••••••' + last 4 chars of the plaintext")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialTestResult(BaseModel):
    """Result of a live connection test for a given service credential."""

    service: str
    key_name: str
    success: bool
    message: str
    latency_ms: int | None = None


class CredentialDeleteResponse(BaseModel):
    deleted: bool
    id: str
