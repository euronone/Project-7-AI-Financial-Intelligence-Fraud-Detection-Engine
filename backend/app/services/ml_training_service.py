"""
FinShield AI — Custom ML Training Service
==========================================

Orchestrates end-to-end ML model training for a tenant:

  Stage 1 — Data Fetch         : pull transactions + customers from FinShield DB
  Stage 2 — Column Filter      : respect schema-mapping enabled/disabled flags
  Stage 3 — Feature Engineering: call batch_features() from feature_engineering.py
  Stage 4 — Algorithm Training : train each selected algorithm
  Stage 5 — Auto-Optimization  : hyperparameter grid search (supervised models)
  Stage 6 — Ensemble + Evaluate: build weighted ensemble, compute final metrics
  Stage 7 — Persist            : save artifacts + update DB

Running strategy (no Celery):
  • CPU-bound training runs in asyncio's default ThreadPoolExecutor via
    run_in_executor() so it never blocks the FastAPI event loop.
  • Progress is written to the module-level _JOB_CACHE dict (fast reads for
    polling) and flushed to the DB at job completion / failure.
"""

from __future__ import annotations

import asyncio
import logging
import pickle
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, roc_curve
from sklearn.neighbors import LocalOutlierFactor
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import DBSCAN
from sklearn.model_selection import cross_val_score, train_test_split

try:
    from imblearn.over_sampling import SMOTE

    _SMOTE_AVAILABLE = True
except ImportError:
    _SMOTE_AVAILABLE = False
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.ml.feature_engineering import batch_features
from app.models.ml_model import MLModel
from app.models.training_job import TrainingJob

try:
    import xgboost as xgb

    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False

try:
    import lightgbm as lgb

    _LGB_AVAILABLE = True
except ImportError:
    _LGB_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

MODELS_DIR = Path(__file__).resolve().parents[1] / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ml-train")

# In-memory job progress cache (job_id → progress dict)
# Written by background coroutines, read by poll endpoint.
_JOB_CACHE: dict[str, dict] = {}

# ── Algorithm catalogue ────────────────────────────────────────────────────────

