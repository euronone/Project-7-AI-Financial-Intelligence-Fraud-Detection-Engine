"""In-app notification service."""

import uuid

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.schemas.audit import NotificationListResponse, NotificationResponse

logger = structlog.get_logger()


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        metadata_=metadata,
    )
    db.add(notif)
    await db.flush()
    logger.info("notification_created", user_id=str(user_id), type=notification_type.value)
    return notif


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    unread_only: bool = False,
) -> NotificationListResponse:
    query = select(Notification).where(Notification.user_id == user_id)
    count_q = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    unread_q = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
    )

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
        count_q = count_q.where(Notification.is_read == False)  # noqa: E712

    total = (await db.execute(count_q)).scalar() or 0
    unread = (await db.execute(unread_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return NotificationListResponse(
        total=total,
        unread=unread,
        items=[NotificationResponse.model_validate(n) for n in items],
    )


async def mark_as_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.flush()


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount
