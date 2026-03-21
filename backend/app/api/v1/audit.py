import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin, require_viewer
from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse, NotificationListResponse
from app.schemas.common import MessageResponse
from app.services import notification_service

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    action: str | None = None,
    resource_type: str | None = None,
    user_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
) -> AuditLogListResponse:
    query = select(AuditLog)
    count_q = select(func.count()).select_from(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
        count_q = count_q.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_q = count_q.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_q = count_q.where(AuditLog.user_id == user_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[AuditLogResponse.model_validate(a) for a in items],
    )


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_viewer),
) -> NotificationListResponse:
    return await notification_service.list_notifications(
        db, user.id, page=page, page_size=page_size, unread_only=unread_only
    )


@router.patch("/notifications/{notification_id}/read", response_model=MessageResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_viewer),
) -> MessageResponse:
    await notification_service.mark_as_read(db, notification_id, user.id)
    return MessageResponse(message="Marked as read")


@router.post("/notifications/read-all", response_model=MessageResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_viewer),
) -> MessageResponse:
    count = await notification_service.mark_all_read(db, user.id)
    return MessageResponse(message=f"Marked {count} notifications as read")
