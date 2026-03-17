from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)
from app.services import webhook_service

router = APIRouter()


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_viewer),
) -> WebhookListResponse:
    return await webhook_service.list_webhooks(
        db, user.id, page=page, page_size=page_size,
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> WebhookResponse:
    webhook = await webhook_service.get_webhook(db, webhook_id)
    return WebhookResponse.model_validate(webhook)


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> WebhookResponse:
    webhook = await webhook_service.create_webhook(db, user.id, body)
    return WebhookResponse.model_validate(webhook)


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID,
    body: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> WebhookResponse:
    webhook = await webhook_service.update_webhook(db, webhook_id, body)
    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> dict:
    await webhook_service.delete_webhook(db, webhook_id)
    return {"message": f"Webhook {webhook_id} deleted"}


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: uuid.UUID,
    body: WebhookTestRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> WebhookTestResponse:
    return await webhook_service.test_webhook(db, webhook_id, body)
