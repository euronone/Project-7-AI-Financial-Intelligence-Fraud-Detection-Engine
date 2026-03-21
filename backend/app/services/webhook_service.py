from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime

import httpx
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.models.webhook import Webhook
from app.schemas.webhook import (
    VALID_WEBHOOK_EVENTS,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)

logger = structlog.get_logger()

FINSHIELD_SIGNATURE_HEADER = "X-FinShield-Signature"
WEBHOOK_TIMEOUT_SECONDS = 10
MAX_FAILURE_COUNT = 5


def _sign_payload(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest for the given payload."""
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def list_webhooks(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
) -> WebhookListResponse:
    """List webhooks created by a specific user with pagination."""
    count_q = select(func.count()).select_from(Webhook).where(Webhook.created_by == user_id)
    total: int = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Webhook)
        .where(Webhook.created_by == user_id)
        .order_by(Webhook.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()

    return WebhookListResponse(
        items=[WebhookResponse.model_validate(w) for w in rows],
        total=total,
    )


async def get_webhook(db: AsyncSession, webhook_id: uuid.UUID) -> Webhook:
    """Fetch a single webhook by ID or raise NotFoundError."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if webhook is None:
        raise NotFoundError("Webhook", str(webhook_id))
    return webhook


async def create_webhook(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: WebhookCreate,
) -> Webhook:
    """Persist a new webhook configuration."""
    webhook = Webhook(
        name=data.name,
        url=str(data.url),
        events=data.events,
        secret=data.secret,
        is_active=True,
        failure_count=0,
        created_by=user_id,
    )
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    logger.info("webhook_created", webhook_id=str(webhook.id), name=data.name)
    return webhook


async def update_webhook(
    db: AsyncSession,
    webhook_id: uuid.UUID,
    data: WebhookUpdate,
) -> Webhook:
    """Apply partial updates to an existing webhook."""
    webhook = await get_webhook(db, webhook_id)
    update_fields = data.model_dump(exclude_unset=True)

    if "url" in update_fields and update_fields["url"] is not None:
        update_fields["url"] = str(update_fields["url"])

    for field, value in update_fields.items():
        setattr(webhook, field, value)

    await db.flush()
    await db.refresh(webhook)
    logger.info("webhook_updated", webhook_id=str(webhook_id))
    return webhook


async def delete_webhook(db: AsyncSession, webhook_id: uuid.UUID) -> None:
    """Delete a webhook permanently."""
    webhook = await get_webhook(db, webhook_id)
    await db.delete(webhook)
    await db.flush()
    logger.info("webhook_deleted", webhook_id=str(webhook_id))


async def test_webhook(
    db: AsyncSession,
    webhook_id: uuid.UUID,
    test_request: WebhookTestRequest,
) -> WebhookTestResponse:
    """Send a test payload to the webhook URL and report the result."""
    webhook = await get_webhook(db, webhook_id)

    if test_request.event_type not in VALID_WEBHOOK_EVENTS:
        raise BadRequestError(f"Invalid event type: {test_request.event_type}")

    payload = json.dumps({
        "event": test_request.event_type,
        "data": test_request.sample_data or {},
        "test": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }).encode()

    signature = _sign_payload(payload, webhook.secret)

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
            response = await client.post(
                webhook.url,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    FINSHIELD_SIGNATURE_HEADER: signature,
                },
            )
        elapsed_ms = (time.monotonic() - start) * 1000
        success = 200 <= response.status_code < 300
        return WebhookTestResponse(
            success=success,
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 2),
        )
    except httpx.HTTPError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning("webhook_test_failed", webhook_id=str(webhook_id), error=str(exc))
        return WebhookTestResponse(
            success=False,
            response_time_ms=round(elapsed_ms, 2),
            error=str(exc),
        )


async def trigger_webhooks(
    db: AsyncSession,
    event_type: str,
    payload: dict,
) -> None:
    """Fan-out an event to all active webhooks subscribed to event_type."""
    query = (
        select(Webhook)
        .where(
            Webhook.is_active.is_(True),
            Webhook.failure_count < MAX_FAILURE_COUNT,
            Webhook.events.any(event_type),
        )
    )
    webhooks = (await db.execute(query)).scalars().all()

    if not webhooks:
        return

    body = json.dumps({
        "event": event_type,
        "data": payload,
        "timestamp": datetime.now(UTC).isoformat(),
    }).encode()

    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
        for webhook in webhooks:
            signature = _sign_payload(body, webhook.secret)
            try:
                response = await client.post(
                    webhook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        FINSHIELD_SIGNATURE_HEADER: signature,
                    },
                )
                webhook.last_triggered_at = datetime.now(UTC)
                if response.status_code >= 400:
                    webhook.failure_count += 1
                    logger.warning(
                        "webhook_delivery_failed",
                        webhook_id=str(webhook.id),
                        status_code=response.status_code,
                    )
                else:
                    webhook.failure_count = 0
            except httpx.HTTPError as exc:
                webhook.failure_count += 1
                logger.error(
                    "webhook_delivery_error",
                    webhook_id=str(webhook.id),
                    error=str(exc),
                )

    await db.flush()
