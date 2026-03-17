"""
F5 — Risk Scoring: Service layer.

Implements all F5 sub-tasks:
  F5.1  compute_risk_score()        — composite score from all components
  F5.2  classify()                  — delegated to RiskScorer
  F5.3  component breakdown          — returned in every score result
  F5.4  get_risk_history()           — per-entity historical scores
  F5.5  get_risk_distribution()      — entity counts per tier
  F5.6  get_top_risk_entities()      — leaderboard of highest-risk entities
  F5.7  auto_update_risk_score()     — re-score on event triggers
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.ml.risk_scorer import RiskScorer
from app.models.risk_score import RiskScoreRecord
from app.schemas.risk_scoring import (
    AutoUpdateResponse,
    CalculateRiskResponse,
    ComponentScores,
    EntityRiskProfile,
    RiskDistribution,
    RiskScoreHistory,
    RiskScoreHistoryEntry,
    RiskTierCount,
    TopRiskEntities,
    TopRiskEntity,
    UpdateTrigger,
)

# ── In-memory store (replace with async SQLAlchemy session in production) ───
_risk_store: Dict[str, List[RiskScoreRecord]] = {}  # entity_id → [records]

# Seed with deterministic mock data so the endpoints return useful results
def _seed_mock_data() -> None:
    from app.ml.risk_scorer import RiskScorer as _RS

    rs = _RS()
    now = datetime.now(timezone.utc)
    entities = [
        ("ent-001", 0.82, 0.75, 0.60, 0.70, 0.50, True),
        ("ent-002", 0.45, 0.30, 0.20, 0.35, 0.15, False),
        ("ent-003", 0.15, 0.10, 0.05, 0.10, 0.08, False),
        ("ent-004", 0.68, 0.55, 0.40, 0.50, 0.30, False),
        ("ent-005", 0.92, 0.88, 0.75, 0.80, 0.65, True),
        ("ent-006", 0.25, 0.20, 0.10, 0.15, 0.05, False),
        ("ent-007", 0.58, 0.50, 0.35, 0.45, 0.25, False),
        ("ent-008", 0.78, 0.65, 0.55, 0.60, 0.40, False),
    ]
    for eid, ml, rule, vel, beh, net, wl in entities:
        records: List[RiskScoreRecord] = []
        for i in range(10):
            drift = i * 0.01
            score, level, factors, explanation = rs.compute(
                ml + drift, rule + drift, vel + drift,
                beh + drift, net + drift, wl,
            )
            records.append(
                RiskScoreRecord(
                    entity_id=eid,
                    overall_score=score,
                    component_scores={
                        "ml_score": round(ml + drift, 4),
                        "rule_score": round(rule + drift, 4),
                        "velocity_score": round(vel + drift, 4),
                        "behavioral_score": round(beh + drift, 4),
                        "network_score": round(net + drift, 4),
                    },
                    risk_factors=factors,
                    model_version="risk_scorer_v1.0.0",
                    explanation=explanation,
                    created_at=now - timedelta(days=9 - i),
                )
            )
        _risk_store[eid] = records


_seed_mock_data()


class RiskScoringService:
    """All F5 business logic."""

    def __init__(self) -> None:
        self._scorer = RiskScorer()

    # ── F5.1 / F5.2 / F5.3: On-demand calculation ───────────────────────

    def compute_risk_score(
        self,
        entity_id: str,
        transaction_data: Dict,
        watchlist_match: bool = False,
        triggered_rules: Optional[List[str]] = None,
    ) -> CalculateRiskResponse:
        """
        Compute a composite risk score for an entity on a given transaction.
        Persists the result to the in-memory store (F5.7 compatible).
        """
        # Derive component scores from transaction data + ML pipeline outputs
        ml_score = self._derive_ml_score(transaction_data)
        rule_score = self._derive_rule_score(triggered_rules or [], transaction_data)
        velocity_score = self._derive_velocity_score(entity_id, transaction_data)
        behavioral_score = self._derive_behavioral_score(entity_id, transaction_data)
        network_score = self._derive_network_score(transaction_data)

        history_count = len(_risk_store.get(entity_id, []))

        overall, risk_level, risk_factors, explanation = self._scorer.compute(
            ml_score=ml_score,
            rule_score=rule_score,
            velocity_score=velocity_score,
            behavioral_score=behavioral_score,
            network_score=network_score,
            watchlist_match=watchlist_match,
            entity_history_count=history_count,
        )

        component_scores = {
            "ml_score": round(ml_score, 4),
            "rule_score": round(rule_score, 4),
            "velocity_score": round(velocity_score, 4),
            "behavioral_score": round(behavioral_score, 4),
            "network_score": round(network_score, 4),
        }

        record = RiskScoreRecord(
            entity_id=entity_id,
            overall_score=overall,
            component_scores=component_scores,
            risk_factors=risk_factors,
            model_version=self._scorer.model_version,
            explanation=explanation,
            transaction_id=transaction_data.get("id"),
        )
        _risk_store.setdefault(entity_id, []).append(record)

        return CalculateRiskResponse(
            entity_id=entity_id,
            overall_score=overall,
            risk_level=risk_level,
            component_scores=ComponentScores(**component_scores),
            risk_factors=risk_factors,
            explanation=explanation,
            model_version=self._scorer.model_version,
            record_id=record.id,
        )

    # ── F5.1 / F5.4: Entity risk profile ────────────────────────────────

    def get_entity_risk_profile(self, entity_id: str) -> Optional[EntityRiskProfile]:
        """Return the latest risk score + trend for an entity."""
        records = _risk_store.get(entity_id)
        if not records:
            return None

        latest = records[-1]
        trend = [r.overall_score for r in records[-30:]]

        return EntityRiskProfile(
            entity_id=entity_id,
            current_score=latest.overall_score,
            risk_level=self._scorer.classify(latest.overall_score),
            component_scores=ComponentScores(**latest.component_scores),
            risk_factors=latest.risk_factors,
            model_version=latest.model_version,
            explanation=latest.explanation,
            last_updated=latest.created_at,
            score_trend=trend,
        )

    # ── F5.4: Risk score history ─────────────────────────────────────────

    def get_risk_history(
        self,
        entity_id: str,
        limit: int = 30,
        offset: int = 0,
    ) -> RiskScoreHistory:
        """Return paginated score history for an entity."""
        records = _risk_store.get(entity_id, [])
        total = len(records)
        page = records[offset: offset + limit]

        entries = [
            RiskScoreHistoryEntry(
                id=r.id,
                overall_score=r.overall_score,
                risk_level=self._scorer.classify(r.overall_score),
                component_scores=ComponentScores(**r.component_scores),
                risk_factors=r.risk_factors,
                transaction_id=r.transaction_id,
                created_at=r.created_at,
            )
            for r in page
        ]

        return RiskScoreHistory(entity_id=entity_id, history=entries, total=total)

    # ── F5.5: Risk distribution ──────────────────────────────────────────

    def get_risk_distribution(self) -> RiskDistribution:
        """Return entity count per risk tier across all tracked entities."""
        tier_counts: Dict[str, int] = {
            "low": 0, "medium": 0, "high": 0, "critical": 0,
        }
        total = len(_risk_store)

        for entity_id, records in _risk_store.items():
            if not records:
                continue
            latest_score = records[-1].overall_score
            level = self._scorer.classify(latest_score)
            tier_counts[level] += 1

        tiers = [
            RiskTierCount(
                risk_level=level,
                count=count,
                percentage=round(count / total * 100, 2) if total else 0.0,
            )
            for level, count in tier_counts.items()
        ]

        return RiskDistribution(
            total_entities=total,
            tiers=tiers,
            thresholds=self._scorer.thresholds,
        )

    # ── F5.6: Top-N leaderboard ──────────────────────────────────────────

    def get_top_risk_entities(self, n: int = 10) -> TopRiskEntities:
        """Return the N entities with the highest current risk score."""
        snapshots = []
        for entity_id, records in _risk_store.items():
            if not records:
                continue
            latest = records[-1]
            snapshots.append((entity_id, latest))

        snapshots.sort(key=lambda x: x[1].overall_score, reverse=True)
        top = snapshots[:n]

        entities = [
            TopRiskEntity(
                rank=i + 1,
                entity_id=eid,
                overall_score=rec.overall_score,
                risk_level=self._scorer.classify(rec.overall_score),
                risk_factors=rec.risk_factors,
                last_updated=rec.created_at,
            )
            for i, (eid, rec) in enumerate(top)
        ]

        return TopRiskEntities(entities=entities, total_returned=len(entities))

    # ── F5.7: Auto-update on events ─────────────────────────────────────

    def auto_update_risk_score(
        self,
        entity_id: str,
        trigger: UpdateTrigger,
        context: Dict,
    ) -> AutoUpdateResponse:
        """Re-score an entity on a triggering event (F5.7)."""
        records = _risk_store.get(entity_id, [])
        previous_score = records[-1].overall_score if records else 0.0

        # Build synthetic transaction data from context
        tx_data = {
            "id": context.get("transaction_id", str(uuid.uuid4())),
            "amount": context.get("amount", 0.0),
            "source_entity_id": entity_id,
        }
        watchlist_match = trigger == UpdateTrigger.WATCHLIST_MATCH or context.get(
            "watchlist_match", False
        )
        result = self.compute_risk_score(
            entity_id=entity_id,
            transaction_data=tx_data,
            watchlist_match=watchlist_match,
        )

        return AutoUpdateResponse(
            entity_id=entity_id,
            trigger=trigger,
            previous_score=previous_score,
            new_score=result.overall_score,
            risk_level=result.risk_level,
            updated=True,
        )

    # ── Internal score derivation helpers ───────────────────────────────

    @staticmethod
    def _derive_ml_score(tx: Dict) -> float:
        amount = float(tx.get("amount", 0.0))
        distance = float(tx.get("distance_from_last_tx_km", 0.0))
        return min(1.0, (amount / 10_000.0) * 0.7 + (distance / 5_000.0) * 0.3)

    @staticmethod
    def _derive_rule_score(rules: List[str], tx: Dict) -> float:
        score = 0.0
        amount = float(tx.get("amount", 0.0))
        if amount > 10_000:
            score = max(score, 0.8)
        if amount > 5_000:
            score = max(score, 0.5)
        if rules:
            score = max(score, 0.6)
        return min(1.0, score)

    @staticmethod
    def _derive_velocity_score(entity_id: str, tx: Dict) -> float:
        records = _risk_store.get(entity_id, [])
        recent = [
            r for r in records
            if r.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ]
        count = len(recent)
        if count > 20:
            return 0.9
        if count > 10:
            return 0.6
        if count > 5:
            return 0.3
        return 0.05

    @staticmethod
    def _derive_behavioral_score(entity_id: str, tx: Dict) -> float:
        records = _risk_store.get(entity_id, [])
        if not records:
            return 0.1
        avg = sum(r.overall_score for r in records[-10:]) / len(records[-10:])
        current_amount = float(tx.get("amount", 0.0))
        deviation = min(1.0, current_amount / 10_000.0)
        return min(1.0, avg * 0.5 + deviation * 0.5)

    @staticmethod
    def _derive_network_score(tx: Dict) -> float:
        known_fraud_nodes = int(tx.get("known_fraud_nodes", 0))
        shared_devices = int(tx.get("shared_devices", 0))
        return min(1.0, known_fraud_nodes * 0.3 + shared_devices * 0.1)
