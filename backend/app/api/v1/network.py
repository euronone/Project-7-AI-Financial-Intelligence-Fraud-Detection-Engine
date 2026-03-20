from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_analyst, require_viewer
from app.dependencies import get_db
from app.models.user import User
from app.schemas.network import (
    EntityConnectionResponse,
    NetworkAnalysisRequest,
    NetworkAnalysisResponse,
    NetworkGraphResponse,
)
from app.services import network_analysis_service

logger = structlog.get_logger()

router = APIRouter()


@router.get("/graph", response_model=NetworkGraphResponse)
async def get_network_graph(
    min_transactions: int = Query(default=2, ge=1),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> NetworkGraphResponse:
    """Return the transaction network graph for visualization."""
    return await network_analysis_service.get_network_graph(
        db, min_transactions=min_transactions, limit=limit
    )


@router.get("/entity/{entity_id}/connections", response_model=EntityConnectionResponse)
async def get_entity_connections(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer),
) -> EntityConnectionResponse:
    """Return all entities connected to the given entity via transactions."""
    return await network_analysis_service.get_entity_connections(db, entity_id)


@router.post("/analyze", response_model=NetworkAnalysisResponse)
async def analyze_network(
    body: NetworkAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst),
) -> NetworkAnalysisResponse:
    """Run network-based fraud analysis with cluster detection."""
    return await network_analysis_service.analyze_network(db, body)
