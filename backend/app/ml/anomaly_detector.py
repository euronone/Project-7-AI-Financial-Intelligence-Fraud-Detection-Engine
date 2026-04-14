"""
FinShield AI — Unsupervised Anomaly Detection (Layer 2)
=========================================================
Trains and runs:
  • Isolation Forest  — statistical outlier detection
  • DBSCAN            — density-based clustering (loner = anomaly)

Both models produce anomaly_score (0–1, higher = more anomalous).
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class AnomalyDetector:
    """
    Wraps Isolation Forest + DBSCAN.

    Training:
        detector = AnomalyDetector()
        detector.fit(X_train)   # X_train: legitimate transactions preferred
        detector.save()

    Inference:
        detector = AnomalyDetector.load()
        score = detector.score(x)   # returns float 0–1
    """

    def __init__(self, contamination: float = 0.03):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        self.dbscan = DBSCAN(eps=1.2, min_samples=10, n_jobs=-1)
        self._fitted = False

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, X: np.ndarray) -> "AnomalyDetector":
        """Fit both models on training feature matrix."""
        X_scaled = self.scaler.fit_transform(X)

        print("  [IF] Training Isolation Forest...")
        self.isolation_forest.fit(X_scaled)

        print("  [DB] Training DBSCAN...")
        # DBSCAN on a sample for memory efficiency (10k rows is fine)
        sample_size = min(5000, len(X_scaled))
        idx = np.random.choice(len(X_scaled), sample_size, replace=False)
        self.dbscan.fit(X_scaled[idx])
        self._dbscan_train_X = X_scaled[idx]  # kept for inference comparison

        self._fitted = True
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Returns anomaly scores in [0, 1] for each row.
        1.0 = most anomalous, 0.0 = most normal.
        """
        if not self._fitted:
            raise RuntimeError("AnomalyDetector not fitted. Call fit() or load() first.")

        X_scaled = self.scaler.transform(X)

        # Isolation Forest: raw score in (-1, 0) -> rescale to [0, 1]
        if_raw = self.isolation_forest.score_samples(X_scaled)  # negative
        if_score = 1 - (if_raw - if_raw.min()) / (if_raw.max() - if_raw.min() + 1e-9)

        # DBSCAN: measure distance to nearest training cluster center
        # Use average distance to nearest 5 training points
        db_scores = np.zeros(len(X_scaled))
        for i, x in enumerate(X_scaled):
            dists = np.linalg.norm(self._dbscan_train_X - x, axis=1)
            db_scores[i] = np.mean(np.sort(dists)[:5])

        db_score_norm = np.clip(db_scores / (db_scores.max() + 1e-9), 0, 1)

        # Weighted combination: IF 60% + DBSCAN 40%
        combined = 0.60 * if_score + 0.40 * db_score_norm
        return np.clip(combined, 0, 1).astype(np.float32)

    def score_single(self, x: np.ndarray) -> float:
        """Score a single feature vector."""
        return float(self.score(x.reshape(1, -1))[0])

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | None = None):
        os.makedirs(MODELS_DIR, exist_ok=True)
        path = path or os.path.join(MODELS_DIR, "anomaly_detector_v1.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Saved AnomalyDetector -> {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "AnomalyDetector":
        path = path or os.path.join(MODELS_DIR, "anomaly_detector_v1.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)
