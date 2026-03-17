import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.dependencies import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services import audit_service, user_service

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserListResponse:
    """List all users (admin only)."""
    return await user_service.list_users(db, page=page, page_size=page_size)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:
    """Create a new user (admin only)."""
    user = await user_service.create_user(db, data)
    await audit_service.log_action(
        db,
        user_id=admin.id,
        action="create_user",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "role": user.role.value},
    )
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:
    """Update a user's details (admin only)."""
    user = await user_service.update_user(db, user_id, data)
    await audit_service.log_action(
        db,
        user_id=admin.id,
        action="update_user",
        resource_type="user",
        resource_id=user.id,
    )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> MessageResponse:
    """Deactivate a user (soft delete, admin only)."""
    user = await user_service.deactivate_user(db, user_id)
    await audit_service.log_action(
        db,
        user_id=admin.id,
        action="deactivate_user",
        resource_type="user",
        resource_id=user.id,
    )
    return MessageResponse(message=f"User {user.email} deactivated")
