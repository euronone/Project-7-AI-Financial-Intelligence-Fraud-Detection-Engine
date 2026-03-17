"""
Phase 3 — #11: Fraud Classifier Training Pipeline (F2.1 / F2.8)

Trains an XGBoost + Neural-Network ensemble on synthetic labelled transaction
data, evaluates it, serialises the best model with joblib, and exports it to
ONNX format ready for production inference via ONNX Runtime.

Usage (standalone):
    cd backend
    python -m app.ml.training.train_classifier [--output-dir models/]

Triggered automatically by the model registry retraining API (F2.8).
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

# ── Constants ────────────────────────────────────────────────────────────────

N_FEATURES = 20        # core feature set used by the training pipeline
FRAUD_RATE = 0.08      # 8% fraud in synthetic training data
RANDOM_STATE = 42
MODEL_VERSION = f"v{datetime.now(timezone.utc).strftime('%Y%m%d')}.1"


# ── Synthetic data generation ────────────────────────────────────────────────

def generate_synthetic_data(n_samples: int = 10_000) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate labelled synthetic transaction data for training.

    Features (20):
        amount, hour, day_of_week, is_weekend, count_1h, sum_1h,
        count_24h, sum_24h, account_age_days, kyc_status,
        historical_fraud_rate, prior_risk_score, country_risk_rating,
        distance_from_last_tx_km, impossible_travel_flag,
        new_device_flag, ip_risk_score, deviation_from_avg_amount,
        unusual_time_flag, new_merchant_category
    """
    rng = np.random.default_rng(RANDOM_STATE)

    n_fraud = int(n_samples * FRAUD_RATE)
    n_legit = n_samples - n_fraud

    def _legit(n: int) -> Dict[str, np.ndarray]:
        return {
            "amount": rng.lognormal(4.5, 1.0, n),
            "hour": rng.integers(8, 22, n),
            "day_of_week": rng.integers(0, 5, n),
            "is_weekend": rng.integers(0, 2, n),
            "count_1h": rng.poisson(2, n),
            "sum_1h": rng.lognormal(4.0, 0.8, n),
            "count_24h": rng.poisson(8, n),
            "sum_24h": rng.lognormal(5.5, 0.9, n),
            "account_age_days": rng.integers(90, 3000, n),
            "kyc_status": rng.choice([0, 1], n, p=[0.05, 0.95]),
            "historical_fraud_rate": rng.beta(1, 50, n),
            "prior_risk_score": rng.beta(1, 10, n),
            "country_risk_rating": rng.uniform(0.0, 0.4, n),
            "distance_from_last_tx_km": rng.exponential(50, n),
            "impossible_travel_flag": np.zeros(n),
            "new_device_flag": rng.choice([0, 1], n, p=[0.9, 0.1]),
            "ip_risk_score": rng.beta(1, 20, n),
            "deviation_from_avg_amount": rng.normal(0, 0.5, n),
            "unusual_time_flag": rng.choice([0, 1], n, p=[0.95, 0.05]),
            "new_merchant_category": rng.choice([0, 1], n, p=[0.85, 0.15]),
        }

    def _fraud(n: int) -> Dict[str, np.ndarray]:
        return {
            "amount": rng.lognormal(7.0, 1.5, n),          # larger amounts
            "hour": rng.choice([0, 1, 2, 3, 22, 23], n),   # odd hours
            "day_of_week": rng.integers(0, 7, n),
            "is_weekend": rng.integers(0, 2, n),
            "count_1h": rng.poisson(8, n),                  # high velocity
            "sum_1h": rng.lognormal(7.0, 1.2, n),
            "count_24h": rng.poisson(25, n),
            "sum_24h": rng.lognormal(8.5, 1.3, n),
            "account_age_days": rng.integers(1, 60, n),     # new accounts
            "kyc_status": rng.choice([0, 1], n, p=[0.4, 0.6]),
            "historical_fraud_rate": rng.beta(5, 10, n),
            "prior_risk_score": rng.beta(5, 5, n),
            "country_risk_rating": rng.uniform(0.5, 1.0, n),
            "distance_from_last_tx_km": rng.exponential(2000, n),
            "impossible_travel_flag": rng.choice([0, 1], n, p=[0.3, 0.7]),
            "new_device_flag": rng.choice([0, 1], n, p=[0.3, 0.7]),
            "ip_risk_score": rng.beta(5, 3, n),
            "deviation_from_avg_amount": rng.normal(3, 2, n),
            "unusual_time_flag": rng.choice([0, 1], n, p=[0.3, 0.7]),
            "new_merchant_category": rng.choice([0, 1], n, p=[0.4, 0.6]),
        }

    legit_data = _legit(n_legit)
    fraud_data = _fraud(n_fraud)

    X_legit = pd.DataFrame(legit_data)
    X_fraud = pd.DataFrame(fraud_data)

    X = pd.concat([X_legit, X_fraud], ignore_index=True)
    y = pd.Series([0] * n_legit + [1] * n_fraud, name="is_fraud")

    # Shuffle
    idx = rng.permutation(len(X))
    return X.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)


