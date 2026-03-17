"""
Phase 3 — #12: Anomaly Detection Training Pipeline (F2.2 / F2.8)

Trains an Isolation Forest + Autoencoder (MLP-based) ensemble on synthetic
transaction data.  Isolation Forest detects statistical outliers (unsupervised);
the Autoencoder learns a low-dimensional reconstruction of normal behaviour and
flags high reconstruction-error samples as anomalies.

Usage (standalone):
    cd backend
    python -m app.ml.training.train_anomaly_model [--output-dir models/]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
CONTAMINATION = 0.08          # expected fraction of anomalies
N_FEATURES = 15               # feature set for anomaly model
MODEL_VERSION = f"v{datetime.now(timezone.utc).strftime('%Y%m%d')}.1"


# ── Synthetic data generation ────────────────────────────────────────────────

def generate_normal_transactions(n: int = 9_000) -> np.ndarray:
    """Generate 'normal' transaction feature vectors."""
    rng = np.random.default_rng(RANDOM_STATE)
    return np.column_stack([
        rng.lognormal(4.5, 0.8, n),      # amount
        rng.integers(8, 22, n),           # hour (business hours)
        rng.poisson(3, n),                # count_1h
        rng.lognormal(4.0, 0.7, n),      # sum_1h
        rng.integers(90, 3000, n),        # account_age_days
        rng.beta(1, 20, n),              # historical_fraud_rate
        rng.uniform(0.0, 0.3, n),        # country_risk
        rng.exponential(30, n),           # distance_km
        np.zeros(n),                      # impossible_travel
        rng.choice([0, 1], n, p=[0.9, 0.1]),  # new_device
        rng.beta(1, 15, n),              # ip_risk
        rng.normal(0, 0.4, n),           # amount_deviation
        rng.choice([0, 1], n, p=[0.95, 0.05]),  # unusual_time
        rng.choice([0, 1], n, p=[0.85, 0.15]),  # new_merchant
        rng.beta(1, 10, n),              # prior_risk_score
    ])


def generate_anomalous_transactions(n: int = 1_000) -> np.ndarray:
    """Generate anomalous transaction feature vectors."""
    rng = np.random.default_rng(RANDOM_STATE + 1)
    return np.column_stack([
        rng.lognormal(8.0, 2.0, n),      # very large or very small amounts
        rng.choice([0, 1, 2, 3, 23], n), # unusual hours
        rng.poisson(20, n),              # very high velocity
        rng.lognormal(8.0, 1.5, n),
        rng.integers(1, 14, n),          # very new accounts
        rng.beta(8, 10, n),             # high fraud history
        rng.uniform(0.7, 1.0, n),       # high-risk countries
        rng.exponential(3000, n),        # impossible distances
        rng.choice([0, 1], n, p=[0.2, 0.8]),
        rng.choice([0, 1], n, p=[0.2, 0.8]),
        rng.beta(8, 4, n),
        rng.normal(5, 3, n),            # extreme amount deviation
        rng.choice([0, 1], n, p=[0.2, 0.8]),
        rng.choice([0, 1], n, p=[0.3, 0.7]),
        rng.beta(6, 5, n),
    ])


# ── Isolation Forest ──────────────────────────────────────────────────────────

def train_isolation_forest(X_normal: np.ndarray) -> IsolationForest:
    """F2.2 — Train Isolation Forest on normal data only (unsupervised)."""
    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        max_features=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_normal)
    return model


# ── Autoencoder ───────────────────────────────────────────────────────────────

class TransactionAutoencoder:
    """
    F2.2 — MLP-based autoencoder that learns to reconstruct normal transactions.
    High reconstruction error → anomaly.
    """

    def __init__(self, n_features: int = N_FEATURES, latent_dim: int = 5):
        self.n_features = n_features
        self.latent_dim = latent_dim
        self.scaler = StandardScaler()
        # Encoder + Decoder implemented as one MLPRegressor (input → bottleneck → output)
        self.model = MLPRegressor(
            hidden_layer_sizes=(32, latent_dim, 32),
            activation="relu",
            max_iter=500,
            random_state=RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1,
            tol=1e-4,
        )
        self.threshold_: float = 0.0

    def fit(self, X: np.ndarray) -> "TransactionAutoencoder":
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, X_scaled)
        recon = self.model.predict(X_scaled)
        errors = np.mean((X_scaled - recon) ** 2, axis=1)
        # Threshold = 95th percentile of normal reconstruction errors
        self.threshold_ = float(np.percentile(errors, 95))
        return self

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        recon = self.model.predict(X_scaled)
        return np.mean((X_scaled - recon) ** 2, axis=1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly probability (0 = normal, 1 = anomaly)."""
        errors = self.reconstruction_error(X)
        # Normalise: scores > threshold are anomalous
        return np.clip(errors / (self.threshold_ * 2), 0.0, 1.0)


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_ensemble(
    iso_forest: IsolationForest,
    autoencoder: TransactionAutoencoder,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict:
    """Evaluate the combined anomaly detector on labelled test data."""
    # Isolation Forest: -1 = anomaly, 1 = normal → convert to 0/1 proba
    iso_scores = -iso_forest.score_samples(X_test)           # higher = more anomalous
    iso_proba = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-9)

    # Autoencoder scores already in [0, 1]
    ae_proba = autoencoder.score_samples(X_test)

    # Ensemble (equal weight)
    ensemble_proba = (iso_proba * 0.5) + (ae_proba * 0.5)
    ensemble_pred = (ensemble_proba >= 0.5).astype(int)

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    return {
        "accuracy": round(accuracy_score(y_test, ensemble_pred), 4),
        "precision": round(precision_score(y_test, ensemble_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, ensemble_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, ensemble_pred, zero_division=0), 4),
        "auc_roc": round(roc_auc_score(y_test, ensemble_proba), 4),
        "auc_pr": round(average_precision_score(y_test, ensemble_proba), 4),
        "n_test_samples": len(y_test),
        "n_anomaly_test": int(y_test.sum()),
        "autoencoder_threshold": round(autoencoder.threshold_, 6),
    }


