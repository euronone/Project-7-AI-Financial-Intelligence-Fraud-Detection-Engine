"""
F5 — Risk Scoring: Pydantic v2 request / response schemas.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "low"          # 0.0 – 0.3
    MEDIUM = "medium"    # 0.3 – 0.6
    HIGH = "high"        # 0.6 – 0.8
    CRITICAL = "critical"  # 0.8 – 1.0


class UpdateTrigger(str, Enum):
    NEW_TRANSACTION = "new_transaction"
    ALERT_RESOLUTION = "alert_resolution"
    WATCHLIST_MATCH = "watchlist_match"


# ── Component breakdown (F5.3) ──────────────────────────────────────────────

class ComponentScores(BaseModel):
    ml_score: float = Field(..., ge=0.0, le=1.0, description="ML ensemble fraud probability")
    rule_score: float = Field(..., ge=0.0, le=1.0, description="Rules engine trigger score")
    velocity_score: float = Field(..., ge=0.0, le=1.0, description="Transaction velocity anomaly score")
    behavioral_score: float = Field(..., ge=0.0, le=1.0, description="Behavioral deviation score")
    network_score: float = Field(..., ge=0.0, le=1.0, description="Network / fraud-ring score")


# ── Core risk score payload ──────────────────────────────────────────────────

class RiskScoreBase(BaseModel):
    entity_id: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    component_scores: ComponentScores
    risk_factors: List[str] = Field(default_factory=list)
    model_version: str
    explanation: Optional[str] = None
    transaction_id: Optional[str] = None


class RiskScoreResponse(RiskScoreBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Entity risk profile (F5.1 / F5.3 / F5.4) ────────────────────────────────

class EntityRiskProfile(BaseModel):
    entity_id: str
    current_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    component_scores: ComponentScores
    risk_factors: List[str]
    model_version: str
    explanation: Optional[str] = None
    last_updated: datetime
    score_trend: List[float] = Field(
        default_factory=list,
        description="Last 30 overall scores in chronological order",
    )


# ── Risk score history entry (F5.4) ──────────────────────────────────────────

class RiskScoreHistoryEntry(BaseModel):
    id: str
    overall_score: float
    risk_level: RiskLevel
    component_scores: ComponentScores
    risk_factors: List[str]
    transaction_id: Optional[str]
    created_at: datetime


class RiskScoreHistory(BaseModel):
    entity_id: str
    history: List[RiskScoreHistoryEntry]
    total: int


# ── On-demand calculate request / response (F5.1) ───────────────────────────

class CalculateRiskRequest(BaseModel):
    entity_id: str
    transaction_data: Dict = Field(
        ...,
        description="Raw transaction payload forwarded to ML pipeline",
    )
    watchlist_match: bool = Field(False, description="Whether entity has a watchlist hit")
    triggered_rules: List[str] = Field(default_factory=list)

    @field_validator("entity_id")
    @classmethod
    def entity_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("entity_id must not be empty")
        return v


class CalculateRiskResponse(BaseModel):
    entity_id: str
    overall_score: float
    risk_level: RiskLevel
    component_scores: ComponentScores
    risk_factors: List[str]
    explanation: str
    model_version: str
    record_id: str


# ── Risk distribution (F5.5) ─────────────────────────────────────────────────

class RiskTierCount(BaseModel):
    risk_level: RiskLevel
    count: int
    percentage: float


class RiskDistribution(BaseModel):
    total_entities: int
    tiers: List[RiskTierCount]
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "low_max": 0.3,
            "medium_max": 0.6,
            "high_max": 0.8,
            "critical_max": 1.0,
        }
    )


# ── Top-N leaderboard (F5.6) ─────────────────────────────────────────────────

class TopRiskEntity(BaseModel):
    rank: int
    entity_id: str
    overall_score: float
    risk_level: RiskLevel
    risk_factors: List[str]
    last_updated: datetime


class TopRiskEntities(BaseModel):
    entities: List[TopRiskEntity]
    total_returned: int


# ── Auto-update trigger (F5.7) ───────────────────────────────────────────────

class AutoUpdateRequest(BaseModel):
    entity_id: str
    trigger: UpdateTrigger
    context: Dict = Field(default_factory=dict)


class AutoUpdateResponse(BaseModel):
    entity_id: str
    trigger: UpdateTrigger
    previous_score: float
    new_score: float
    risk_level: RiskLevel
    updated: bool
