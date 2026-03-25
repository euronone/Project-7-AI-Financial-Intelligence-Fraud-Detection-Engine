"""Authentication endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, Tenant
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictException, UnauthorizedException, NotFoundException
from app.dependencies import CurrentUser
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=dict, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new institution + admin user."""
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already registered")

    # Create tenant (institution)
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_name=body.institution_name,
        institution_type=body.institution_type,
        subscription_plan=body.subscription_plan,
        plan_started_at=datetime.now(timezone.utc),
    )
    db.add(tenant)
    await db.flush()  # get tenant.id before creating user

    # Create admin user
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        phone_number=body.phone_number,
        role="admin",
        is_active=True,
        is_verified=True,
        supabase_uid=body.supabase_uid,
    )
    db.add(user)
    await db.commit()

    # Generate tokens
    token_data = {"sub": user.id, "tenant_id": tenant.id, "role": user.role}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "Bearer",
        "user": UserResponse.from_user(user, tenant).model_dump(),
    }


@router.post("/login", response_model=dict)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Email/password login — returns JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    # Fetch tenant
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token_data = {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "Bearer",
        "expires_in": 900,
        "user": UserResponse.from_user(user, tenant).model_dump(),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for new access + refresh tokens."""
    import jwt as _jwt
    try:
        payload = decode_token(body.refresh_token)
    except _jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Not a refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")

    token_data = {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=900,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Return current authenticated user profile."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return UserResponse.from_user(current_user, tenant)


@router.post("/logout")
async def logout(current_user: CurrentUser):
    """Logout — client should discard tokens (stateless JWT)."""
    return {"message": "Logged out successfully"}
