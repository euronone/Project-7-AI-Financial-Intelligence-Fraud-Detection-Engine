import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(min_length=12)


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[UserResponse]
