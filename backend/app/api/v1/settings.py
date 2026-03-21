from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.permissions import require_admin
from app.dependencies import get_db
from app.models.user import User
from app.schemas.settings import (
    ApiKeyCreate,
    ApiKeyFullResponse,
    ApiKeyResponse,
    SystemSettings,
    SystemSettingsUpdate,
    TeamListResponse,
    TeamMember,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/system", response_model=SystemSettings)
async def get_system_settings(
    _user: User = Depends(require_admin),
) -> SystemSettings:
    """Return current system settings derived from config + defaults."""
    cfg = get_settings()
    return SystemSettings(
        app_name=cfg.app_name,
        app_env=cfg.app_env,
    )


@router.put("/system", response_model=SystemSettings)
async def update_system_settings(
    body: SystemSettingsUpdate,
    _user: User = Depends(require_admin),
) -> SystemSettings:
    """Stub: merge incoming updates with current defaults and return."""
    cfg = get_settings()
    current = SystemSettings(app_name=cfg.app_name, app_env=cfg.app_env)
    update_data = body.model_dump(exclude_unset=True)
    updated = current.model_copy(update=update_data)
    logger.info("system_settings_updated", fields=list(update_data.keys()))
    return updated


@router.get("/team", response_model=TeamListResponse)
async def list_team(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> TeamListResponse:
    """List all users as team members."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return TeamListResponse(
        members=[TeamMember.model_validate(u) for u in users],
        total=len(users),
    )


@router.post("/api-keys", response_model=ApiKeyFullResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    _user: User = Depends(require_admin),
) -> ApiKeyFullResponse:
    """Stub: generate a mock API key. In production, persist and hash the key."""
    key_id = str(uuid.uuid4())
    raw_key = f"fsk_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=body.expires_in_days)

    logger.info("api_key_created", key_id=key_id, name=body.name)
    return ApiKeyFullResponse(
        id=key_id,
        name=body.name,
        key_prefix=raw_key[:8],
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        is_active=True,
        api_key=raw_key,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    _user: User = Depends(require_admin),
) -> list[ApiKeyResponse]:
    """Stub: returns an empty list until API key persistence is implemented."""
    return []


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    _user: User = Depends(require_admin),
) -> dict:
    """Stub: revoke an API key by ID."""
    logger.info("api_key_revoked", key_id=key_id)
    return {"message": f"API key {key_id} revoked"}
