import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user
from app.core.rate_limiter import rate_limit_auth
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services import audit_service, auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password, returns JWT tokens."""
    tokens = await auth_service.authenticate_user(db, credentials)
    await audit_service.log_action(
        db,
        action="login",
        resource_type="auth",
        details={"email": credentials.email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    return await auth_service.refresh_access_token(db, body)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the current user's profile (name only — role changes require admin)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.flush()
    return UserResponse.model_validate(current_user)
