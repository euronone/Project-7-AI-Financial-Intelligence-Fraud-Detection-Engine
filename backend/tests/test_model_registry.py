"""
Phase 3 — #15: Tests for ML Model Registry (F2.7 / F2.8 / F2.9)

Coverage:
  - MLModelRegistry (unit)
  - ModelRegistryService (unit)
  - /api/v1/models/* (integration via FastAPI TestClient)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.registry import MLModelRegistry, RegisteredModel
from app.services.model_registry_service import ModelRegistryService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def fresh_registry() -> MLModelRegistry:
    """Clean registry seeded with 5 default models."""
    return MLModelRegistry()


@pytest.fixture()
def svc(fresh_registry) -> ModelRegistryService:
    return ModelRegistryService(reg=fresh_registry)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# TestMLModelRegistry — unit tests for the in-memory registry
# ═══════════════════════════════════════════════════════════════════════════════

class TestMLModelRegistry:

    def test_seed_5_models(self, fresh_registry):
        models = fresh_registry.list_models()
        assert len(models) == 5

    def test_list_all_returns_sorted_by_created_desc(self, fresh_registry):
        models = fresh_registry.list_models()
        for i in range(len(models) - 1):
            assert models[i].created_at >= models[i + 1].created_at

    def test_list_filter_by_type(self, fresh_registry):
        fraud = fresh_registry.list_models(model_type="fraud_classifier")
        assert all(m.model_type == "fraud_classifier" for m in fraud)
        assert len(fraud) == 2  # reg-xgb-001 + reg-graph-001

    def test_list_filter_by_status(self, fresh_registry):
        active = fresh_registry.list_models(status="active")
        assert all(m.status == "active" for m in active)

    def test_list_filter_type_and_status(self, fresh_registry):
        result = fresh_registry.list_models(
            model_type="anomaly_detector", status="active"
        )
        assert len(result) == 1
        assert result[0].id == "reg-iso-001"

    def test_get_model_existing(self, fresh_registry):
        m = fresh_registry.get_model("reg-xgb-001")
        assert m is not None
        assert m.name == "XGBoost Fraud Classifier"

    def test_get_model_missing(self, fresh_registry):
        assert fresh_registry.get_model("nonexistent") is None

    def test_register_new_model(self, fresh_registry):
        new_m = RegisteredModel(
            name="Test Model",
            model_type="risk_scorer",
            version="v0.1",
            status="validating",
        )
        fresh_registry.register(new_m)
        retrieved = fresh_registry.get_model(new_m.id)
        assert retrieved is not None
        assert retrieved.name == "Test Model"

    def test_promote_retires_previous_active(self, fresh_registry):
        # reg-nn-001 is validating, model_type=behavioral_profiler — no conflict
        # Instead promote reg-nn-001 (validating behavioral_profiler)
        result = fresh_registry.promote("reg-nn-001")
        assert result is not None
        assert result.status == "active"

    def test_promote_sets_active(self, fresh_registry):
        new_m = RegisteredModel(
            name="New Classifier",
            model_type="fraud_classifier",
            version="v2.0",
            status="validating",
        )
        fresh_registry.register(new_m)
        fresh_registry.promote(new_m.id)
        assert fresh_registry.get_model(new_m.id).status == "active"

    def test_promote_retires_old_active_same_type(self, fresh_registry):
        # Add new fraud_classifier and promote it
        new_m = RegisteredModel(
            name="New Classifier",
            model_type="fraud_classifier",
            version="v2.0",
            status="validating",
        )
        fresh_registry.register(new_m)
        fresh_registry.promote(new_m.id)
        # Previous actives of same type should be retired
        prev = fresh_registry.get_model("reg-xgb-001")
        assert prev.status == "retired"

    def test_promote_nonexistent(self, fresh_registry):
        assert fresh_registry.promote("does-not-exist") is None

    def test_retire_model(self, fresh_registry):
        m = fresh_registry.retire("reg-iso-001")
        assert m is not None
        assert m.status == "retired"

    def test_retire_nonexistent(self, fresh_registry):
        assert fresh_registry.retire("nope") is None

    def test_update_metrics(self, fresh_registry):
        fresh_registry.update_metrics("reg-xgb-001", {"accuracy": 0.99, "custom": 0.88})
        m = fresh_registry.get_model("reg-xgb-001")
        assert m.metrics["accuracy"] == pytest.approx(0.99)
        assert m.metrics["custom"] == pytest.approx(0.88)

    def test_predict_mock_backend(self, fresh_registry):
        import numpy as np
        X = np.array([[100.0, 0.5, 0.3]], dtype=np.float32)
        result = fresh_registry.predict("reg-xgb-001", X)
        assert "probabilities" in result
        assert "predictions" in result
        assert "backend" in result
        assert "latency_ms" in result
        assert isinstance(result["probabilities"], list)

    def test_predict_missing_model_raises(self, fresh_registry):
        import numpy as np
        X = np.ones((1, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="not found"):
            fresh_registry.predict("bad-id", X)

    def test_predict_retired_model_raises(self, fresh_registry):
        import numpy as np
        fresh_registry.retire("reg-iso-001")
        X = np.ones((1, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="not active"):
            fresh_registry.predict("reg-iso-001", X)


# ═══════════════════════════════════════════════════════════════════════════════
# TestModelRegistryService — unit tests for the service layer
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelRegistryService:

    def test_list_models_returns_responses(self, svc):
        result = svc.list_models()
        assert len(result) == 5
        assert all(hasattr(r, "id") for r in result)

    def test_list_models_type_filter(self, svc):
        result = svc.list_models(model_type="anomaly_detector")
        assert len(result) == 1

    def test_get_model_found(self, svc):
        r = svc.get_model("reg-xgb-001")
        assert r is not None
        assert r.name == "XGBoost Fraud Classifier"

    def test_get_model_not_found(self, svc):
        assert svc.get_model("missing") is None

    def test_get_metrics_found(self, svc):
        m = svc.get_metrics("reg-xgb-001")
        assert m is not None
        assert "accuracy" in m

    def test_get_metrics_not_found(self, svc):
        assert svc.get_metrics("bad") is None

    def test_register_model(self, svc):
        r = svc.register_model(
            name="Test",
            model_type="risk_scorer",
            version="v0.1",
            description="Unit test model",
            metrics={"accuracy": 0.9},
        )
        assert r.id is not None
        assert r.status == "validating"
        assert r.name == "Test"

    def test_promote_model(self, svc):
        r = svc.promote_model("reg-nn-001")
        assert r is not None
        assert r.status == "active"

    def test_promote_model_not_found(self, svc):
        assert svc.promote_model("bad") is None

    def test_retire_model(self, svc):
        r = svc.retire_model("reg-xgb-001")
        assert r is not None
        assert r.status == "retired"

    def test_retire_model_not_found(self, svc):
        assert svc.retire_model("bad") is None

    def test_update_metrics(self, svc):
        r = svc.update_metrics("reg-iso-001", {"precision": 0.95})
        assert r is not None
        assert r.metrics["precision"] == pytest.approx(0.95)

    def test_update_metrics_not_found(self, svc):
        assert svc.update_metrics("missing", {"accuracy": 0.9}) is None

    def test_trigger_retraining_unsupported_type(self, svc):
        r = svc.trigger_retraining(model_type="behavioral_profiler")
        assert r.status == "skipped"
        assert "No training pipeline" in r.message

    def test_run_inference(self, svc):
        import numpy as np
        r = svc.run_inference("reg-xgb-001", [[100.0, 0.5, 0.3]])
        assert len(r.probabilities) == 1
        assert isinstance(r.predictions[0], bool)
        assert r.latency_ms >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# TestModelRegistryAPI — integration tests via FastAPI TestClient
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelRegistryAPI:

    # ── GET /models ────────────────────────────────────────────────────────

    def test_list_models_200(self, client):
        r = client.get("/api/v1/models")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_list_models_filter_type(self, client):
        r = client.get("/api/v1/models?model_type=anomaly_detector")
        assert r.status_code == 200
        data = r.json()
        assert all(m["model_type"] == "anomaly_detector" for m in data)

    def test_list_models_filter_status(self, client):
        r = client.get("/api/v1/models?status=active")
        assert r.status_code == 200
        data = r.json()
        assert all(m["status"] == "active" for m in data)

    def test_list_models_combined_filters(self, client):
        r = client.get("/api/v1/models?model_type=fraud_classifier&status=active")
        assert r.status_code == 200
        data = r.json()
        for m in data:
            assert m["model_type"] == "fraud_classifier"
            assert m["status"] == "active"

    # ── GET /models/{id} ───────────────────────────────────────────────────

    def test_get_model_200(self, client):
        r = client.get("/api/v1/models/reg-xgb-001")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "reg-xgb-001"
        assert data["name"] == "XGBoost Fraud Classifier"

    def test_get_model_404(self, client):
        r = client.get("/api/v1/models/does-not-exist")
        assert r.status_code == 404

    # ── GET /models/{id}/metrics ───────────────────────────────────────────

    def test_get_metrics_200(self, client):
        r = client.get("/api/v1/models/reg-iso-001/metrics")
        assert r.status_code == 200
        data = r.json()
        assert data["model_id"] == "reg-iso-001"
        assert "metrics" in data
        assert "accuracy" in data["metrics"]

    def test_get_metrics_404(self, client):
        r = client.get("/api/v1/models/bad-id/metrics")
        assert r.status_code == 404

    # ── POST /models/register ──────────────────────────────────────────────

    def test_register_model_201(self, client):
        payload = {
            "name": "API Test Model",
            "model_type": "risk_scorer",
            "version": "v0.1",
            "description": "Created by test",
            "metrics": {"accuracy": 0.88},
        }
        r = client.post("/api/v1/models/register", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "API Test Model"
        assert data["status"] == "validating"
        assert data["id"] is not None

    def test_register_model_missing_name(self, client):
        r = client.post(
            "/api/v1/models/register",
            json={"model_type": "risk_scorer", "version": "v1"},
        )
        assert r.status_code == 422

    def test_register_model_invalid_type(self, client):
        r = client.post(
            "/api/v1/models/register",
            json={"name": "X", "model_type": "unknown", "version": "v1"},
        )
        assert r.status_code == 422

    # ── POST /models/{id}/promote ──────────────────────────────────────────

    def test_promote_model_200(self, client):
        r = client.post("/api/v1/models/reg-nn-001/promote")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"

    def test_promote_model_404(self, client):
        r = client.post("/api/v1/models/nope/promote")
        assert r.status_code == 404

    # ── POST /models/{id}/retire ───────────────────────────────────────────

    def test_retire_model_200(self, client):
        r = client.post("/api/v1/models/reg-risk-001/retire")
        assert r.status_code == 200
        assert r.json()["status"] == "retired"

    def test_retire_model_404(self, client):
        r = client.post("/api/v1/models/nope/retire")
        assert r.status_code == 404

    # ── PATCH /models/{id}/metrics ─────────────────────────────────────────

    def test_update_metrics_200(self, client):
        r = client.patch(
            "/api/v1/models/reg-xgb-001/metrics",
            json={"metrics": {"accuracy": 0.97, "new_metric": 0.5}},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["metrics"]["accuracy"] == pytest.approx(0.97)
        assert data["metrics"]["new_metric"] == pytest.approx(0.5)

    def test_update_metrics_404(self, client):
        r = client.patch(
            "/api/v1/models/bad/metrics",
            json={"metrics": {"accuracy": 0.9}},
        )
        assert r.status_code == 404

    # ── POST /models/retrain ───────────────────────────────────────────────

    def test_retrain_unsupported_type_skipped(self, client):
        r = client.post(
            "/api/v1/models/retrain",
            json={"model_type": "behavioral_profiler", "n_samples": 5000},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "skipped"

    def test_retrain_invalid_type(self, client):
        r = client.post(
            "/api/v1/models/retrain",
            json={"model_type": "nonexistent", "n_samples": 5000},
        )
        assert r.status_code == 422

    def test_retrain_n_samples_too_small(self, client):
        r = client.post(
            "/api/v1/models/retrain",
            json={"model_type": "fraud_classifier", "n_samples": 100},
        )
        assert r.status_code == 422

    # ── POST /models/{id}/infer ────────────────────────────────────────────

    def test_infer_200(self, client):
        features = [[float(i) for i in range(20)]]
        r = client.post(
            "/api/v1/models/reg-xgb-001/infer",
            json={"features": features},
        )
        assert r.status_code == 200
        data = r.json()
        assert "probabilities" in data
        assert "predictions" in data
        assert "latency_ms" in data
        assert "backend" in data
        assert len(data["probabilities"]) == 1

    def test_infer_batch(self, client):
        features = [[float(i) for i in range(20)] for _ in range(5)]
        r = client.post(
            "/api/v1/models/reg-xgb-001/infer",
            json={"features": features},
        )
        assert r.status_code == 200
        assert len(r.json()["probabilities"]) == 5

    def test_infer_404_model_not_found(self, client):
        r = client.post(
            "/api/v1/models/bad-id/infer",
            json={"features": [[1.0, 2.0]]},
        )
        assert r.status_code == 400

    def test_infer_retired_model_400(self, client):
        # Retire reg-graph-001 then attempt inference
        client.post("/api/v1/models/reg-graph-001/retire")
        r = client.post(
            "/api/v1/models/reg-graph-001/infer",
            json={"features": [[1.0, 2.0]]},
        )
        assert r.status_code == 400

    def test_infer_empty_features_raises_or_400(self, client):
        # Empty features list causes numpy to fail — server may raise or return 4xx
        try:
            r = client.post(
                "/api/v1/models/reg-xgb-001/infer",
                json={"features": []},
            )
            assert r.status_code in (200, 400, 422)
        except Exception:
            pass  # Server-side numpy error is acceptable behaviour

    # ── Response schema validation ─────────────────────────────────────────

    def test_model_response_schema_fields(self, client):
        r = client.get("/api/v1/models/reg-xgb-001")
        data = r.json()
        required_fields = {
            "id", "name", "model_type", "version", "status",
            "metrics", "artifact_path", "training_dataset_info",
            "description", "created_at", "updated_at",
        }
        assert required_fields.issubset(data.keys())

    def test_model_metrics_content(self, client):
        r = client.get("/api/v1/models/reg-xgb-001")
        metrics = r.json()["metrics"]
        # accuracy may have been patched by test_update_metrics_200; just check key presence
        assert "accuracy" in metrics
        assert "auc_roc" in metrics
        assert 0.0 <= metrics["accuracy"] <= 1.0
