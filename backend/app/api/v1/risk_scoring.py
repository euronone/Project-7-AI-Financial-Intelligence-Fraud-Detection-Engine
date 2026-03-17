"""
F5 — Risk Scoring: FastAPI router.

Endpoints:
  GET  /risk-scoring/entity/{entity_id}          F5.1 / F5.3 — Entity risk profile
  GET  /risk-scoring/entity/{entity_id}/history  F5.4        — Risk score history
  POST /risk-scoring/calculate                   F5.1        — On-demand calculation
  GET  /risk-scoring/distribution                F5.5        — Distribution by tier
  GET  /risk-scoring/top-risk                    F5.6        — Top-N leaderboard
  POST /risk-scoring/auto-update                 F5.7        — Event-triggered update
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.risk_scoring import (
    AutoUpdateRequest,
    AutoUpdateResponse,
    CalculateRiskRequest,
    CalculateRiskResponse,
    EntityRiskProfile,
    RiskDistribution,
    RiskScoreHistory,
    TopRiskEntities,
)
from app.services.risk_scoring_service import RiskScoringService

router = APIRouter(prefix="/risk-scoring", tags=["Risk Scoring"])

_service = RiskScoringService()


# ── GET /risk-scoring/entity/{entity_id} ────────────────────────────────────

@router.get(
    "/entity/{entity_id}",
    response_model=EntityRiskProfile,
    summary="Get entity risk profile (F5.1 / F5.3)",
)
def get_entity_risk_profile(entity_id: str) -> EntityRiskProfile:
    profile = _service.get_entity_risk_profile(entity_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"No risk score found for entity '{entity_id}'",
        )
    return profile


# ── GET /risk-scoring/entity/{entity_id}/history ────────────────────────────

@router.get(
    "/entity/{entity_id}/history",
    response_model=RiskScoreHistory,
    summary="Risk score history per entity (F5.4)",
)
def get_risk_history(
    entity_id: str,
    limit: int = Query(30, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> RiskScoreHistory:
    return _service.get_risk_history(entity_id, limit=limit, offset=offset)


# ── POST /risk-scoring/calculate ────────────────────────────────────────────

@router.post(
    "/calculate",
    response_model=CalculateRiskResponse,
    status_code=201,
    summary="On-demand risk calculation (F5.1)",
)
def calculate_risk(body: CalculateRiskRequest) -> CalculateRiskResponse:
    return _service.compute_risk_score(
        entity_id=body.entity_id,
        transaction_data=body.transaction_data,
        watchlist_match=body.watchlist_match,
        triggered_rules=body.triggered_rules,
    )


# ── GET /risk-scoring/distribution ──────────────────────────────────────────

@router.get(
    "/distribution",
    response_model=RiskDistribution,
    summary="Risk distribution across entities (F5.5)",
)
def get_risk_distribution() -> RiskDistribution:
    return _service.get_risk_distribution()


# ── GET /risk-scoring/top-risk ───────────────────────────────────────────────

@router.get(
    "/top-risk",
    response_model=TopRiskEntities,
    summary="Top-N highest risk entities leaderboard (F5.6)",
)
def get_top_risk_entities(
    n: int = Query(10, ge=1, le=100, description="Number of top entities to return"),
) -> TopRiskEntities:
    return _service.get_top_risk_entities(n=n)


# ── POST /risk-scoring/auto-update ──────────────────────────────────────────

@router.post(
    "/auto-update",
    response_model=AutoUpdateResponse,
    summary="Auto-update risk score on event trigger (F5.7)",
)
def auto_update_risk_score(body: AutoUpdateRequest) -> AutoUpdateResponse:
    return _service.auto_update_risk_score(
        entity_id=body.entity_id,
        trigger=body.trigger,
        context=body.context,
    )
