"""
FinShield AI — SHAP Explainability
=====================================
Generates SHAP explanations for the XGBoost model.

Usage:
    explainer = SHAPExplainer.build(fraud_classifier, X_train, feature_names)
    explainer.save()

    # At inference:
    explainer = SHAPExplainer.load()
    top_factors = explainer.explain(x, top_n=5)
"""

import os
import pickle
from dataclasses import dataclass

import numpy as np
import shap


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


@dataclass
class FeatureContribution:
    """A single feature's contribution to the fraud score."""

    feature_name: str
    shap_value: float
    feature_value: float
    direction: str  # "increases_risk" | "decreases_risk"


class SHAPExplainer:
    """
    SHAP TreeExplainer wrapper for XGBoost model.
    Provides human-readable top-N fraud factor explanations.
    """

    def __init__(self, explainer: shap.TreeExplainer, feature_names: list[str]):
        self._explainer = explainer
        self.feature_names = feature_names

    # ── Build & save ──────────────────────────────────────────────────────────

    @classmethod
    def build(
        cls,
        fraud_classifier,
        X_background: np.ndarray,
        feature_names: list[str],
    ) -> "SHAPExplainer":
        """
        Build a TreeExplainer from the XGBoost model inside FraudClassifier.

        X_background: a representative sample of training data (scaled).
        """
        print("  [SHAP] Building TreeExplainer on XGBoost model...")
        xgb_model = fraud_classifier.xgb_model
        scaler = fraud_classifier.scaler
        X_scaled = scaler.transform(X_background)

        # Use a sample for background (faster)
        sample_size = min(200, len(X_scaled))
        idx = np.random.choice(len(X_scaled), sample_size, replace=False)
        background = X_scaled[idx]

        explainer = shap.TreeExplainer(xgb_model, background)
        return cls(explainer, feature_names)

    def save(self, path: str | None = None):
        os.makedirs(MODELS_DIR, exist_ok=True)
        path = path or os.path.join(MODELS_DIR, "shap_explainer_v1.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Saved SHAPExplainer -> {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "SHAPExplainer":
        path = path or os.path.join(MODELS_DIR, "shap_explainer_v1.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)

    # ── Inference ─────────────────────────────────────────────────────────────

    def explain(
        self,
        x_scaled: np.ndarray,
        top_n: int = 5,
    ) -> list[FeatureContribution]:
        """
        Explain a single pre-scaled feature vector.
        Returns top_n features by |SHAP value|.
        """
        x2d = x_scaled.reshape(1, -1)
        shap_values = self._explainer.shap_values(x2d)

        # shap_values may be shape (1, n_features) or list for multi-class
        if isinstance(shap_values, list):
            sv = shap_values[1][0]  # positive class
        else:
            sv = shap_values[0] if shap_values.ndim == 2 else shap_values

        feature_vals = x_scaled.flatten()

        # Sort by absolute SHAP value
        indices = np.argsort(np.abs(sv))[::-1][:top_n]

        results = []
        for i in indices:
            name = self.feature_names[i] if i < len(self.feature_names) else f"feat_{i}"
            # Strip "feat_" prefix for readability
            display_name = name.replace("feat_", "")
            results.append(
                FeatureContribution(
                    feature_name=display_name,
                    shap_value=round(float(sv[i]), 4),
                    feature_value=round(float(feature_vals[i]), 4),
                    direction="increases_risk" if sv[i] > 0 else "decreases_risk",
                )
            )

        return results

    def global_importance(self, X_scaled: np.ndarray, top_n: int = 20) -> list[dict]:
        """
        Compute mean |SHAP| across a dataset for global feature importance.
        """
        shap_values = self._explainer.shap_values(X_scaled)
        if isinstance(shap_values, list):
            sv = shap_values[1]
        else:
            sv = shap_values

        mean_abs = np.abs(sv).mean(axis=0)
        indices = np.argsort(mean_abs)[::-1][:top_n]

        return [
            {
                "rank": int(rank + 1),
                "feature": self.feature_names[i].replace("feat_", "")
                if i < len(self.feature_names)
                else f"feat_{i}",
                "mean_abs_shap": round(float(mean_abs[i]), 4),
            }
            for rank, i in enumerate(indices)
        ]
