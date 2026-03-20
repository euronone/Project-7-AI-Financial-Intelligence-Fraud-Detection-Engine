import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse

logger = structlog.get_logger()


async def register_user(db: AsyncSession, data: SignupRequest) -> TokenResponse:
    """Registers a new user and returns access + refresh tokens."""
    settings = get_settings()
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise BadRequestException("Email already registered")

    try:
        role = UserRole(data.role.lower())
    except ValueError:
        role = UserRole.VIEWER

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    token_data = {"sub": str(user.id), "role": user.role.value, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("user_registered", user_id=str(user.id), role=user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


async def authenticate_user(db: AsyncSession, credentials: LoginRequest) -> TokenResponse:
    """Validates credentials and returns access + refresh tokens."""
    settings = get_settings()
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(credentials.password, user.password_hash):
        logger.warning("auth_failed", email=credentials.email)
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    token_data = {"sub": str(user.id), "role": user.role.value, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("auth_success", user_id=str(user.id), role=user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


async def refresh_access_token(db: AsyncSession, request: RefreshRequest) -> TokenResponse:
    """Validates a refresh token and issues a new access token pair."""
    settings = get_settings()
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise BadRequestException("Invalid token type — expected refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token missing subject")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or deactivated")

    token_data = {"sub": str(user.id), "role": user.role.value, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
