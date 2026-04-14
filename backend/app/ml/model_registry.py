"""
FinShield AI — Model Registry
================================
Tracks model versions, metrics, and artifact paths.
Persists to JSON file (also syncs with Supabase ml_models table when available).
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
REGISTRY_FILE = os.path.join(MODELS_DIR, "model_registry.json")


class ModelRegistry:
    """
    Simple file-based model registry.

    Stores metadata for each trained model version:
      - model_type, version, status, metrics, artifact paths
    """

    def __init__(self):
        self._registry: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE) as f:
                return json.load(f)
        return {"models": []}

    def _save(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self._registry, f, indent=2, default=str)

    # ── Register ──────────────────────────────────────────────────────────────

    def register(
        self,
        model_name: str,
        model_type: str,
        version: str,
        artifact_path: str,
        metrics: dict,
        tenant_id: Optional[str] = None,
        status: str = "active",
    ) -> dict:
        """
        Register a trained model in the registry.

        Returns the registry entry dict.
        """
        entry = {
            "id": f"{model_name}_{version}",
            "tenant_id": tenant_id,
            "model_name": model_name,
            "model_type": model_type,
            "version": version,
            "status": status,
            "artifact_path": artifact_path,
            "precision": round(metrics.get("precision", 0.0), 4),
            "recall": round(metrics.get("recall", 0.0), 4),
            "f1_score": round(metrics.get("f1_score", 0.0), 4),
            "auc_roc": round(metrics.get("auc_roc", 0.0), 4),
            "false_positive_rate": round(metrics.get("false_positive_rate", 0.0), 4),
            "training_samples": metrics.get("training_samples", 0),
            "feature_count": metrics.get("feature_count", 0),
            "promoted_at": datetime.now(timezone.utc).isoformat() if status == "active" else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mark any previous versions of same model as retired
        for m in self._registry["models"]:
            if m["model_name"] == model_name and m["status"] == "active":
                m["status"] = "retired"

        self._registry["models"].append(entry)
        self._save()
        return entry

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_active(self, model_name: str) -> Optional[dict]:
        """Get the currently active version of a model."""
        for m in reversed(self._registry["models"]):
            if m["model_name"] == model_name and m["status"] == "active":
                return m
        return None

    def list_all(self) -> list[dict]:
        return list(reversed(self._registry["models"]))

    def get_summary(self) -> dict:
        """Summary for dashboard display."""
        active_models = [m for m in self._registry["models"] if m["status"] == "active"]
        return {
            "total_versions": len(self._registry["models"]),
            "active_models": len(active_models),
            "models": active_models,
        }

    def print_summary(self):
        """Print a table of all registered models."""
        print("\n  MODEL REGISTRY")
        print("  " + "-" * 80)
        print(f"  {'Name':<30} {'Version':<10} {'Status':<10} {'F1':<8} {'AUC-ROC'}")
        print("  " + "-" * 80)
        for m in self._registry["models"]:
            f1 = f"{m.get('f1_score', 0):.3f}"
            auc = f"{m.get('auc_roc', 0):.3f}"
            print(f"  {m['model_name']:<30} {m['version']:<10} {m['status']:<10} {f1:<8} {auc}")
        print()