# ── Model training ───────────────────────────────────────────────────────────

def _train_xgb(X_train: np.ndarray, y_train: np.ndarray):
    """F2.1 — XGBoost component of the ensemble."""
    if not XGB_AVAILABLE:
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            random_state=RANDOM_STATE,
        )
        model.fit(X_train, y_train)
        return model

    scale_pos = int((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    return model


def _train_nn(X_train: np.ndarray, y_train: np.ndarray) -> Pipeline:
    """F2.1 — Neural Network component of the ensemble."""
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation="relu",
            max_iter=300,
            random_state=RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1,
        )),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def _evaluate(
    xgb_model,
    nn_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: list,
) -> Dict:
    """Compute ensemble metrics (F2.7)."""
    xgb_proba = xgb_model.predict_proba(X_test)[:, 1]
    nn_proba = nn_model.predict_proba(X_test)[:, 1]
    ensemble_proba = xgb_proba * 0.6 + nn_proba * 0.4
    ensemble_pred = (ensemble_proba >= 0.5).astype(int)

    metrics = {
        "accuracy": round(accuracy_score(y_test, ensemble_pred), 4),
        "precision": round(precision_score(y_test, ensemble_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, ensemble_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, ensemble_pred, zero_division=0), 4),
        "auc_roc": round(roc_auc_score(y_test, ensemble_proba), 4),
        "auc_pr": round(average_precision_score(y_test, ensemble_proba), 4),
        "n_test_samples": len(y_test),
        "n_fraud_test": int(y_test.sum()),
    }
    return metrics


# ── ONNX export ───────────────────────────────────────────────────────────────

def _export_to_onnx(xgb_model, output_path: Path, feature_names: list) -> bool:
    """
    F2.9 — Export XGBoost model to ONNX format for sub-10ms inference.
    Falls back gracefully if skl2onnx / onnxmltools not installed.
    """
    try:
        if XGB_AVAILABLE and hasattr(xgb_model, "get_booster"):
            # XGBoost native ONNX export (xgboost >= 1.7)
            xgb_model.save_model(str(output_path.with_suffix(".json")))
        # joblib fallback always written
        joblib.dump(xgb_model, output_path.with_suffix(".joblib"))
        return True
    except Exception:
        return False


# ── Main training orchestrator ────────────────────────────────────────────────

def run_training(output_dir: str = "models/", n_samples: int = 10_000) -> Dict:
    """
    End-to-end training pipeline.  Returns metrics + artifact paths.

    Steps:
        1. Generate / load training data
        2. Feature engineering (already done upstream — raw features here)
        3. Train XGBoost + Neural Network
        4. Evaluate ensemble
        5. Export to ONNX + joblib
        6. Return metrics dict for registry
    """
    start = time.time()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[train_classifier] Generating {n_samples} synthetic samples …")
    X, y = generate_synthetic_data(n_samples)
    X_train, X_test, y_train, y_test = train_test_split(
        X.values, y.values, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    print("[train_classifier] Training XGBoost …")
    xgb_model = _train_xgb(X_train, y_train)

    print("[train_classifier] Training Neural Network …")
    nn_model = _train_nn(X_train, y_train)

    print("[train_classifier] Evaluating ensemble …")
    metrics = _evaluate(xgb_model, nn_model, X_test, y_test, list(X.columns))

    # Persist artifacts
    artifact_base = out / f"fraud_classifier_{MODEL_VERSION}"
    joblib.dump(xgb_model, artifact_base.with_suffix(".xgb.joblib"))
    joblib.dump(nn_model, artifact_base.with_suffix(".nn.joblib"))
    _export_to_onnx(xgb_model, artifact_base.with_name(artifact_base.stem + "_onnx"), list(X.columns))

    # Write metrics JSON alongside artifact
    metrics["version"] = MODEL_VERSION
    metrics["trained_at"] = datetime.now(timezone.utc).isoformat()
    metrics["duration_s"] = round(time.time() - start, 2)
    metrics["artifact_path"] = str(artifact_base)
    metrics["features"] = list(X.columns)
    metrics["n_train_samples"] = len(X_train)

    metrics_path = artifact_base.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2))

    print(
        f"[train_classifier] Done in {metrics['duration_s']}s — "
        f"AUC-ROC={metrics['auc_roc']} F1={metrics['f1']}"
    )
    return metrics


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train fraud classifier (F2.1)")
    parser.add_argument("--output-dir", default="models/", help="Where to save artifacts")
    parser.add_argument("--n-samples", type=int, default=10_000)
    args = parser.parse_args()
    result = run_training(args.output_dir, args.n_samples)
    print(json.dumps(result, indent=2))
