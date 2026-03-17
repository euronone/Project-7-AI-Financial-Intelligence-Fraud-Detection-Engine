import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.case import (
    CaseAssign,
    CaseCreate,
    CaseListResponse,
    CaseResponse,
    CaseStatistics,
    CaseStatusUpdate,
    CaseUpdate,
)
from app.services import case_service

router = APIRouter()


@router.get("", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> CaseListResponse:
    return await case_service.list_cases(db, page=page, page_size=page_size, status=status, priority=priority)


@router.get("/statistics", response_model=CaseStatistics)
async def case_statistics(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> CaseStatistics:
    return await case_service.get_case_statistics(db)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> CaseResponse:
    case = await case_service.get_case(db, case_id)
    return CaseResponse.model_validate(case)


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> CaseResponse:
    case = await case_service.create_case(db, data, user.id)
    return CaseResponse.model_validate(case)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> CaseResponse:
    case = await case_service.update_case(db, case_id, data)
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_status(
    case_id: uuid.UUID,
    body: CaseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> CaseResponse:
    case = await case_service.update_case_status(db, case_id, body, user.id)
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}/assign", response_model=CaseResponse)
async def assign_case(
    case_id: uuid.UUID,
    body: CaseAssign,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> CaseResponse:
    case = await case_service.assign_case(db, case_id, body, user.id)
    return CaseResponse.model_validate(case)


@router.get("/{case_id}/timeline")
async def get_timeline(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> dict:
    case = await case_service.get_case(db, case_id)
    return case.timeline or {"events": []}
