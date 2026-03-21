import math
import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate

logger = structlog.get_logger()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", str(user_id))
    return user


async def list_users(
    db: AsyncSession, *, page: int = 1, page_size: int = 25
) -> UserListResponse:
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[UserResponse.model_validate(u) for u in users],
    )


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError(f"User with email '{data.email}' already exists")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    logger.info("user_created", user_id=str(user.id), email=user.email, role=user.role.value)
    return user


async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = await get_user_by_id(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    logger.info("user_updated", user_id=str(user.id), fields=list(update_data.keys()))
    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_user_by_id(db, user_id)
    user.is_active = False
    await db.flush()
    logger.info("user_deactivated", user_id=str(user.id))
    return user
