"""Auth request/response schemas."""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Literal


class SignupRequest(BaseModel):
    # str instead of EmailStr — allows .local / internal domains used in demo accounts
    email: str
    password: str
    full_name: str
    phone_number: str | None = None
    institution_name: str
    institution_type: Literal["bank", "fintech", "insurance", "payment_processor", "neobank"] = "bank"
    subscription_plan: Literal["free", "pro", "advanced"] = "free"
    country_code: str = "IN"
    supabase_uid: str | None = None  # Provided when signup goes through Supabase auth

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    institution_name: str
    institution_type: str
    plan: str
    has_completed_onboarding: bool
    avatar_initials: str

    @classmethod
    def from_user(cls, user, tenant) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            institution_name=tenant.organization_name if tenant else "",
            institution_type=tenant.institution_type if tenant else "bank",
            plan=tenant.subscription_plan if tenant else "free",
            has_completed_onboarding=user.has_completed_onboarding,
            avatar_initials=(user.full_name or user.email)[:2].upper(),
        )