ALGORITHM_CATALOGUE = {
    "clustering": [
        {
            "id": "isolation_forest",
            "name": "Isolation Forest",
            "description": (
                "Detects anomalies by isolating data points through random splits. "
                "No fraud labels required — works on any dataset size."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": True,
        },
        {
            "id": "dbscan",
            "name": "DBSCAN Clustering",
            "description": (
                "Groups transactions into dense clusters. Points not belonging "
                "to any cluster are treated as anomalies (fraud candidates)."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": False,
        },
        {
            "id": "lof",
            "name": "Local Outlier Factor",
            "description": (
                "Measures local density deviation of a data point with respect "
                "to its neighbours. Effective for multi-density fraud patterns."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": False,
        },
    ],
    "supervised": [
        {
            "id": "xgboost",
            "name": "XGBoost",
            "description": (
                "Primary fraud classifier. Handles class imbalance via scale_pos_weight. "
                "Typically achieves highest AUC-ROC on tabular fraud data."
            ),
            "library": "xgboost",
            "tunable": True,
            "recommended": True,
            "available": _XGB_AVAILABLE,
        },
        {
            "id": "random_forest",
            "name": "Random Forest",
            "description": (
                "Ensemble of 200 decision trees. Stable, interpretable feature "
                "importance, good resistance to overfitting."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": True,
            "available": True,
        },
        {
            "id": "gradient_boosting",
            "name": "Gradient Boosting",
            "description": (
                "Sequential tree boosting. Excellent at capturing non-linear "
                "interactions; slower to train than XGBoost."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": False,
            "available": True,
        },
        {
            "id": "neural_network",
            "name": "Neural Network (MLP)",
            "description": (
                "Multi-layer perceptron with 3 hidden layers (256→128→64). "
                "Best for large datasets with complex feature interactions."
            ),
            "library": "scikit-learn",
            "tunable": True,
            "recommended": True,
            "available": True,
        },
        {
            "id": "logistic_regression",
            "name": "Logistic Regression",
            "description": (
                "Fast linear baseline. Useful as a sanity-check reference and "
                "for highly regularised / interpretable deployments."
            ),
            "library": "scikit-learn",
            "tunable": False,
            "recommended": False,
            "available": True,
        },
        {
            "id": "lightgbm",
            "name": "LightGBM",
            "description": (
                "Fast gradient boosting on histograms. Excellent on large datasets "
                "where XGBoost may be slower."
            ),
            "library": "lightgbm",
            "tunable": True,
            "recommended": False,
            "available": _LGB_AVAILABLE,
        },
    ],
}

# Hyperparameter grids for auto-optimization (supervised models only)
# Grids are tuned for fraud detection: imbalanced classes, tabular data, high AUC priority
_PARAM_GRIDS: dict[str, list[dict]] = {
    "xgboost": [
        # Grid 1 — fast, good baseline
        {
            "max_depth": 4,
            "learning_rate": 0.1,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 5,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
        },
        # Grid 2 — deeper, slower learning rate (better for imbalanced)
        {
            "max_depth": 6,
            "learning_rate": 0.05,
            "n_estimators": 400,
            "subsample": 0.8,
            "colsample_bytree": 0.7,
            "min_child_weight": 3,
            "reg_alpha": 0.01,
            "reg_lambda": 2.0,
        },
        # Grid 3 — aggressive regularization to prevent overfitting on small fraud sets
        {
            "max_depth": 3,
            "learning_rate": 0.03,
            "n_estimators": 600,
            "subsample": 0.7,
            "colsample_bytree": 0.6,
            "min_child_weight": 10,
            "reg_alpha": 1.0,
            "reg_lambda": 5.0,
        },
    ],
    "random_forest": [
        {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 4, "max_features": "sqrt"},
        {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 2, "max_features": "sqrt"},
        {"n_estimators": 400, "max_depth": None, "min_samples_leaf": 1, "max_features": 0.5},
    ],
    "gradient_boosting": [
        {"n_estimators": 150, "max_depth": 3, "learning_rate": 0.08, "subsample": 0.8},
        {"n_estimators": 250, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.7},
        {"n_estimators": 400, "max_depth": 3, "learning_rate": 0.03, "subsample": 0.6},
    ],
    "neural_network": [
        {"hidden_layer_sizes": (128, 64), "alpha": 0.01, "max_iter": 300, "batch_size": 64},
        {"hidden_layer_sizes": (256, 128, 64), "alpha": 0.001, "max_iter": 400, "batch_size": 128},
        {
            "hidden_layer_sizes": (512, 256, 128),
            "alpha": 0.0001,
            "max_iter": 500,
            "batch_size": 256,
        },
    ],
    "lightgbm": [
        {"num_leaves": 31, "learning_rate": 0.1, "n_estimators": 200},
        {"num_leaves": 63, "learning_rate": 0.05, "n_estimators": 300},
        {"num_leaves": 127, "learning_rate": 0.03, "n_estimators": 400},
    ],
}

_UNSUPERVISED = {"isolation_forest", "dbscan", "lof"}
_SUPERVISED = {
    "xgboost",
    "random_forest",
    "gradient_boosting",
    "neural_network",
    "logistic_regression",
    "lightgbm",
}


# ── Progress helpers ───────────────────────────────────────────────────────────


def _log(job_id: str, msg: str, pct: int | None = None, stage: str | None = None) -> None:
    """Append a log line to the in-memory cache (non-blocking)."""
    entry = _JOB_CACHE.setdefault(job_id, {})
    lines: list = entry.setdefault("log_lines", [])
    lines.append({"ts": datetime.now(timezone.utc).isoformat(), "msg": msg})
    if pct is not None:
        entry["progress_pct"] = pct
    if stage is not None:
        entry["current_stage"] = stage
    logger.debug("[job=%s] %s", job_id, msg)


# ── Sync helpers (run in executor) ────────────────────────────────────────────


def _build_model(algo_id: str, params: dict, spw: float) -> Any:
    """Instantiate a fresh model with given hyperparameters."""
    if algo_id == "xgboost" and _XGB_AVAILABLE:
        return xgb.XGBClassifier(
            **params,
            scale_pos_weight=spw,
            eval_metric="aucpr",
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )
    if algo_id == "random_forest":
        return RandomForestClassifier(
            **params,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
    if algo_id == "gradient_boosting":
        return GradientBoostingClassifier(**params, random_state=42)
    if algo_id == "neural_network":
        return MLPClassifier(**params, early_stopping=True, random_state=42)
    if algo_id == "logistic_regression":
        return LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=42)
    if algo_id == "lightgbm" and _LGB_AVAILABLE:
        return lgb.LGBMClassifier(
            **params,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
    raise ValueError(f"Unknown supervised algorithm: {algo_id}")


def _score_unsupervised(algo_id: str, params: dict, X_all: np.ndarray) -> np.ndarray:
    """
    Fit an unsupervised model and return anomaly scores in [0, 1]
    where 1 = most anomalous (most likely fraud).
    """
    if algo_id == "isolation_forest":
        clf = IsolationForest(**params, random_state=42, n_jobs=-1)
        clf.fit(X_all)
        raw = -clf.score_samples(X_all)  # higher = more anomalous

    elif algo_id == "lof":
        contamination = params.get("contamination", 0.05)
        clf = LocalOutlierFactor(contamination=contamination, n_jobs=-1)
        raw = -clf.fit_predict(X_all).astype(float)  # -1 = outlier → positive
        raw = np.where(raw > 0, 1.0, 0.0)  # binary: outlier or not

    elif algo_id == "dbscan":
        eps = params.get("eps", 1.0)
        min_samples = params.get("min_samples", 5)
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X_all)
        labels = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1).fit_predict(X_scaled)
        raw = (labels == -1).astype(float)  # noise points = anomalous

    else:
        raise ValueError(f"Unknown unsupervised algorithm: {algo_id}")

    # Normalize to [0, 1]
    rng = raw.max() - raw.min()
    return (raw - raw.min()) / (rng + 1e-9) if rng > 1e-9 else raw


def _compute_metrics(
    y_true: np.ndarray, scores: np.ndarray, threshold: float | None = None
) -> dict:
    """Return precision/recall/F1/AUC-ROC for a score array.

    When threshold is None (default), the optimal cut-off is found by
    maximising Youden's J statistic (sensitivity + specificity - 1) on the
    ROC curve.  This is far more reliable than a fixed 0.5 when fraud is rare.
    """
    if len(y_true) == 0 or y_true.sum() == 0:
        return {}
    try:
        auc = float(roc_auc_score(y_true, scores))
    except Exception:
        auc = 0.0

    # Find optimal threshold if not supplied
    if threshold is None:
        try:
            fpr, tpr, thresholds = roc_curve(y_true, scores)
            j_scores = tpr - fpr  # Youden's J = sensitivity + specificity - 1
            best_idx = int(np.argmax(j_scores))
            threshold = float(thresholds[best_idx])
        except Exception:
            threshold = 0.5

    y_pred = (scores >= threshold).astype(int)
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "auc_roc": round(auc, 4),
        "threshold": round(float(threshold), 4),
        "test_samples": int(len(y_true)),
        "fraud_samples": int(y_true.sum()),
    }


def _optimize_supervised(
    algo_id: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    spw: float,
    log_fn: Callable,
) -> dict:
    """
    3-fold CV grid search.  Returns best params found.
    Falls back to default params if CV fails (small dataset, etc.).
    """
    grid = _PARAM_GRIDS.get(algo_id, [])
    if not grid:
        return {}

    best_params: dict = grid[0]
    best_score: float = -1.0

    for i, params in enumerate(grid):
        log_fn(f"  Hyperparameter pass {i+1}/{len(grid)}: {params}")
        try:
            model = _build_model(algo_id, params, spw)
            scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=min(3, max(2, int(y_train.sum() // 5))),
                scoring="roc_auc",
                n_jobs=-1,
                error_score=0.0,
            )
            mean = float(scores.mean())
            log_fn(f"    CV AUC-ROC = {mean:.4f}")
            if mean > best_score:
                best_score = mean
                best_params = params
        except Exception as exc:
            log_fn(f"    Skipped (error: {exc})")

    log_fn(f"  Best params: {best_params}  (CV AUC-ROC={best_score:.4f})")
    return best_params


def _apply_disabled_columns(
    txn_records: list[dict],
    schema_mapping: dict,
) -> list[dict]:
    """
    Zero out fields that the tenant has disabled in their schema mapping.

    When a FinShield canonical field has enabled=False, we set its value to
    None/0 in every txn record so it contributes zero variance to feature
    engineering — effectively excluding it from the model without rewriting
    the feature pipeline.

    Also handles custom columns: if a custom field is marked enabled=True
    and its client_column is present in the records, it is kept as-is.
    If enabled=False, it is zeroed out.
    """
    txn_mapping = schema_mapping.get("transactions", {})
    disabled_fields: set[str] = set()

    for finshield_field, cfg in txn_mapping.items():
        if isinstance(cfg, dict) and not cfg.get("enabled", True):
            disabled_fields.add(finshield_field)

    if not disabled_fields:
        return txn_records

    out: list[dict] = []
    for row in txn_records:
        new_row = dict(row)
        for field in disabled_fields:
            if field in new_row:
                # Use 0 for numerics, empty string for strings
                val = new_row[field]
                if isinstance(val, (int, float)):
                    new_row[field] = 0
                else:
                    new_row[field] = None
        out.append(new_row)
    return out


def _sync_training_pipeline(
    job_id: str,
    algo_ids: list[str],
    txn_records: list[dict],
    cust_records: list[dict],
    auto_optimize: bool,
    schema_mapping: dict | None = None,
    test_size: float = 0.20,
) -> dict:
    """
    CPU-bound training pipeline. Runs in a ThreadPoolExecutor thread.

    Returns a result dict:
    {
        "metrics": { algo_id: {...}, "ensemble": {...} },
        "best_algorithm": str,
        "optimization_rounds": int,
        "feature_count": int,
        "training_samples": int,
        "artifacts": { algo_id: pickle_bytes },
    }

    schema_mapping: when provided (use_custom_columns=True), disabled fields
    are zeroed out before feature engineering so they don't influence the model.
    """

    def log(msg: str, pct: int | None = None, stage: str | None = None):
        _log(job_id, msg, pct, stage)

    # ── Stage 2: Convert to DataFrames (+ apply schema column filter) ─────────
    log("Converting records to DataFrames…", pct=15, stage="Feature Engineering")

    if schema_mapping:
        disabled_fields = {
            f
            for f, cfg in schema_mapping.get("transactions", {}).items()
            if isinstance(cfg, dict) and not cfg.get("enabled", True)
        }
        if disabled_fields:
            log(
                f"  Disabling {len(disabled_fields)} columns per schema mapping: {sorted(disabled_fields)}"
            )
            txn_records = _apply_disabled_columns(txn_records, schema_mapping)

    txn_df = pd.DataFrame(txn_records)
    cust_df = pd.DataFrame(cust_records) if cust_records else None

    if txn_df.empty:
        raise ValueError("No transactions found in the selected window.")

    # Ensure required columns
    if "transaction_timestamp" not in txn_df.columns:
        raise ValueError("transactions table is missing 'transaction_timestamp' column.")

    # ── Stage 3: Feature engineering ─────────────────────────────────────────
    log(f"Engineering features for {len(txn_df):,} transactions…", pct=22)

    # Extract raw labels BEFORE feature engineering (using original DataFrame order)
    has_labels_raw = "fraud_category" in txn_df.columns
    if has_labels_raw:
        y_raw = (txn_df["fraud_category"] == "fraudulent").astype(int).values
    else:
        y_raw = None

    orig_pos: np.ndarray | None = None
    try:
        # batch_features returns (ndarray, feat_cols, orig_pos) where orig_pos
        # holds the original row indices BEFORE the internal sort by
        # [customer_id, timestamp].  We MUST use it to re-align labels.
        result_fe = batch_features(txn_df, cust_df)
        if isinstance(result_fe, tuple):
            X_all = result_fe[0]  # feature matrix (sorted order)
            orig_pos = result_fe[2] if len(result_fe) > 2 else None
        else:
            X_all = result_fe
        X_all = np.array(X_all, dtype=np.float32)
    except Exception as exc:
        log(f"Feature engineering warning: {exc} — using basic numeric features")
        numeric_cols = txn_df.select_dtypes(include=[np.number]).columns.tolist()
        X_all = txn_df[numeric_cols].fillna(0).values.astype(np.float32)
        orig_pos = None

    n_samples, n_features = X_all.shape
    log(f"Feature matrix: {n_samples:,} rows × {n_features} features", pct=30)

    # Re-align labels to match the sorted feature matrix row order
    has_labels = has_labels_raw and y_raw is not None
    if has_labels:
        if orig_pos is not None and len(orig_pos) == n_samples:
            y_all = y_raw[orig_pos]
            log(f"Labels re-aligned via orig_pos ({n_samples:,} rows).")
        else:
            y_all = y_raw
        fraud_count = int(y_all.sum())
        log(f"Labels: {fraud_count} fraud / {n_samples - fraud_count} legitimate")
    else:
        y_all = np.zeros(n_samples, dtype=int)
        has_labels = False
        log("No fraud labels found — generating synthetic labels via Isolation Forest")

        # ── Synthetic label generation ────────────────────────────────────────
        # When no fraud_category column exists, use Isolation Forest anomaly
        # scores to create pseudo-labels so supervised models can still train.
        # The top ~5% most anomalous transactions become pseudo-frauds.
        try:
            _if = IsolationForest(n_estimators=200, contamination=0.05, random_state=42, n_jobs=-1)
            _if.fit(X_all)
            _raw = -_if.score_samples(X_all)
            _threshold = np.percentile(_raw, 95)
            y_all = (_raw >= _threshold).astype(int)
            fraud_count = int(y_all.sum())
            has_labels = fraud_count >= 5
            log(
                f"Synthetic labels: {fraud_count} pseudo-fraud / {n_samples - fraud_count} legitimate (top-5% anomalies)"
            )
        except Exception as exc:
            log(f"Synthetic label generation failed: {exc} — unsupervised only")

    # Scale features — RobustScaler is better for fraud data with outliers
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_all)
    # Clip extreme values after scaling to prevent XGBoost/RF instability
    X_scaled = np.clip(X_scaled, -10, 10)

    # Train/test split (only if we have labels and enough fraud samples)
    do_supervised = any(a in _SUPERVISED for a in algo_ids) and has_labels and fraud_count >= 5
    if do_supervised:
        spw = float(max(1, (n_samples - fraud_count))) / float(max(1, fraud_count))
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_all, test_size=test_size, stratify=y_all, random_state=42
            )
        except ValueError:
            X_train, X_test, y_train, y_test = (X_scaled, X_scaled, y_all, y_all)

        # ── SMOTE oversampling ────────────────────────────────────────────────
        # When fraud samples are rare (< 100 in training), oversample minority
        # class so supervised models see enough fraud examples.
        train_fraud = int(y_train.sum())
        if _SMOTE_AVAILABLE and train_fraud >= 5 and train_fraud < 100:
            try:
                k = min(5, train_fraud - 1)
                smote = SMOTE(random_state=42, k_neighbors=k)
                X_train, y_train = smote.fit_resample(X_train, y_train)
                log(
                    f"SMOTE: oversampled training set to {len(X_train):,} rows ({int(y_train.sum())} fraud)"
                )
            except Exception as exc:
                log(f"SMOTE skipped: {exc}")
        elif not _SMOTE_AVAILABLE and train_fraud < 100:
            log(
                "Tip: install imbalanced-learn (pip install imbalanced-learn) for SMOTE oversampling"
            )

        log(
            f"Train/test split: {len(X_train):,}/{len(X_test):,}  "
            f"({int((1-test_size)*100)}/{int(test_size*100)} split, "
            f"scale_pos_weight={spw:.1f})"
        )
    else:
        spw = 10.0
        X_train = X_test = X_scaled
        y_train = y_test = y_all

    # ── Stage 4: Train algorithms ─────────────────────────────────────────────
    algo_models: dict[str, Any] = {}
    algo_scores: dict[str, np.ndarray] = {}
    algo_metrics: dict[str, dict] = {}
    n_algos = len(algo_ids)

    for idx, algo_id in enumerate(algo_ids):
        base_pct = 30 + int(35 * idx / n_algos)
        log(f"Training {algo_id}…", pct=base_pct, stage=f"Training {algo_id}")

        try:
            if algo_id in _UNSUPERVISED:
                # Determine contamination from label ratio
                contamination = max(0.01, min(0.4, float(y_all.mean()) or 0.05))
                default_params: dict = {"contamination": contamination, "n_estimators": 150}
                scores_all = _score_unsupervised(algo_id, default_params, X_scaled)
                m = _compute_metrics(y_all, scores_all) if has_labels and fraud_count >= 5 else {}
                # Unsupervised models score on the full dataset (X_scaled), while
                # supervised models score only on X_test. When both are selected,
                # keep unsupervised out of algo_scores to prevent shape mismatch
                # in the ensemble (they still appear in algo_metrics for display).
                if not do_supervised:
                    algo_scores[algo_id] = scores_all
                algo_metrics[algo_id] = m
                algo_models[algo_id] = {"type": "unsupervised", "params": default_params}
                log(
                    f"  {algo_id} done. "
                    + (f"AUC-ROC={m.get('auc_roc','n/a')}" if m else "No labels to evaluate.")
                )

            elif algo_id in _SUPERVISED and do_supervised:
                default_params = (_PARAM_GRIDS.get(algo_id) or [{}])[0]
                model = _build_model(algo_id, default_params, spw)
                model.fit(X_train, y_train)
                scores = model.predict_proba(X_test)[:, 1]
                algo_scores[algo_id] = scores
                m = _compute_metrics(y_test, scores)
                algo_metrics[algo_id] = m
                algo_models[algo_id] = model
                log(
                    f"  {algo_id} done.  "
                    f"AUC-ROC={m.get('auc_roc','n/a')}  "
                    f"F1={m.get('f1_score','n/a')}"
                )
            else:
                log(f"  Skipping {algo_id} (needs labels / not available)")

        except Exception as exc:
            log(f"  {algo_id} FAILED: {exc}")
            algo_metrics[algo_id] = {"error": str(exc)}

    # ── Stage 5: Auto-optimize supervised models ──────────────────────────────
    opt_rounds = 0
    if auto_optimize and do_supervised:
        log("Auto-optimizing hyperparameters…", pct=68, stage="Optimizing")
        supervised_selected = [a for a in algo_ids if a in _SUPERVISED and a in algo_models]

        for algo_id in supervised_selected:
            log(f"Optimizing {algo_id}…")
            try:
                best_params = _optimize_supervised(
                    algo_id,
                    X_train,
                    y_train,
                    spw,
                    log_fn=lambda m, a=algo_id: _log(job_id, m),
                )
                # Retrain with best params
                model = _build_model(algo_id, best_params, spw)
                model.fit(X_train, y_train)
                scores = model.predict_proba(X_test)[:, 1]
                new_m = _compute_metrics(y_test, scores)

                # Only replace if improved
                old_auc = algo_metrics.get(algo_id, {}).get("auc_roc", 0.0)
                new_auc = new_m.get("auc_roc", 0.0)
                if new_auc >= old_auc:
                    algo_metrics[algo_id] = {**new_m, "best_params": best_params}
                    algo_models[algo_id] = model
                    algo_scores[algo_id] = scores
                    log(f"  {algo_id} improved: " f"AUC-ROC {old_auc:.4f} → {new_auc:.4f}")
                else:
                    log(f"  {algo_id} original params better, keeping.")
                opt_rounds += 1
            except Exception as exc:
                log(f"  Optimization failed for {algo_id}: {exc}")

    # ── Stage 6: Ensemble scoring ─────────────────────────────────────────────
    log("Building ensemble…", pct=88, stage="Evaluating")
    scored_algos = {
        a: s for a, s in algo_scores.items() if a in algo_metrics and "auc_roc" in algo_metrics[a]
    }

    ensemble_metrics: dict = {}
    if scored_algos:
        # Weight by AUC-ROC (uniform if no labels)
        weights: dict[str, float] = {}
        for a, s in scored_algos.items():
            auc = algo_metrics[a].get("auc_roc", 0.5)
            weights[a] = max(0.1, auc)
        total_w = sum(weights.values())
        norm_weights = {a: w / total_w for a, w in weights.items()}

        # Ensemble score (weighted average on the TEST set)
        ensemble_score = np.zeros(len(next(iter(scored_algos.values()))))
        for a, s in scored_algos.items():
            ensemble_score += norm_weights[a] * s

        ensemble_metrics = _compute_metrics(y_test, ensemble_score) if has_labels else {}
        ensemble_metrics["weights"] = {a: round(w, 4) for a, w in norm_weights.items()}
        log(
            f"  Ensemble AUC-ROC={ensemble_metrics.get('auc_roc','n/a')}  "
            f"Precision={ensemble_metrics.get('precision','n/a')}  "
            f"Recall={ensemble_metrics.get('recall','n/a')}"
        )

    # ── Determine best algorithm ──────────────────────────────────────────────
    best_algo = max(
        (a for a in algo_metrics if "auc_roc" in algo_metrics[a]),
        key=lambda a: algo_metrics[a].get("auc_roc", 0.0),
        default=algo_ids[0] if algo_ids else "ensemble",
    )

    # ── Serialize artifacts (pickle) ──────────────────────────────────────────
    log("Serializing model artifacts…", pct=94)
    artifacts: dict[str, bytes] = {}
    for algo_id, model in algo_models.items():
        if hasattr(model, "predict"):
            try:
                artifacts[algo_id] = pickle.dumps(
                    {"model": model, "scaler": scaler, "feature_count": n_features},
                    protocol=4,
                )
            except Exception:
                pass

    all_metrics = {**algo_metrics, "ensemble": ensemble_metrics}

    return {
        "metrics": all_metrics,
        "best_algorithm": best_algo,
        "optimization_rounds": opt_rounds,
        "feature_count": n_features,
        "training_samples": n_samples,
        "artifacts": artifacts,
    }


# ── Service class ──────────────────────────────────────────────────────────────


class MLTrainingService:
    """Async service facade — called from API route handlers."""

    # ── Start a new training job ───────────────────────────────────────────────
    @staticmethod
    async def start_job(
        tenant_id: str,
        algorithms: list[str],
        data_window_days: int,
        auto_optimize: bool,
        use_custom_columns: bool,
        parent_job_id: str | None = None,
        test_size: float = 0.20,
    ) -> TrainingJob:
        """
        Create a TrainingJob record, seed the in-memory cache, and
        fire off the background training coroutine.
        """
        job_id = str(uuid.uuid4())

        async with AsyncSessionLocal() as db:
            job = TrainingJob(
                id=job_id,
                tenant_id=tenant_id,
                selected_algorithms=algorithms,
                data_window_days=data_window_days,
                auto_optimize=auto_optimize,
                use_custom_columns=use_custom_columns,
                parent_job_id=parent_job_id,
                status="queued",
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

        _JOB_CACHE[job_id] = {
            "status": "queued",
            "progress_pct": 0,
            "current_stage": "Queued — waiting to start",
            "log_lines": [],
            "metrics": {},
            "best_algorithm": None,
        }

        # Launch in background (does not block request handler)
        asyncio.create_task(
            MLTrainingService._run_training_bg(
                job_id=job_id,
                tenant_id=tenant_id,
                algorithms=algorithms,
                data_window_days=data_window_days,
                auto_optimize=auto_optimize,
                use_custom_columns=use_custom_columns,
                test_size=test_size,
            )
        )

        return job

    # ── Re-optimize with a larger data window ──────────────────────────────────
    @staticmethod
    async def reoptimize_job(
        parent_job_id: str,
        tenant_id: str,
        new_window_days: int,
    ) -> TrainingJob:
        """
        Clone the configuration of an existing job and re-run with a wider
        data window. Returns the new child job.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(TrainingJob).where(TrainingJob.id == parent_job_id))
            parent = result.scalar_one_or_none()
            if not parent:
                raise ValueError(f"Job {parent_job_id} not found")

        return await MLTrainingService.start_job(
            tenant_id=tenant_id,
            algorithms=parent.selected_algorithms or ["xgboost", "isolation_forest"],
            data_window_days=new_window_days,
            auto_optimize=True,
            use_custom_columns=parent.use_custom_columns,
            parent_job_id=parent_job_id,
        )

    # ── List jobs for a tenant ─────────────────────────────────────────────────
    @staticmethod
    async def list_jobs(tenant_id: str, limit: int = 20) -> list[dict]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.tenant_id == tenant_id)
                .order_by(TrainingJob.created_at.desc())
                .limit(limit)
            )
            jobs = result.scalars().all()

        out = []
        for j in jobs:
            live = _JOB_CACHE.get(j.id, {})
            out.append(
                {
                    "job_id": j.id,
                    "status": live.get("status") or j.status,
                    "progress_pct": live.get("progress_pct") or j.progress_pct,
                    "current_stage": live.get("current_stage") or j.current_stage,
                    "algorithms": j.selected_algorithms or [],
                    "data_window_days": j.data_window_days,
                    "auto_optimize": j.auto_optimize,
                    "best_algorithm": live.get("best_algorithm") or j.best_algorithm,
                    "training_samples": j.training_samples,
                    "result_model_id": j.result_model_id,
                    "parent_job_id": j.parent_job_id,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                }
            )
        return out

    # ── Poll a single job ──────────────────────────────────────────────────────
    @staticmethod
    async def get_job_status(job_id: str, tenant_id: str) -> dict:
        """
        Returns live progress from the in-memory cache if the job is running,
        otherwise re-reads from the DB.
        """
        live = _JOB_CACHE.get(job_id)
        if live and live.get("status") in ("running", "queued", "optimizing", "evaluating"):
            return {**live, "job_id": job_id}

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.id == job_id,
                    TrainingJob.tenant_id == tenant_id,
                )
            )
            job = result.scalar_one_or_none()
            if not job:
                raise ValueError(f"Job {job_id} not found")

        return {
            "job_id": job.id,
            "status": job.status,
            "progress_pct": job.progress_pct,
            "current_stage": job.current_stage,
            "log_lines": job.log_lines or [],
            "metrics": job.metrics_json or {},
            "best_algorithm": job.best_algorithm,
            "training_samples": job.training_samples,
            "feature_count": job.feature_count,
            "result_model_id": job.result_model_id,
            "optimization_rounds": job.optimization_rounds,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    # ── Promote trained job → active MLModel ─────────────────────────────────
    @staticmethod
    async def promote_job(job_id: str, tenant_id: str) -> MLModel:
        """
        Save the best artifact from a completed job as an active MLModel row,
        retiring the previous active model for this tenant.
        """
        async with AsyncSessionLocal() as db:
            job_res = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.id == job_id,
                    TrainingJob.tenant_id == tenant_id,
                )
            )
            job = job_res.scalar_one_or_none()
            if not job:
                raise ValueError("Job not found")
            if job.status != "completed":
                raise ValueError(f"Job is not completed (status={job.status})")

            metrics = job.metrics_json or {}
            ensemble_m = metrics.get("ensemble", {})
            best_algo = job.best_algorithm or "ensemble"

            # Retire current active model for this tenant
            active_res = await db.execute(
                select(MLModel).where(
                    MLModel.tenant_id == tenant_id,
                    MLModel.is_active == True,  # noqa: E712
                )
            )
            for m in active_res.scalars().all():
                m.is_active = False

            # Create new active model
            version = f"custom_v{int(datetime.now(timezone.utc).timestamp())}"
            new_model = MLModel(
                tenant_id=tenant_id,
                model_name=f"Custom Ensemble ({', '.join(job.selected_algorithms or [])})",
                model_type="ensemble",
                version=version,
                status="active",
                precision=ensemble_m.get("precision"),
                recall=ensemble_m.get("recall"),
                f1_score=ensemble_m.get("f1_score"),
                auc_roc=ensemble_m.get("auc_roc"),
                training_samples=job.training_samples,
                is_active=True,
                promoted_at=datetime.now(timezone.utc),
                artifact_path=str(MODELS_DIR / f"{version}.pkl"),
                feature_importance=metrics.get(best_algo, {}).get("best_params"),
            )
            db.add(new_model)
            job.result_model_id = new_model.id

            await db.commit()
            await db.refresh(new_model)

        return new_model

    # ── Pickle upload ─────────────────────────────────────────────────────────
    @staticmethod
    async def register_uploaded_pickle(
        file_bytes: bytes,
        filename: str,
        tenant_id: str,
    ) -> dict:
        """
        Validate and register an uploaded .pkl model file.
        Returns model metadata without persisting a full training job.
        """
        try:
            payload = pickle.loads(file_bytes)  # noqa: S301 — file is user-controlled
        except Exception as exc:
            raise ValueError(f"Cannot unpickle file: {exc}") from exc

        # Accept both raw model objects and our wrapped {"model": ..., "scaler": ...} dicts
        if isinstance(payload, dict):
            model = payload.get("model")
        else:
            model = payload

        if not hasattr(model, "predict"):
            raise ValueError(
                "Uploaded file does not contain a valid sklearn-compatible model "
                "(object must have a .predict() method)."
            )

        model_name = filename.replace(".pkl", "").replace("_", " ").title()
        version = f"uploaded_v{int(datetime.now(timezone.utc).timestamp())}"

        # Save to disk
        save_path = MODELS_DIR / f"uploaded_{version}.pkl"
        save_path.write_bytes(file_bytes)

        async with AsyncSessionLocal() as db:
            # Retire existing active model
            active_res = await db.execute(
                select(MLModel).where(
                    MLModel.tenant_id == tenant_id,
                    MLModel.is_active == True,  # noqa: E712
                )
            )
            for m in active_res.scalars().all():
                m.is_active = False

            new_model = MLModel(
                tenant_id=tenant_id,
                model_name=model_name,
                model_type="fraud_classifier",
                version=version,
                status="active",
                is_active=True,
                promoted_at=datetime.now(timezone.utc),
                artifact_path=str(save_path),
            )
            db.add(new_model)
            await db.commit()
            await db.refresh(new_model)

        return {
            "model_id": new_model.id,
            "model_name": model_name,
            "version": version,
            "message": f"Model '{model_name}' registered and set as active.",
        }

    # ── Background training coroutine ─────────────────────────────────────────
    @staticmethod
    async def _run_training_bg(
        job_id: str,
        tenant_id: str,
        algorithms: list[str],
        data_window_days: int,
        auto_optimize: bool,
        use_custom_columns: bool,
        test_size: float = 0.20,
    ) -> None:
        """
        Runs as an asyncio task.
        1. Fetches data (async DB)
        2. Delegates CPU work to the ThreadPoolExecutor
        3. Persists results
        """
        cache = _JOB_CACHE.setdefault(job_id, {})
        cache.update({"status": "running", "progress_pct": 2, "current_stage": "Starting"})

        try:
            # ── Update job started_at ────────────────────────────────────────
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "running"
                    job.started_at = datetime.now(timezone.utc)
                    await db.commit()

            # ── Auto data refresh (if schedule = on_training_start) ──────────
            from app.models.user import Tenant

            schema_mapping: dict | None = None

            async with AsyncSessionLocal() as db:
                tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                tenant_obj = tenant_res.scalar_one_or_none()
                if tenant_obj:
                    schema_mapping = tenant_obj.schema_mapping_json or {}
                    tenant_config = tenant_obj.db_config_json or {}
                    refresh_mode = tenant_config.get("data_refresh", {}).get("mode", "manual")
                else:
                    tenant_config = {}
                    refresh_mode = "manual"

            if refresh_mode == "on_training_start" and tenant_config.get("data_refresh"):
                _log(
                    job_id,
                    "Auto data refresh triggered (mode=on_training_start)…",
                    pct=4,
                    stage="Data Refresh",
                )
                try:
                    from app.services.data_sync_service import DataSyncService

                    refresh_cfg = tenant_config["data_refresh"]
                    sync_stats = await DataSyncService.run_sync(
                        tenant_id=tenant_id,
                        tables=refresh_cfg.get("tables", ["transactions", "customers"]),
                        row_limit=refresh_cfg.get("row_limit", 100_000),
                        incremental=True,
                    )
                    synced_txn = (
                        sync_stats.get("tables", {}).get("transactions", {}).get("upserted", 0)
                    )
                    synced_cst = (
                        sync_stats.get("tables", {}).get("customers", {}).get("upserted", 0)
                    )
                    _log(
                        job_id,
                        f"  Data refresh complete: {synced_txn:,} transactions, {synced_cst:,} customers synced.",
                        pct=7,
                    )
                    if sync_stats.get("errors"):
                        _log(job_id, f"  Sync warnings: {sync_stats['errors']}")
                except Exception as sync_exc:
                    _log(job_id, f"  Data refresh warning (non-fatal): {sync_exc}")

            # ── Stage 1: Fetch data from FinShield internal DB ───────────────
            _log(job_id, "Fetching transactions from database…", pct=8, stage="Fetching Data")

            from app.models.transaction import Transaction
            from app.models.customer import Customer

            async with AsyncSessionLocal() as db:
                txn_query = select(Transaction).where(
                    Transaction.tenant_id == tenant_id,
                    Transaction.is_test == False,  # noqa: E712
                )
                if data_window_days and data_window_days > 0:
                    from datetime import timedelta

                    cutoff = datetime.now(timezone.utc) - timedelta(days=data_window_days)
                    txn_query = txn_query.where(Transaction.transaction_timestamp >= cutoff)

                txn_res = await db.execute(txn_query.limit(100_000))
                txn_objs = txn_res.scalars().all()

                cust_res = await db.execute(
                    select(Customer).where(Customer.tenant_id == tenant_id).limit(10_000)
                )
                cust_objs = cust_res.scalars().all()

            _log(
                job_id,
                f"Loaded {len(txn_objs):,} transactions, {len(cust_objs):,} customers.",
                pct=14,
            )

            # Serialise ORM objects to plain dicts BEFORE leaving the session scope
            def _txn_to_dict(t: Transaction) -> dict:
                return {
                    "transaction_id": t.id,
                    "customer_id": t.customer_id,
                    "amount": float(t.amount or 0),
                    "currency": t.currency or "INR",
                    "transaction_type": t.transaction_type or "purchase",
                    "channel": t.channel or "online",
                    "merchant_name": t.merchant_name or "",
                    "merchant_category_code": t.merchant_category_code or "",
                    "transaction_timestamp": t.transaction_timestamp,
                    "location_lat": float(t.location_lat or 0),
                    "location_lng": float(t.location_lng or 0),
                    "city": t.city or "",
                    "country_code": t.country_code or "IN",
                    "ip_address": str(t.ip_address or ""),
                    "device_fingerprint": t.device_fingerprint or "",
                    "device_type": t.device_type or "unknown",
                    "status": t.status or "completed",
                    "fraud_score": float(t.fraud_score or 0),
                    "fraud_category": t.fraud_category or "unscored",
                    "is_flagged": bool(t.is_flagged),
                    "is_blocked": bool(t.is_blocked),
                }

            def _cust_to_dict(c: Customer) -> dict:
                return {
                    "customer_id": c.id,
                    "risk_score": float(c.risk_score or 0.1),
                    "customer_tier": c.customer_tier or "standard",
                    "balance_amount": float(c.balance_amount or 50000),
                    "account_opening_date": c.account_opening_date,
                    "kyc_level": c.kyc_verification_level or "basic",
                    "profile_type": c.account_type or "personal",
                }

            txn_records = [_txn_to_dict(t) for t in txn_objs]
            cust_records = [_cust_to_dict(c) for c in cust_objs]

            if not txn_records:
                raise ValueError(
                    f"No transactions found in the last {data_window_days} days. "
                    "Try a wider data window or run the seed script."
                )

            # ── Stages 2-6: CPU-bound training in executor ────────────────────
            # Pass schema_mapping only when use_custom_columns=True so the
            # pipeline can zero out disabled fields before feature engineering.
            effective_schema = schema_mapping if use_custom_columns else None

            loop = asyncio.get_event_loop()
            result: dict = await loop.run_in_executor(
                _EXECUTOR,
                lambda: _sync_training_pipeline(
                    job_id=job_id,
                    algo_ids=algorithms,
                    txn_records=txn_records,
                    cust_records=cust_records,
                    auto_optimize=auto_optimize,
                    schema_mapping=effective_schema,
                    test_size=test_size,
                ),
            )

            # ── Stage 7: Save artifacts to disk ───────────────────────────────
            _log(job_id, "Saving model artifacts…", pct=96, stage="Saving")
            for algo_id, artifact_bytes in result.get("artifacts", {}).items():
                path = MODELS_DIR / f"job_{job_id}_{algo_id}.pkl"
                path.write_bytes(artifact_bytes)
                _log(job_id, f"  Saved {algo_id} → {path.name}")

            # ── Persist to DB ─────────────────────────────────────────────────
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "completed"
                    job.progress_pct = 100
                    job.current_stage = "Completed"
                    job.metrics_json = result["metrics"]
                    job.best_algorithm = result["best_algorithm"]
                    job.optimization_rounds = result["optimization_rounds"]
                    job.training_samples = result["training_samples"]
                    job.feature_count = result["feature_count"]
                    job.log_lines = cache.get("log_lines", [])
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()

            cache.update(
                {
                    "status": "completed",
                    "progress_pct": 100,
                    "current_stage": "Completed",
                    "metrics": result["metrics"],
                    "best_algorithm": result["best_algorithm"],
                }
            )
            _log(
                job_id,
                f"✓ Training complete. Best algorithm: {result['best_algorithm']}",
            )

        except Exception as exc:
            err = str(exc)
            logger.exception("Training job %s failed: %s", job_id, err)
            cache.update(
                {
                    "status": "failed",
                    "current_stage": "Failed",
                    "error_message": err,
                }
            )
            _log(job_id, f"✗ Job failed: {err}")

            async with AsyncSessionLocal() as db:
                res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.current_stage = "Failed"
                    job.error_message = err
                    job.log_lines = cache.get("log_lines", [])
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
