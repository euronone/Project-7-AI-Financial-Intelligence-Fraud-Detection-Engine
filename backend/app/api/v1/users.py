"""
Admin user management endpoints.
All routes require admin role and enforce tenant isolation.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Literal, List, Optional
import uuid

from app.db.session import get_db
from app.models.user import User, Tenant
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.dependencies import AdminUser, CurrentUser
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["User Management"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    phone_number: Optional[str] = None
    role: Literal["admin", "analyst", "viewer"] = "analyst"
    temp_password: str = "ChangeMe123!"
    force_reset: bool = True  # User must change password on first login


class UpdateRoleRequest(BaseModel):
    role: Literal["admin", "analyst", "viewer"]


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: Optional[str]
    created_at: str


# ---------------------------------------------------------------------------
# GET /users  — list all users in tenant
# ---------------------------------------------------------------------------


@router.get("", response_model=List[UserListItem])
async def list_users(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """List all users within the admin's tenant."""
    result = await db.execute(
        select(User).where(User.tenant_id == admin.tenant_id).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        UserListItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            phone_number=u.phone_number,
            role=u.role,
            is_active=u.is_active,
            must_change_password=getattr(u, "must_change_password", False),
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# POST /users  — admin creates a new user with a temp password
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a new user in the same tenant with a temporary password."""
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=admin.tenant_id,
        email=body.email,
        full_name=body.full_name,
        phone_number=body.phone_number,
        hashed_password=hash_password(body.temp_password),
        role=body.role,
        is_active=True,
        is_verified=True,
        must_change_password=body.force_reset,
    )
    db.add(user)
    await db.commit()

    return {
        "message": "User created",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "must_change_password": body.force_reset,
    }


# ---------------------------------------------------------------------------
# PUT /users/{user_id}/role  — change a user's role
# ---------------------------------------------------------------------------


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: UpdateRoleRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin changes another user's role within the same tenant."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == admin.tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User")

    # Prevent demoting yourself
    if user.id == admin.id:
        raise ForbiddenException("Cannot change your own role")

    user.role = body.role
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Role updated", "user_id": user.id, "new_role": user.role}


# ---------------------------------------------------------------------------
# POST /users/{user_id}/freeze  — freeze or unfreeze an account
# ---------------------------------------------------------------------------


@router.post("/{user_id}/freeze")
async def freeze_user(
    user_id: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin freezes a user account (blocks login). Toggle — call again to unfreeze."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == admin.tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User")

    if user.id == admin.id:
        raise ForbiddenException("Cannot freeze your own account")

    user.is_active = not user.is_active
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    status = "frozen" if not user.is_active else "activated"
    return {"message": f"Account {status}", "user_id": user.id, "is_active": user.is_active}


# ---------------------------------------------------------------------------
# POST /users/{user_id}/force-reset  — force password reset on next login
# ---------------------------------------------------------------------------


@router.post("/{user_id}/force-reset")
async def force_password_reset(
    user_id: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin marks a user account to require a password change on next login."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == admin.tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User")

    user.must_change_password = True
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Password reset required on next login", "user_id": user.id}


# ---------------------------------------------------------------------------
# GET /users/me  — current user's own profile (any role)
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return current user's full profile."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return UserResponse.from_user(current_user, tenant)
