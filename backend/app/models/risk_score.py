"""
F5 — Risk Scoring: SQLAlchemy async model for risk_scores table.

DB Schema:
  id              UUID PK
  entity_id       UUID FK → entities(id)
  transaction_id  UUID FK → transactions(id), NULLABLE
  overall_score   DECIMAL(5,4) NOT NULL
  component_scores JSONB NOT NULL  (breakdown by factor)
  risk_factors    JSONB NOT NULL   (array of contributing factors)
  model_version   VARCHAR(50) NOT NULL
  explanation     TEXT NULLABLE
  created_at      TIMESTAMPTZ default NOW()
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# SQLAlchemy imports — ready for real DB wiring
try:
    from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class RiskScore(Base):
        __tablename__ = "risk_scores"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
        transaction_id = Column(UUID(as_uuid=True), nullable=True)
        overall_score = Column(Numeric(5, 4), nullable=False)
        component_scores = Column(JSONB, nullable=False)
        risk_factors = Column(JSONB, nullable=False)
        model_version = Column(String(50), nullable=False)
        explanation = Column(Text, nullable=True)
        created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )

except ImportError:
    # SQLAlchemy not installed — model defined as plain dataclass for testing
    Base = None
    RiskScore = None


# ── Pure-Python dataclass mirror (used by service layer without DB) ──────────

class RiskScoreRecord:
    """In-memory representation of a risk_scores row."""

    def __init__(
        self,
        entity_id: str,
        overall_score: float,
        component_scores: Dict[str, float],
        risk_factors: List[str],
        model_version: str,
        explanation: Optional[str] = None,
        transaction_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        id: Optional[str] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.entity_id = entity_id
        self.transaction_id = transaction_id
        self.overall_score = round(float(overall_score), 4)
        self.component_scores = component_scores
        self.risk_factors = risk_factors
        self.model_version = model_version
        self.explanation = explanation
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "transaction_id": self.transaction_id,
            "overall_score": self.overall_score,
            "component_scores": self.component_scores,
            "risk_factors": self.risk_factors,
            "model_version": self.model_version,
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat(),
        }
