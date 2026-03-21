import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.case import CaseCreate, CaseResponse
from app.schemas.fraud_alert import (
    AlertAssign,
    AlertListResponse,
    AlertResponse,
    AlertStatistics,
    AlertStatusUpdate,
)
from app.services import case_service, fraud_detection_service

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    alert_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> AlertListResponse:
    return await fraud_detection_service.list_alerts(
        db, page=page, page_size=page_size, status=status, severity=severity, alert_type=alert_type
    )


@router.get("/statistics", response_model=AlertStatistics)
async def alert_statistics(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> AlertStatistics:
    return await fraud_detection_service.get_alert_statistics(db)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> AlertResponse:
    alert = await fraud_detection_service.get_alert(db, alert_id)
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_status(
    alert_id: uuid.UUID,
    body: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> AlertResponse:
    alert = await fraud_detection_service.update_alert_status(db, alert_id, body, user.id)
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/assign", response_model=AlertResponse)
async def assign_alert(
    alert_id: uuid.UUID,
    body: AlertAssign,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> AlertResponse:
    alert = await fraud_detection_service.assign_alert(db, alert_id, body)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/escalate", response_model=AlertResponse)
async def escalate_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> AlertResponse:
    alert = await fraud_detection_service.escalate_alert(db, alert_id)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/create-case", response_model=CaseResponse)
async def create_case_from_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_analyst),
) -> CaseResponse:
    alert = await fraud_detection_service.get_alert(db, alert_id)
    case_data = CaseCreate(
        title=f"Case from alert: {alert.title}",
        description=alert.description,
        priority="high" if alert.severity.value in ("high", "critical") else "medium",
        alert_ids=[alert.id],
    )
    case = await case_service.create_case(db, case_data, user.id)
    return CaseResponse.model_validate(case)
