"""Authentication endpoints — signup, login, forgot/reset password, change password."""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import jwt as _jwt
import logging

from app.db.session import get_db
from app.models.user import User, Tenant
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    AdminSetPasswordRequest,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    NotFoundException,
    ForbiddenException,
)
from app.dependencies import CurrentUser, AdminUser
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reset_token(user: User) -> str:
    """
    Create a one-time-use password reset JWT.
    Signed with JWT_SECRET + first 16 chars of the current password hash,
    so it becomes invalid the moment the password changes.
    """
    payload = {
        "sub": user.id,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    secret = settings.JWT_SECRET + (user.hashed_password or "")[:16]
    return _jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def _verify_reset_token(token: str, user: User) -> dict:
    """Decode and validate a password reset token for the given user."""
    secret = settings.JWT_SECRET + (user.hashed_password or "")[:16]
    try:
        payload = _jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except _jwt.ExpiredSignatureError:
        raise UnauthorizedException("Reset link has expired. Request a new one.")
    except _jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid reset token.")

    if payload.get("type") != "password_reset":
        raise UnauthorizedException("Invalid token type.")
    if payload.get("sub") != user.id:
        raise UnauthorizedException("Token does not match user.")
    return payload


async def _send_reset_email(email: str, reset_link: str) -> bool:
    """
    Send password reset email via Resend.com (if configured).
    Falls back gracefully — caller handles the 'link' field in response.
    """
    if not settings.RESEND_API_KEY:
        return False
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                    "to": [email],
                    "subject": "Reset your FinShield AI password",
                    "html": f"""
                        <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px">
                          <h2 style="color:#00FF87">Reset your password</h2>
                          <p>Click the link below to reset your FinShield AI password.
                             This link expires in <strong>1 hour</strong>.</p>
                          <a href="{reset_link}"
                             style="display:inline-block;background:#00FF87;color:#000;
                                    font-weight:bold;padding:12px 24px;border-radius:8px;
                                    text-decoration:none;margin:16px 0">
                            Reset Password
                          </a>
                          <p style="color:#666;font-size:12px">
                            If you did not request a password reset, ignore this email.
                          </p>
                        </div>
                    """,
                },
                timeout=10,
            )
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Failed to send reset email via Resend: %s", exc)
        return False


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------


@router.post("/signup", response_model=dict, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new institution + owner user.
    signup_role: 'admin' → institution owner (full access)
                 'user'  → analyst member (limited access, no admin features)
    """
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already registered")

    # Map signup_role to internal role
    role = "admin" if body.signup_role == "admin" else "analyst"

    # Create tenant (institution)
    # Pre-seed notification config with the signup email so fraud alerts have a
    # destination from day one — user can edit later in Settings → Notifications.
    tenant = Tenant(
        id=str(uuid.uuid4()),
        organization_name=body.institution_name,
        institution_type=body.institution_type,
        subscription_plan=body.subscription_plan,
        plan_started_at=datetime.now(timezone.utc),
        db_config_json={
            "notifications": {
                "company_alert_email": body.email,
                "sms_enabled": bool(body.phone_number),
                "email_customer": True,
                "email_company": True,
            }
        },
    )
    db.add(tenant)
    await db.flush()  # get tenant.id before creating user

    # Create user
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        phone_number=body.phone_number,
        role=role,
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


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=dict)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Email/password login — returns JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)  # noqa: E712
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


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for new access + refresh tokens."""
    try:
        payload = decode_token(body.refresh_token)
    except _jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Not a refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")

    token_data = {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=900,
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Return current authenticated user profile."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return UserResponse.from_user(current_user, tenant)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
async def logout(current_user: CurrentUser):
    """Logout — client should discard tokens (stateless JWT)."""
    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate password reset flow.
    Sends a reset link via email if Resend is configured.
    In development (no email service), returns the reset link directly in the response.
    Always returns 200 — never reveals whether the email exists (anti-enumeration).
    """
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if not user:
        # Anti-enumeration: always return success
        return {"message": "If that email exists, a reset link has been sent.", "sent": False}

    reset_token = _make_reset_token(user)

    # Build reset URL — use the Origin header or fall back to localhost
    origin = request.headers.get("origin", "http://localhost:3000")
    reset_link = f"{origin}/reset-password?token={reset_token}&uid={user.id}"

    email_sent = await _send_reset_email(user.email, reset_link)

    response: dict = {
        "message": "If that email exists, a reset link has been sent.",
        "sent": email_sent,
    }

    # In development (no email configured), expose the link so devs can test
    if settings.is_development and not email_sent:
        response["dev_reset_link"] = reset_link
        response["dev_note"] = "Configure RESEND_API_KEY in .env to send real emails"

    return response


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate reset token and update password."""
    result = await db.execute(
        select(User).where(User.id == body.uid, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User")

    # Validate reset token (raises UnauthorizedException if invalid)
    _verify_reset_token(body.token, user)

    # Update password
    user.hashed_password = hash_password(body.new_password)
    user.must_change_password = False
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Password updated successfully. You can now log in."}


# ---------------------------------------------------------------------------
# POST /auth/change-password  (authenticated user changing own password)
# ---------------------------------------------------------------------------


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Authenticated user changes their own password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    current_user.must_change_password = False
    current_user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Password changed successfully"}


# ---------------------------------------------------------------------------
# POST /auth/admin/set-password  (admin sets/resets another user's password)
# ---------------------------------------------------------------------------


@router.post("/admin/set-password")
async def admin_set_password(
    body: AdminSetPasswordRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin sets a temporary password for a user in the same tenant."""
    result = await db.execute(
        select(User).where(User.id == body.user_id, User.tenant_id == admin.tenant_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise NotFoundException("User")

    # Admins cannot change other admins' passwords (only same or lower role)
    if target_user.role == "admin" and target_user.id != admin.id:
        raise ForbiddenException("Cannot change another admin's password")

    target_user.hashed_password = hash_password(body.new_password)
    target_user.must_change_password = body.force_reset
    target_user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": "Password updated",
        "user_id": target_user.id,
        "must_change_password": body.force_reset,
    }
