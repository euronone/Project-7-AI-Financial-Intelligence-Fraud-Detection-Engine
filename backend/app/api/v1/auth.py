"""Auth endpoints — login, refresh, logout, me."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _svc(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, svc: AuthService = Depends(_svc)):
    return await svc.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, svc: AuthService = Depends(_svc)):
    return await svc.refresh(body.refresh_token)


@router.post("/logout")
async def logout():
    """Client-side logout — instruct client to discard tokens."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(
    authorization: str = Header(..., alias="Authorization"),
    svc: AuthService = Depends(_svc),
):
    token = authorization.removeprefix("Bearer ").strip()
    user = await svc.get_current_user(token)
    return UserResponse.from_orm_user(user)
