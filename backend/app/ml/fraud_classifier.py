"""
FinShield AI — Supervised Fraud Classifiers (Layer 3)
=======================================================
Trains and serves:
  • XGBoost   — primary fraud classifier (handles class imbalance)
  • Random Forest — ensemble stability, feature importance
  • Neural Network (sklearn MLP) -> exportable to ONNX-like pkl

The FraudClassifier class wraps all three and returns individual
and ensemble supervised scores (0–1 probability of fraud).
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

import xgboost as xgb


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class FraudClassifier:
    """
    Three-model supervised fraud classifier.

    Training:
        clf = FraudClassifier()
        clf.fit(X_train, y_train)
        clf.save()

    Inference:
        clf = FraudClassifier.load()
        scores = clf.predict_proba(X)         # shape (n, )  fraud probabilities
        detail = clf.predict_detailed(X)      # dict with per-model scores
    """

    def __init__(self, scale_pos_weight: float = 32.0):
        """
        scale_pos_weight: ratio of negative:positive samples.
        For 3% fraud rate: ~32 (97/3 ≈ 32).
        """
        self.scale_pos_weight = scale_pos_weight
        self.scaler = StandardScaler()

        self.xgb_model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="aucpr",
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

        self.nn_model = MLPClassifier(
            hidden_layer_sizes=(256, 128, 64),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=256,
            learning_rate="adaptive",
            max_iter=100,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10,
        )

        self._fitted = False
        self.feature_importances_: np.ndarray | None = None

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FraudClassifier":
        """
        Fit all three classifiers.

        Parameters
        ----------
        X : feature matrix (n_samples, n_features)
        y : binary labels (0 = legit, 1 = fraud)
        """
        X_scaled = self.scaler.fit_transform(X)

        print(f"  [XGB] Training XGBoost (fraud: {y.sum()}, legit: {(1-y).sum()})...")
        self.xgb_model.fit(X_scaled, y)

        print("  [RF]  Training Random Forest...")
        self.rf_model.fit(X_scaled, y)

        print("  [NN]  Training Neural Network...")
        self.nn_model.fit(X_scaled, y)

        # Store combined feature importances (XGB + RF average)
        xgb_fi = self.xgb_model.feature_importances_
        rf_fi = self.rf_model.feature_importances_
        self.feature_importances_ = (xgb_fi + rf_fi) / 2

        self._fitted = True
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Returns fraud probability for each sample (0–1).
        Weighted ensemble: XGB 50% + RF 30% + NN 20%.
        """
        if not self._fitted:
            raise RuntimeError("FraudClassifier not fitted.")

        X_scaled = self.scaler.transform(X)
        xgb_p = self.xgb_model.predict_proba(X_scaled)[:, 1]
        rf_p = self.rf_model.predict_proba(X_scaled)[:, 1]
        nn_p = self.nn_model.predict_proba(X_scaled)[:, 1]

        return np.clip(0.50 * xgb_p + 0.30 * rf_p + 0.20 * nn_p, 0, 1).astype(np.float32)

    def predict_detailed(self, X: np.ndarray) -> dict:
        """Returns per-model scores as a dict."""
        if not self._fitted:
            raise RuntimeError("FraudClassifier not fitted.")

        X_scaled = self.scaler.transform(X)
        xgb_p = self.xgb_model.predict_proba(X_scaled)[:, 1]
        rf_p = self.rf_model.predict_proba(X_scaled)[:, 1]
        nn_p = self.nn_model.predict_proba(X_scaled)[:, 1]
        ensemble = np.clip(0.50 * xgb_p + 0.30 * rf_p + 0.20 * nn_p, 0, 1)

        return {
            "xgboost": xgb_p.tolist(),
            "random_forest": rf_p.tolist(),
            "neural_network": nn_p.tolist(),
            "supervised_ensemble": ensemble.tolist(),
        }

    def predict_single(self, x: np.ndarray) -> tuple[float, dict]:
        """Score a single feature vector. Returns (ensemble_score, detail_dict)."""
        d = self.predict_detailed(x.reshape(1, -1))
        return float(d["supervised_ensemble"][0]), {k: v[0] for k, v in d.items()}

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | None = None):
        os.makedirs(MODELS_DIR, exist_ok=True)
        path = path or os.path.join(MODELS_DIR, "fraud_classifier_v1.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Saved FraudClassifier -> {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "FraudClassifier":
        path = path or os.path.join(MODELS_DIR, "fraud_classifier_v1.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)
