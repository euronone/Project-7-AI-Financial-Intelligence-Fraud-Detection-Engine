"""Authentication business logic — login, token refresh, current user."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginResponse, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── public methods ──────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> LoginResponse:
        user = await self._get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("Account is disabled")

        user.last_login_at = datetime.now(timezone.utc)
        await self._db.commit()

        return LoginResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            refresh_token=create_refresh_token(str(user.id)),
            user=UserResponse.from_orm_user(user),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user = await self._get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or disabled")

        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value)
        )

    async def get_current_user(self, access_token: str) -> User:
        payload = decode_token(access_token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")

        user = await self._get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or disabled")
        return user

    # ── private helpers ─────────────────────────────────────────────────────

    async def _get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_by_id(self, user_id: str) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
