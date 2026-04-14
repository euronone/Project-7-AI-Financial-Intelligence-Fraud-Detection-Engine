"""Auth request/response schemas."""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Literal, Optional


class SignupRequest(BaseModel):
    # str instead of EmailStr — allows .local / internal domains used in demo accounts
    email: str
    password: str
    full_name: str
    phone_number: str | None = None
    institution_name: str
    institution_type: Literal["bank", "fintech", "insurance", "payment_processor", "neobank"] = (
        "bank"
    )
    subscription_plan: Literal["free", "pro", "advanced"] = "free"
    country_code: str = "IN"
    supabase_uid: str | None = None  # Provided when signup goes through Supabase auth
    # Role selection: "admin" creates institution owner, "user" creates analyst member
    signup_role: Literal["admin", "user"] = "admin"

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


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    uid: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class AdminSetPasswordRequest(BaseModel):
    user_id: str
    new_password: str
    force_reset: bool = False  # If True, user must change password on next login

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Temporary password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    role: str
    institution_name: str
    institution_type: str
    plan: str
    has_completed_onboarding: bool
    avatar_initials: str
    is_active: bool
    must_change_password: bool

    @classmethod
    def from_user(cls, user, tenant) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role,
            institution_name=tenant.organization_name if tenant else "",
            institution_type=tenant.institution_type if tenant else "bank",
            plan=tenant.subscription_plan if tenant else "free",
            has_completed_onboarding=user.has_completed_onboarding,
            avatar_initials=(user.full_name or user.email)[:2].upper(),
            is_active=user.is_active,
            must_change_password=getattr(user, "must_change_password", False),
        )