# ── Main training orchestrator ────────────────────────────────────────────────

def run_training(output_dir: str = "models/", n_normal: int = 9_000, n_anomaly: int = 1_000) -> Dict:
    """
    End-to-end anomaly detection training.

    Steps:
        1. Generate synthetic normal + anomalous transactions
        2. Train Isolation Forest (unsupervised, on normal only)
        3. Train Autoencoder (reconstruction, on normal only)
        4. Evaluate ensemble on held-out labelled test set
        5. Serialise artifacts
        6. Return metrics for the model registry
    """
    start = time.time()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[train_anomaly] Generating data ({n_normal} normal, {n_anomaly} anomalous) …")
    X_normal = generate_normal_transactions(n_normal)
    X_anomaly = generate_anomalous_transactions(n_anomaly)

    X_all = np.vstack([X_normal, X_anomaly])
    y_all = np.array([0] * n_normal + [1] * n_anomaly)

    # Split before training to avoid data leakage
    X_train_norm, X_test_norm, _, _ = train_test_split(
        X_normal, np.zeros(n_normal), test_size=0.2, random_state=RANDOM_STATE
    )
    X_test = np.vstack([X_test_norm, X_anomaly])
    y_test = np.array([0] * len(X_test_norm) + [1] * n_anomaly)

    print("[train_anomaly] Training Isolation Forest …")
    iso_forest = train_isolation_forest(X_train_norm)

    print("[train_anomaly] Training Autoencoder …")
    autoencoder = TransactionAutoencoder(n_features=N_FEATURES)
    autoencoder.fit(X_train_norm)

    print("[train_anomaly] Evaluating ensemble …")
    metrics = evaluate_ensemble(iso_forest, autoencoder, X_test, y_test)

    # Persist
    artifact_base = out / f"anomaly_detector_{MODEL_VERSION}"
    joblib.dump(iso_forest, artifact_base.with_suffix(".iso_forest.joblib"))
    joblib.dump(autoencoder, artifact_base.with_suffix(".autoencoder.joblib"))

    metrics["version"] = MODEL_VERSION
    metrics["trained_at"] = datetime.now(timezone.utc).isoformat()
    metrics["duration_s"] = round(time.time() - start, 2)
    metrics["artifact_path"] = str(artifact_base)
    metrics["n_train_samples"] = len(X_train_norm)

    metrics_path = artifact_base.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2))

    print(
        f"[train_anomaly] Done in {metrics['duration_s']}s — "
        f"AUC-ROC={metrics['auc_roc']} F1={metrics['f1']}"
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train anomaly detector (F2.2)")
    parser.add_argument("--output-dir", default="models/")
    parser.add_argument("--n-normal", type=int, default=9_000)
    parser.add_argument("--n-anomaly", type=int, default=1_000)
    args = parser.parse_args()
    result = run_training(args.output_dir, args.n_normal, args.n_anomaly)
    print(json.dumps(result, indent=2))
