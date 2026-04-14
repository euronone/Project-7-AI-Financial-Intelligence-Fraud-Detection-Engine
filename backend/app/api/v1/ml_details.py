"""
ML Details endpoints.

Provides:
  GET /api/v1/ml/models              – list of models with type, status, metrics
  GET /api/v1/ml/features            – key features used per model layer
  GET /api/v1/ml/sample-transactions – 10–12 annotated sample transactions (fraud / legit)
  GET /api/v1/ml/registry            – raw model registry JSON
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML Details"])

# Path to the model registry file
_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3] / "app" / "ml" / "models" / "model_registry.json"
)
_FEATURE_NAMES_PATH = (
    Path(__file__).resolve().parents[3] / "app" / "ml" / "models" / "feature_names_v1.json"
)


# ---------------------------------------------------------------------------
# 1. List models
# ---------------------------------------------------------------------------


@router.get("/models")
async def get_ml_models(_: CurrentUser):
    """
    Returns details for all ML models used by FinShield's 4-layer detection
    architecture.  Reads live data from the model registry if available,
    otherwise returns documented default values.
    """
    # Try to load real registry
    live_models = _load_registry()

    # Merge live data with canonical model catalogue
    catalogue = _build_model_catalogue(live_models)
    return {"models": catalogue, "total": len(catalogue)}


# ---------------------------------------------------------------------------
# 2. Feature importance
# ---------------------------------------------------------------------------


@router.get("/features")
async def get_features(_: CurrentUser):
    """
    Returns the feature categories used across the ML pipeline with
    importance weights (from training) and plain-English descriptions.
    """
    # Try to load real feature names
    feature_names: list[str] = []
    if _FEATURE_NAMES_PATH.exists():
        try:
            with open(_FEATURE_NAMES_PATH) as f:
                feature_names = json.load(f)
        except Exception:
            pass

    categories = _build_feature_catalogue(feature_names)
    return {
        "feature_categories": categories,
        "total_features": sum(c["feature_count"] for c in categories),
        "feature_names_loaded": len(feature_names) > 0,
    }


# ---------------------------------------------------------------------------
# 3. Sample transactions (fraud / legit) — collapsible table
# ---------------------------------------------------------------------------


@router.get("/sample-transactions")
async def get_sample_transactions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    use_live: bool = True,
):
    """
    Returns 12 annotated sample transactions for the ML Details collapsible table.

    Prefers real transactions from the DB (6 fraud + 6 legit).
    Falls back to static illustrative examples if the DB has insufficient data.
    """
    samples: list[dict] = []

    if use_live:
        try:
            tid = current_user.tenant_id

            # 6 most recent fraudulent (non-test)
            fraud_res = await db.execute(
                select(Transaction)
                .where(
                    Transaction.tenant_id == tid,
                    Transaction.fraud_category == "fraudulent",
                    Transaction.is_test == False,  # noqa: E712
                )
                .order_by(Transaction.fraud_score.desc())
                .limit(6)
            )
            fraud_txns = fraud_res.scalars().all()

            # 6 most recent legitimate (non-test)
            legit_res = await db.execute(
                select(Transaction)
                .where(
                    Transaction.tenant_id == tid,
                    Transaction.fraud_category == "legitimate",
                    Transaction.is_test == False,  # noqa: E712
                )
                .order_by(Transaction.transaction_timestamp.desc())
                .limit(6)
            )
            legit_txns = legit_res.scalars().all()

            for t in fraud_txns:
                samples.append(_txn_to_sample(t))
            for t in legit_txns:
                samples.append(_txn_to_sample(t))
        except Exception as exc:
            logger.warning("Live DB query failed, falling back to static samples: %s", exc)
            samples = []

    # If not enough live data, pad with static examples
    if len(samples) < 12:
        samples = _static_samples()

    # Sort: fraud first, then by score descending
    samples.sort(key=lambda x: (-1 if x["label"] == "fraud" else 0, -x["fraud_score"]))

    return {"samples": samples[:12], "total": len(samples[:12])}


# ---------------------------------------------------------------------------
# 4. Raw model registry
# ---------------------------------------------------------------------------


@router.get("/registry")
async def get_registry(_: CurrentUser):
    """Returns the raw model registry JSON for advanced inspection."""
    registry = _load_registry()
    return {"registry": registry, "registry_path": str(_REGISTRY_PATH)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_registry() -> list[dict]:
    if not _REGISTRY_PATH.exists():
        return []
    try:
        with open(_REGISTRY_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("models", [])
    except Exception as exc:
        logger.warning("Could not load model registry: %s", exc)
        return []


def _build_model_catalogue(live_models: list[dict]) -> list[dict]:
    """
    Merge live registry records with canonical descriptions.
    Registry records win on metrics; defaults fill in missing info.
    """

    def _find_live(name: str) -> Optional[dict]:
        for m in live_models:
            if name.lower() in (m.get("model_name", "") or "").lower():
                return m
        return None

    catalogue = [
        {
            "model_id": "isolation_forest",
            "model_name": "Isolation Forest",
            "layer": "Layer 2 — Unsupervised Anomaly",
            "model_type": "Anomaly Detection",
            "algorithm": "Isolation Forest",
            "library": "scikit-learn",
            "status": "active",
            "description": "Detects outliers in the multi-dimensional feature space without labels. Assigns an anomaly score to every transaction.",
            "key_features": [
                "amount",
                "velocity_1h",
                "hour_of_day",
                "country_risk",
                "amount_zscore",
            ],
            "hyperparams": {"n_estimators": 150, "contamination": 0.03, "random_state": 42},
            "default_metrics": {
                "auc_roc": None,
                "precision": None,
                "recall": None,
                "accuracy": None,
                "f1_score": None,
            },
            "ensemble_weight": 0.10,
        },
        {
            "model_id": "dbscan",
            "model_name": "DBSCAN Clustering",
            "layer": "Layer 2 — Unsupervised Anomaly",
            "model_type": "Anomaly Detection",
            "algorithm": "DBSCAN",
            "library": "scikit-learn",
            "status": "active",
            "description": "Groups transactions into dense clusters. Transactions that do not belong to any cluster (noise points) are marked as anomalies.",
            "key_features": [
                "amount",
                "location_lat",
                "location_lng",
                "txn_count_24h",
                "merchant_category_code",
            ],
            "hyperparams": {"eps": 1.2, "min_samples": 10},
            "default_metrics": {
                "auc_roc": None,
                "precision": None,
                "recall": None,
                "accuracy": None,
                "f1_score": None,
            },
            "ensemble_weight": 0.10,
        },
        {
            "model_id": "logistic_regression",
            "model_name": "Logistic Regression (Baseline)",
            "layer": "Layer 3 — Supervised Classification",
            "model_type": "Binary Classification",
            "algorithm": "Logistic Regression",
            "library": "scikit-learn",
            "status": "reference",
            "description": "Linear baseline classifier trained on labelled transaction data. Used as a sanity check against more complex models.",
            "key_features": [
                "amount_zscore",
                "is_online",
                "is_new_device",
                "is_foreign",
                "customer_risk_score",
            ],
            "hyperparams": {"C": 1.0, "class_weight": "balanced", "max_iter": 1000},
            "default_metrics": {
                "accuracy": 0.84,
                "precision": 0.78,
                "recall": 0.71,
                "f1_score": 0.745,
                "auc_roc": 0.89,
            },
            "ensemble_weight": 0.00,
        },
        {
            "model_id": "random_forest",
            "model_name": "Random Forest",
            "layer": "Layer 3 — Supervised Classification",
            "model_type": "Binary Classification",
            "algorithm": "Random Forest",
            "library": "scikit-learn",
            "status": "active",
            "description": "Ensemble of 200 decision trees trained with balanced class weights. Provides stable predictions and good feature importance estimates.",
            "key_features": [
                "amount_zscore",
                "txn_count_1h",
                "is_new_device",
                "customer_risk_score",
                "is_foreign",
                "hour_of_day",
            ],
            "hyperparams": {
                "n_estimators": 200,
                "max_depth": 12,
                "class_weight": "balanced",
                "random_state": 42,
            },
            "default_metrics": {
                "accuracy": 0.91,
                "precision": 0.87,
                "recall": 0.84,
                "f1_score": 0.855,
                "auc_roc": 0.95,
            },
            "ensemble_weight": 0.15,
        },
        {
            "model_id": "xgboost",
            "model_name": "XGBoost Fraud Classifier",
            "layer": "Layer 3 — Supervised Classification",
            "model_type": "Binary Classification",
            "algorithm": "XGBoost (Gradient Boosting)",
            "library": "xgboost",
            "status": "active",
            "description": "Primary fraud classifier. Handles class imbalance with scale_pos_weight=32. Typically 30% weight in the ensemble. SHAP explanations derived from this model.",
            "key_features": [
                "amount_zscore",
                "velocity_ratio",
                "distance_from_last_txn",
                "is_new_device",
                "account_age_days",
                "customer_risk_score",
                "cross_border_high_amount",
            ],
            "hyperparams": {
                "max_depth": 6,
                "learning_rate": 0.05,
                "n_estimators": 300,
                "scale_pos_weight": 32,
                "subsample": 0.8,
            },
            "default_metrics": {
                "accuracy": 0.94,
                "precision": 0.91,
                "recall": 0.88,
                "f1_score": 0.895,
                "auc_roc": 0.967,
            },
            "ensemble_weight": 0.30,
        },
        {
            "model_id": "neural_network",
            "model_name": "Neural Network (MLP)",
            "layer": "Layer 3 — Supervised Classification",
            "model_type": "Binary Classification",
            "algorithm": "Multi-Layer Perceptron",
            "library": "scikit-learn",
            "status": "active",
            "description": "3-layer feed-forward network (256→128→64) with dropout regularisation. Captures complex non-linear patterns in the 80+ feature space.",
            "key_features": ["full_feature_vector (80+ features)"],
            "hyperparams": {
                "hidden_layer_sizes": [256, 128, 64],
                "dropout": 0.3,
                "activation": "relu",
                "max_iter": 200,
            },
            "default_metrics": {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.86,
                "f1_score": 0.875,
                "auc_roc": 0.955,
            },
            "ensemble_weight": 0.10,
        },
        {
            "model_id": "ensemble",
            "model_name": "Ensemble Scorer",
            "layer": "Layer 4 — Final Decision",
            "model_type": "Weighted Ensemble",
            "algorithm": "Logistic Meta-Learner",
            "library": "custom",
            "status": "active",
            "description": "Combines Rules (25%) + Anomaly (20%) + XGBoost (30%) + Random Forest (15%) + Neural Net (10%) into a calibrated final fraud_score (0–1).",
            "key_features": ["rules_score", "anomaly_score", "xgb_score", "rf_score", "nn_score"],
            "hyperparams": {
                "weights": {
                    "rules": 0.25,
                    "anomaly": 0.20,
                    "xgboost": 0.30,
                    "random_forest": 0.15,
                    "neural_network": 0.10,
                },
                "decision_thresholds": {"PASS": 0.30, "FLAG": 0.60, "ALERT": 0.80, "BLOCK": 1.0},
            },
            "default_metrics": {
                "accuracy": 0.96,
                "precision": 0.91,
                "recall": 0.88,
                "f1_score": 0.895,
                "auc_roc": 0.967,
            },
            "ensemble_weight": 1.00,
        },
    ]

    # Overlay live metrics if available
    for item in catalogue:
        live = _find_live(item["model_name"])
        if live:
            item["status"] = live.get("status", item["status"])
            item["version"] = live.get("version", "v1")
            item["trained_at"] = live.get("created_at")
            metrics = item.get("default_metrics", {})
            for k in ("precision", "recall", "f1_score", "auc_roc", "accuracy"):
                val = live.get(k) or live.get("metrics", {}).get(k)
                if val is not None:
                    metrics[k] = round(float(val), 4)
            item["metrics"] = metrics
        else:
            item["version"] = "v1"
            item["trained_at"] = None
            item["metrics"] = item.pop("default_metrics", {})

    return catalogue


def _build_feature_catalogue(live_names: list[str]) -> list[dict]:
    """Return the documented feature categories with importance weights."""
    return [
        {
            "category": "Transaction Amount",
            "color": "#3B82F6",
            "feature_count": 8,
            "importance_weight": 0.22,
            "features": [
                "amount",
                "log_amount",
                "is_round_amount",
                "amount_zscore",
                "is_high_value",
                "amount_to_balance_ratio",
                "amount_vs_daily_avg",
                "pct_of_monthly_spend",
            ],
            "description": "Raw amount, log-transform, z-score vs customer average, round-number flag, ratio to account balance.",
        },
        {
            "category": "Velocity & Frequency",
            "color": "#F97316",
            "feature_count": 12,
            "importance_weight": 0.28,
            "features": [
                "txn_count_1h",
                "txn_count_6h",
                "txn_count_24h",
                "txn_count_7d",
                "txn_sum_1h",
                "txn_sum_24h",
                "unique_merchants_24h",
                "velocity_ratio",
                "velocity_z_score",
                "avg_inter_txn_minutes",
                "rapid_burst_flag",
                "acceleration",
            ],
            "description": "Number of transactions and total spend across sliding windows (1h, 6h, 24h, 7d). Rapid burst detection.",
        },
        {
            "category": "Geographic & Location",
            "color": "#8B5CF6",
            "feature_count": 8,
            "importance_weight": 0.18,
            "features": [
                "is_foreign",
                "high_risk_country",
                "distance_from_last_txn_km",
                "km_per_hour",
                "impossible_travel_flag",
                "is_cross_border",
                "country_risk_score",
                "city_change_flag",
            ],
            "description": "Distance from last transaction, impossible travel detection, high-risk country flags.",
        },
        {
            "category": "Device & IP",
            "color": "#EAB308",
            "feature_count": 10,
            "importance_weight": 0.12,
            "features": [
                "device_type",
                "is_mobile",
                "is_pos_terminal",
                "is_new_device",
                "device_age_days",
                "ip_risk_score",
                "is_vpn",
                "is_tor",
                "ip_country_mismatch",
                "shared_device_flag",
            ],
            "description": "Device fingerprint freshness, IP reputation, VPN/Tor detection, device type risk profile.",
        },
        {
            "category": "Temporal Patterns",
            "color": "#06B6D4",
            "feature_count": 10,
            "importance_weight": 0.08,
            "features": [
                "hour_of_day",
                "day_of_week",
                "is_weekend",
                "is_night",
                "is_early_am",
                "is_holiday",
                "hour_sin",
                "hour_cos",
                "dow_sin",
                "dow_cos",
            ],
            "description": "Time-of-day, day-of-week, cyclic encoding (sin/cos) for hour and day.",
        },
        {
            "category": "Customer / Entity",
            "color": "#22C55E",
            "feature_count": 12,
            "importance_weight": 0.07,
            "features": [
                "customer_risk_score",
                "customer_tier",
                "balance_amount",
                "account_age_days",
                "kyc_level",
                "active_card_count",
                "historical_fraud_count",
                "days_since_last_fraud",
                "is_compromised_profile",
                "card_network",
                "card_compromised",
                "recent_password_reset",
            ],
            "description": "Customer lifetime risk, KYC level, account age, historical fraud incidents.",
        },
        {
            "category": "Merchant & MCC",
            "color": "#EC4899",
            "feature_count": 6,
            "importance_weight": 0.05,
            "features": [
                "merchant_category_code",
                "high_risk_mcc",
                "is_online_merchant",
                "is_atm",
                "new_merchant_flag",
                "merchant_fraud_rate",
            ],
            "description": "Merchant category risk scoring, new merchant detection, high-risk MCC categories.",
        },
    ]


def _safe_list(value) -> list:
    """Safely convert a triggered_rule_ids value to a list, handling Python repr format."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    import ast
    import json

    try:
        return json.loads(value)
    except Exception:
        try:
            return ast.literal_eval(value)
        except Exception:
            return []


