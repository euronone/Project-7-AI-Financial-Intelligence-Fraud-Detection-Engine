"""Case management service."""

import math
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.case import Case, CasePriority, CaseStatus
from app.schemas.case import (
    CaseAssign,
    CaseCreate,
    CaseListResponse,
    CaseResponse,
    CaseStatistics,
    CaseStatusUpdate,
    CaseUpdate,
)

logger = structlog.get_logger()

_case_counter = 0


async def _next_case_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(Case))
    count = (result.scalar() or 0) + 1
    return f"CASE-{count:06d}"


async def list_cases(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    priority: str | None = None,
) -> CaseListResponse:
    query = select(Case)
    count_q = select(func.count()).select_from(Case)

    if status:
        query = query.where(Case.status == status)
        count_q = count_q.where(Case.status == status)
    if priority:
        query = query.where(Case.priority == priority)
        count_q = count_q.where(Case.priority == priority)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Case.created_at.desc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return CaseListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[CaseResponse.model_validate(c) for c in items],
    )


async def get_case(db: AsyncSession, case_id: uuid.UUID) -> Case:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Case", str(case_id))
    return case


async def create_case(db: AsyncSession, data: CaseCreate, user_id: uuid.UUID) -> Case:
    case_number = await _next_case_number(db)

    case = Case(
        case_number=case_number,
        title=data.title,
        description=data.description,
        status=CaseStatus.OPEN,
        priority=data.priority,
        assigned_to=data.assigned_to,
        alert_ids=data.alert_ids,
        created_by=user_id,
        timeline={"events": [{
            "type": "created",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": str(user_id),
            "notes": "Case created",
        }]},
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    logger.info("case_created", case_id=str(case.id), case_number=case_number)
    return case


async def update_case(db: AsyncSession, case_id: uuid.UUID, data: CaseUpdate) -> Case:
    case = await get_case(db, case_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    await db.flush()
    await db.refresh(case)
    logger.info("case_updated", case_id=str(case_id))
    return case


async def update_case_status(
    db: AsyncSession,
    case_id: uuid.UUID,
    data: CaseStatusUpdate,
    user_id: uuid.UUID,
) -> Case:
    case = await get_case(db, case_id)
    case.status = data.status

    if data.status in (CaseStatus.CLOSED_CONFIRMED_FRAUD, CaseStatus.CLOSED_FALSE_POSITIVE):
        case.closed_at = datetime.now(UTC)

    timeline = case.timeline or {"events": []}
    timeline["events"].append({
        "type": "status_change",
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": str(user_id),
        "new_status": data.status.value,
        "notes": data.notes,
    })
    case.timeline = timeline

    await db.flush()
    await db.refresh(case)
    logger.info("case_status_updated", case_id=str(case_id), status=data.status.value)
    return case


async def assign_case(db: AsyncSession, case_id: uuid.UUID, data: CaseAssign, user_id: uuid.UUID) -> Case:
    case = await get_case(db, case_id)
    case.assigned_to = data.assigned_to
    if case.status == CaseStatus.OPEN:
        case.status = CaseStatus.IN_PROGRESS

    timeline = case.timeline or {"events": []}
    timeline["events"].append({
        "type": "assigned",
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": str(user_id),
        "assigned_to": str(data.assigned_to),
    })
    case.timeline = timeline

    await db.flush()
    await db.refresh(case)
    logger.info("case_assigned", case_id=str(case_id), assigned_to=str(data.assigned_to))
    return case


async def get_case_statistics(db: AsyncSession) -> CaseStatistics:
    total = (await db.execute(select(func.count()).select_from(Case))).scalar() or 0

    status_counts: dict[str, int] = {}
    for s in CaseStatus:
        count = (await db.execute(
            select(func.count()).select_from(Case).where(Case.status == s)
        )).scalar() or 0
        status_counts[s.value] = count

    priority_counts: dict[str, int] = {}
    for p in CasePriority:
        count = (await db.execute(
            select(func.count()).select_from(Case).where(Case.priority == p)
        )).scalar() or 0
        priority_counts[p.value] = count

    return CaseStatistics(
        total=total,
        open=status_counts.get("open", 0),
        in_progress=status_counts.get("in_progress", 0),
        pending_review=status_counts.get("pending_review", 0),
        escalated=status_counts.get("escalated", 0),
        closed_confirmed_fraud=status_counts.get("closed_confirmed_fraud", 0),
        closed_false_positive=status_counts.get("closed_false_positive", 0),
        by_priority=priority_counts,
    )
