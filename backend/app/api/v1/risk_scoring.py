import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.ml_model import (
    PipelineResultResponse,
    RiskDistribution,
    RiskScoreListResponse,
    TopRiskEntity,
)
from app.services import risk_scoring_service

router = APIRouter()


@router.post("/transactions/{transaction_id}/score", response_model=PipelineResultResponse)
async def score_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> PipelineResultResponse:
    return await risk_scoring_service.score_transaction(db, transaction_id)


@router.post("/entities/{entity_id}/calculate", response_model=PipelineResultResponse)
async def calculate_entity_risk(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> PipelineResultResponse:
    return await risk_scoring_service.calculate_entity_risk(db, entity_id)


@router.get("/entities/{entity_id}/history", response_model=RiskScoreListResponse)
async def entity_risk_history(
    entity_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RiskScoreListResponse:
    return await risk_scoring_service.get_entity_risk_history(db, entity_id, page=page, page_size=page_size)


@router.get("/distribution", response_model=RiskDistribution)
async def risk_distribution(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> RiskDistribution:
    return await risk_scoring_service.get_risk_distribution(db)


@router.get("/top-risk", response_model=list[TopRiskEntity])
async def top_risk_entities(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> list[TopRiskEntity]:
    return await risk_scoring_service.get_top_risk_entities(db, limit=limit)
