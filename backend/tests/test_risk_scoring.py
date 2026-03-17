"""
F5 — Risk Scoring: Backend tests.

Covers:
  - RiskScorer unit tests (F5.1 / F5.2 / F5.3)
  - RiskScoringService unit tests (F5.4 / F5.5 / F5.6 / F5.7)
  - FastAPI endpoint integration tests (all 6 endpoints)

Run:
  cd backend
  pip install pytest httpx fastapi pydantic
  pytest tests/test_risk_scoring.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.ml.risk_scorer import RiskScorer, DEFAULT_THRESHOLDS
from app.services.risk_scoring_service import RiskScoringService
from app.main import app

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# RiskScorer Unit Tests (F5.1 / F5.2 / F5.3)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskScorer:
    def setup_method(self):
        self.scorer = RiskScorer()

    # ── F5.1: composite score is a weighted combination ──────────────────────

    def test_composite_score_in_range(self):
        score, _, _, _ = self.scorer.compute(0.5, 0.4, 0.3, 0.3, 0.2)
        assert 0.0 <= score <= 1.0

    def test_all_zeros_gives_low_score(self):
        score, level, _, _ = self.scorer.compute(0.0, 0.0, 0.0, 0.0, 0.0)
        assert score == 0.0
        assert level == "low"

    def test_all_ones_gives_critical(self):
        score, level, _, _ = self.scorer.compute(1.0, 1.0, 1.0, 1.0, 1.0)
        assert score == 1.0
        assert level == "critical"

    def test_weighted_composite_is_correct(self):
        # weights: ml=0.35, rule=0.25, vel=0.15, beh=0.15, net=0.10
        score, _, _, _ = self.scorer.compute(
            ml_score=0.8,
            rule_score=0.6,
            velocity_score=0.4,
            behavioral_score=0.4,
            network_score=0.2,
        )
        expected = 0.8 * 0.35 + 0.6 * 0.25 + 0.4 * 0.15 + 0.4 * 0.15 + 0.2 * 0.10
        assert abs(score - round(expected, 4)) < 1e-4

    # ── F5.2: risk level classification ─────────────────────────────────────

    def test_classify_low(self):
        assert self.scorer.classify(0.0) == "low"
        assert self.scorer.classify(0.29) == "low"
        assert self.scorer.classify(0.3) == "low"

    def test_classify_medium(self):
        assert self.scorer.classify(0.31) == "medium"
        assert self.scorer.classify(0.6) == "medium"

    def test_classify_high(self):
        assert self.scorer.classify(0.61) == "high"
        assert self.scorer.classify(0.8) == "high"

    def test_classify_critical(self):
        assert self.scorer.classify(0.81) == "critical"
        assert self.scorer.classify(1.0) == "critical"

    def test_watchlist_match_boosts_score_to_minimum_0_70(self):
        score, _, _, _ = self.scorer.compute(
            0.0, 0.0, 0.0, 0.0, 0.0, watchlist_match=True
        )
        assert score >= 0.70

    def test_history_penalty_applied(self):
        score_no_history, _, _, _ = self.scorer.compute(
            0.5, 0.5, 0.5, 0.5, 0.5, entity_history_count=0
        )
        score_with_history, _, _, _ = self.scorer.compute(
            0.5, 0.5, 0.5, 0.5, 0.5, entity_history_count=5
        )
        assert score_with_history >= score_no_history

    # ── F5.3: component scores are returned ─────────────────────────────────

    def test_explanation_not_empty(self):
        _, _, _, explanation = self.scorer.compute(0.7, 0.6, 0.5, 0.4, 0.3)
        assert isinstance(explanation, str)
        assert len(explanation) > 10

    def test_risk_factors_returned(self):
        _, _, factors, _ = self.scorer.compute(0.9, 0.8, 0.7, 0.7, 0.6)
        assert isinstance(factors, list)
        assert len(factors) > 0

    def test_no_risk_factors_when_all_low(self):
        _, _, factors, _ = self.scorer.compute(0.0, 0.0, 0.0, 0.0, 0.0)
        assert "No significant risk factors identified" in factors

    # ── F5.2: configurable thresholds ───────────────────────────────────────

    def test_custom_thresholds(self):
        scorer = RiskScorer(thresholds={"low_max": 0.2, "medium_max": 0.5, "high_max": 0.7, "critical_max": 1.0})
        assert scorer.classify(0.25) == "medium"  # above custom low_max of 0.2

    def test_update_thresholds_at_runtime(self):
        self.scorer.update_thresholds({"low_max": 0.1})
        assert self.scorer.thresholds["low_max"] == 0.1

    # ── Clamping ─────────────────────────────────────────────────────────────

    def test_scores_clamped_above_1(self):
        score, _, _, _ = self.scorer.compute(2.0, 2.0, 2.0, 2.0, 2.0)
        assert score <= 1.0

    def test_scores_clamped_below_0(self):
        score, _, _, _ = self.scorer.compute(-1.0, -1.0, -1.0, -1.0, -1.0)
        assert score >= 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# RiskScoringService Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskScoringService:
    def setup_method(self):
        self.svc = RiskScoringService()

    # ── F5.1: compute_risk_score ─────────────────────────────────────────────

    def test_compute_returns_response_object(self):
        result = self.svc.compute_risk_score(
            entity_id="test-entity-new",
            transaction_data={"id": "tx-1", "amount": 500.0},
        )
        assert result.entity_id == "test-entity-new"
        assert 0.0 <= result.overall_score <= 1.0
        assert result.risk_level in ("low", "medium", "high", "critical")
        assert isinstance(result.risk_factors, list)
        assert result.record_id

    def test_compute_high_amount_elevates_score(self):
        low = self.svc.compute_risk_score(
            "ent-test-a", {"id": "tx-low", "amount": 100.0}
        )
        high = self.svc.compute_risk_score(
            "ent-test-b", {"id": "tx-high", "amount": 50000.0}
        )
        assert high.overall_score >= low.overall_score

    def test_watchlist_match_raises_risk(self):
        no_wl = self.svc.compute_risk_score(
            "ent-wl-test", {"id": "tx-1", "amount": 10.0}, watchlist_match=False
        )
        with_wl = self.svc.compute_risk_score(
            "ent-wl-test", {"id": "tx-2", "amount": 10.0}, watchlist_match=True
        )
        assert with_wl.overall_score >= no_wl.overall_score

    def test_component_scores_are_valid(self):
        result = self.svc.compute_risk_score(
            "ent-comp", {"id": "tx-c", "amount": 200.0}
        )
        for field in ("ml_score", "rule_score", "velocity_score", "behavioral_score", "network_score"):
            val = getattr(result.component_scores, field)
            assert 0.0 <= val <= 1.0

    # ── F5.1: get_entity_risk_profile ────────────────────────────────────────

    def test_get_profile_existing_entity(self):
        profile = self.svc.get_entity_risk_profile("ent-001")
        assert profile is not None
        assert profile.entity_id == "ent-001"
        assert 0.0 <= profile.current_score <= 1.0
        assert len(profile.score_trend) > 0

    def test_get_profile_unknown_entity_returns_none(self):
        assert self.svc.get_entity_risk_profile("does-not-exist-xyz") is None

    # ── F5.4: get_risk_history ───────────────────────────────────────────────

    def test_history_returns_entries(self):
        history = self.svc.get_risk_history("ent-001")
        assert history.entity_id == "ent-001"
        assert history.total > 0
        assert len(history.history) > 0

    def test_history_pagination_limit(self):
        history = self.svc.get_risk_history("ent-001", limit=3)
        assert len(history.history) <= 3

    def test_history_unknown_entity_empty(self):
        history = self.svc.get_risk_history("ghost-entity")
        assert history.total == 0
        assert history.history == []

    # ── F5.5: get_risk_distribution ─────────────────────────────────────────

    def test_distribution_tiers_sum_to_total(self):
        dist = self.svc.get_risk_distribution()
        tier_sum = sum(t.count for t in dist.tiers)
        assert tier_sum == dist.total_entities

    def test_distribution_percentages_sum_to_100(self):
        dist = self.svc.get_risk_distribution()
        total_pct = sum(t.percentage for t in dist.tiers)
        assert abs(total_pct - 100.0) < 0.5  # rounding tolerance

    def test_distribution_all_four_tiers_present(self):
        dist = self.svc.get_risk_distribution()
        levels = {t.risk_level for t in dist.tiers}
        assert levels == {"low", "medium", "high", "critical"}

    # ── F5.6: get_top_risk_entities ─────────────────────────────────────────

    def test_top_risk_sorted_descending(self):
        top = self.svc.get_top_risk_entities(n=5)
        scores = [e.overall_score for e in top.entities]
        assert scores == sorted(scores, reverse=True)

    def test_top_risk_respects_n(self):
        top = self.svc.get_top_risk_entities(n=3)
        assert top.total_returned <= 3

    def test_top_risk_ranks_sequential(self):
        top = self.svc.get_top_risk_entities(n=5)
        ranks = [e.rank for e in top.entities]
        assert ranks == list(range(1, len(ranks) + 1))

    # ── F5.7: auto_update_risk_score ────────────────────────────────────────

    def test_auto_update_new_transaction(self):
        result = self.svc.auto_update_risk_score(
            "ent-001",
            "new_transaction",
            {"amount": 1000.0},
        )
        assert result.updated is True
        assert result.trigger == "new_transaction"
        assert 0.0 <= result.new_score <= 1.0

    def test_auto_update_watchlist_match_boosts_score(self):
        result = self.svc.auto_update_risk_score(
            "ent-003",  # normally low risk
            "watchlist_match",
            {"amount": 10.0},
        )
        assert result.new_score >= 0.70

    def test_auto_update_records_previous_score(self):
        from app.services.risk_scoring_service import _risk_store
        records = _risk_store.get("ent-002", [])
        prev = records[-1].overall_score if records else 0.0
        result = self.svc.auto_update_risk_score(
            "ent-002", "alert_resolution", {}
        )
        assert result.previous_score == prev


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Endpoint Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskScoringAPI:

    # ── GET /api/v1/risk-scoring/entity/{entity_id} ──────────────────────────

    def test_get_entity_profile_200(self):
        r = client.get("/api/v1/risk-scoring/entity/ent-001")
        assert r.status_code == 200
        body = r.json()
        assert body["entity_id"] == "ent-001"
        assert "current_score" in body
        assert "risk_level" in body
        assert "component_scores" in body
        assert "score_trend" in body

    def test_get_entity_profile_404(self):
        r = client.get("/api/v1/risk-scoring/entity/ghost-entity-xyz")
        assert r.status_code == 404

    def test_entity_profile_score_in_range(self):
        r = client.get("/api/v1/risk-scoring/entity/ent-002")
        body = r.json()
        assert 0.0 <= body["current_score"] <= 1.0

    # ── GET /api/v1/risk-scoring/entity/{entity_id}/history ─────────────────

    def test_get_history_200(self):
        r = client.get("/api/v1/risk-scoring/entity/ent-001/history")
        assert r.status_code == 200
        body = r.json()
        assert "history" in body
        assert "total" in body
        assert isinstance(body["history"], list)

    def test_get_history_pagination(self):
        r = client.get("/api/v1/risk-scoring/entity/ent-001/history?limit=3&offset=0")
        assert r.status_code == 200
        assert len(r.json()["history"]) <= 3

    def test_get_history_unknown_entity_empty(self):
        r = client.get("/api/v1/risk-scoring/entity/ghost-xyz/history")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0

    def test_get_history_invalid_limit(self):
        r = client.get("/api/v1/risk-scoring/entity/ent-001/history?limit=0")
        assert r.status_code == 422  # FastAPI validation error

    # ── POST /api/v1/risk-scoring/calculate ─────────────────────────────────

    def test_calculate_201(self):
        payload = {
            "entity_id": "ent-api-test",
            "transaction_data": {"id": "tx-api-1", "amount": 250.0},
            "watchlist_match": False,
        }
        r = client.post("/api/v1/risk-scoring/calculate", json=payload)
        assert r.status_code == 201
        body = r.json()
        assert body["entity_id"] == "ent-api-test"
        assert 0.0 <= body["overall_score"] <= 1.0
        assert body["risk_level"] in ("low", "medium", "high", "critical")
        assert "component_scores" in body
        assert "risk_factors" in body
        assert "explanation" in body
        assert "record_id" in body

    def test_calculate_missing_entity_id_422(self):
        r = client.post("/api/v1/risk-scoring/calculate", json={"transaction_data": {}})
        assert r.status_code == 422

    def test_calculate_empty_entity_id_422(self):
        r = client.post(
            "/api/v1/risk-scoring/calculate",
            json={"entity_id": "   ", "transaction_data": {}},
        )
        assert r.status_code == 422

    def test_calculate_watchlist_elevates_score(self):
        base = client.post(
            "/api/v1/risk-scoring/calculate",
            json={
                "entity_id": "wl-cmp",
                "transaction_data": {"id": "t1", "amount": 10.0},
                "watchlist_match": False,
            },
        ).json()
        boosted = client.post(
            "/api/v1/risk-scoring/calculate",
            json={
                "entity_id": "wl-cmp2",
                "transaction_data": {"id": "t2", "amount": 10.0},
                "watchlist_match": True,
            },
        ).json()
        assert boosted["overall_score"] >= base["overall_score"]

    # ── GET /api/v1/risk-scoring/distribution ────────────────────────────────

    def test_get_distribution_200(self):
        r = client.get("/api/v1/risk-scoring/distribution")
        assert r.status_code == 200
        body = r.json()
        assert "total_entities" in body
        assert "tiers" in body
        assert isinstance(body["tiers"], list)
        assert len(body["tiers"]) == 4

    def test_distribution_tiers_have_required_fields(self):
        r = client.get("/api/v1/risk-scoring/distribution")
        for tier in r.json()["tiers"]:
            assert "risk_level" in tier
            assert "count" in tier
            assert "percentage" in tier

    # ── GET /api/v1/risk-scoring/top-risk ────────────────────────────────────

    def test_get_top_risk_200(self):
        r = client.get("/api/v1/risk-scoring/top-risk")
        assert r.status_code == 200
        body = r.json()
        assert "entities" in body
        assert "total_returned" in body

    def test_top_risk_n_param(self):
        r = client.get("/api/v1/risk-scoring/top-risk?n=3")
        assert r.status_code == 200
        assert r.json()["total_returned"] <= 3

    def test_top_risk_scores_descending(self):
        r = client.get("/api/v1/risk-scoring/top-risk?n=5")
        scores = [e["overall_score"] for e in r.json()["entities"]]
        assert scores == sorted(scores, reverse=True)

    def test_top_risk_invalid_n(self):
        r = client.get("/api/v1/risk-scoring/top-risk?n=0")
        assert r.status_code == 422

    # ── POST /api/v1/risk-scoring/auto-update ────────────────────────────────

    def test_auto_update_new_transaction(self):
        payload = {
            "entity_id": "ent-001",
            "trigger": "new_transaction",
            "context": {"amount": 500.0},
        }
        r = client.post("/api/v1/risk-scoring/auto-update", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["entity_id"] == "ent-001"
        assert body["trigger"] == "new_transaction"
        assert body["updated"] is True
        assert "previous_score" in body
        assert "new_score" in body
        assert "risk_level" in body

    def test_auto_update_watchlist_trigger(self):
        payload = {
            "entity_id": "ent-003",
            "trigger": "watchlist_match",
            "context": {},
        }
        r = client.post("/api/v1/risk-scoring/auto-update", json=payload)
        assert r.status_code == 200
        assert r.json()["new_score"] >= 0.70

    def test_auto_update_invalid_trigger_422(self):
        r = client.post(
            "/api/v1/risk-scoring/auto-update",
            json={"entity_id": "ent-001", "trigger": "INVALID_TRIGGER"},
        )
        assert r.status_code == 422