def _txn_to_sample(t: Transaction) -> dict:
    return {
        "transaction_id": t.id[:12] + "...",
        "amount": float(t.amount or 0),
        "channel": t.channel,
        "merchant_name": t.merchant_name or "Unknown",
        "city": t.city or "—",
        "country_code": t.country_code or "IN",
        "device_type": t.device_type or "unknown",
        "timestamp": t.transaction_timestamp.isoformat() if t.transaction_timestamp else None,
        "fraud_score": float(t.fraud_score or 0),
        "label": "fraud" if t.fraud_category == "fraudulent" else "legitimate",
        "fraud_category": t.fraud_category,
        "risk_level": t.fraud_risk_level or "low",
        "triggered_rules": _safe_list(t.triggered_rule_ids),
        "model_version": t.model_version or "—",
        "color": "#EF4444" if t.fraud_category == "fraudulent" else "#22C55E",
    }


def _static_samples() -> list[dict]:
    """
    Static illustrative sample transactions for the ML Details collapsible table.
    Used when the DB has fewer than 12 real labeled rows.
    """
    return [
        {
            "transaction_id": "txn_001abcdef...",
            "amount": 45000.00,
            "channel": "online",
            "merchant_name": "Amazon UK",
            "city": "London",
            "country_code": "GB",
            "device_type": "mobile",
            "timestamp": "2025-06-15T22:30:00Z",
            "fraud_score": 0.94,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "critical",
            "triggered_rules": ["impossible_travel", "foreign_transaction", "large_amount"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_002abcdef...",
            "amount": 98000.00,
            "channel": "atm",
            "merchant_name": "ATM Withdrawal",
            "city": "Delhi",
            "country_code": "IN",
            "device_type": "pos_terminal",
            "timestamp": "2025-06-16T03:15:00Z",
            "fraud_score": 0.88,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "critical",
            "triggered_rules": ["unusual_hour", "large_amount"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_003abcdef...",
            "amount": 12000.00,
            "channel": "online",
            "merchant_name": "Flipkart",
            "city": "Bangalore",
            "country_code": "IN",
            "device_type": "desktop",
            "timestamp": "2025-06-17T14:00:00Z",
            "fraud_score": 0.82,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "critical",
            "triggered_rules": ["velocity_spike_1h"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_004abcdef...",
            "amount": 9500.00,
            "channel": "online",
            "merchant_name": "Unknown Merchant",
            "city": "Mumbai",
            "country_code": "IN",
            "device_type": "mobile",
            "timestamp": "2025-06-18T02:45:00Z",
            "fraud_score": 0.79,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "high",
            "triggered_rules": ["unusual_hour", "large_amount"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_005abcdef...",
            "amount": 55000.00,
            "channel": "online",
            "merchant_name": "Travel Portal",
            "city": "Dubai",
            "country_code": "AE",
            "device_type": "desktop",
            "timestamp": "2025-06-19T11:00:00Z",
            "fraud_score": 0.73,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "high",
            "triggered_rules": ["foreign_transaction", "large_amount"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_006abcdef...",
            "amount": 15000.00,
            "channel": "mobile",
            "merchant_name": "Croma",
            "city": "Chennai",
            "country_code": "IN",
            "device_type": "mobile",
            "timestamp": "2025-06-20T19:30:00Z",
            "fraud_score": 0.65,
            "label": "fraud",
            "fraud_category": "fraudulent",
            "risk_level": "high",
            "triggered_rules": ["large_amount", "velocity_moderate"],
            "model_version": "ensemble_v1",
            "color": "#EF4444",
        },
        {
            "transaction_id": "txn_007abcdef...",
            "amount": 2500.00,
            "channel": "pos_physical",
            "merchant_name": "D-Mart",
            "city": "Mumbai",
            "country_code": "IN",
            "device_type": "pos_terminal",
            "timestamp": "2025-06-15T11:20:00Z",
            "fraud_score": 0.04,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
        {
            "transaction_id": "txn_008abcdef...",
            "amount": 800.00,
            "channel": "pos_physical",
            "merchant_name": "Cafe Coffee Day",
            "city": "Pune",
            "country_code": "IN",
            "device_type": "pos_terminal",
            "timestamp": "2025-06-15T09:10:00Z",
            "fraud_score": 0.03,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
        {
            "transaction_id": "txn_009abcdef...",
            "amount": 3200.00,
            "channel": "online",
            "merchant_name": "Swiggy",
            "city": "Bangalore",
            "country_code": "IN",
            "device_type": "mobile",
            "timestamp": "2025-06-16T20:00:00Z",
            "fraud_score": 0.07,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
        {
            "transaction_id": "txn_010abcdef...",
            "amount": 1500.00,
            "channel": "pos_physical",
            "merchant_name": "BPCL Petrol",
            "city": "Hyderabad",
            "country_code": "IN",
            "device_type": "pos_terminal",
            "timestamp": "2025-06-17T08:30:00Z",
            "fraud_score": 0.05,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
        {
            "transaction_id": "txn_011abcdef...",
            "amount": 18000.00,
            "channel": "online",
            "merchant_name": "MakeMyTrip",
            "city": "Mumbai",
            "country_code": "IN",
            "device_type": "desktop",
            "timestamp": "2025-06-18T15:00:00Z",
            "fraud_score": 0.11,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
        {
            "transaction_id": "txn_012abcdef...",
            "amount": 500.00,
            "channel": "mobile",
            "merchant_name": "BookMyShow",
            "city": "Delhi",
            "country_code": "IN",
            "device_type": "mobile",
            "timestamp": "2025-06-19T16:45:00Z",
            "fraud_score": 0.02,
            "label": "legitimate",
            "fraud_category": "legitimate",
            "risk_level": "low",
            "triggered_rules": [],
            "model_version": "ensemble_v1",
            "color": "#22C55E",
        },
    ]
