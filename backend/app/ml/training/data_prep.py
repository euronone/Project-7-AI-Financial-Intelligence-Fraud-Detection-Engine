"""Data preparation utilities for model training.

Generates synthetic labeled training data from the transaction table,
or loads a pre-built dataset for offline training.
"""

import random
from typing import Any

from app.ml.feature_engineering import extract_features


def generate_synthetic_dataset(
    transactions: list[dict],
    *,
    fraud_rate: float = 0.05,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate a labeled dataset from transactions with synthetic fraud labels.

    For dev purposes — in production, labels come from resolved alerts.
    """
    rng = random.Random(seed)
    dataset: list[dict[str, Any]] = []

    for txn in transactions:
        features = extract_features(txn)
        is_fraud = _assign_synthetic_label(txn, features, fraud_rate, rng)
        dataset.append({
            "features": features,
            "label": 1 if is_fraud else 0,
            "transaction_id": txn.get("id"),
        })

    return dataset


def _assign_synthetic_label(
    txn: dict, features: dict[str, float], base_rate: float, rng: random.Random
) -> bool:
    """Heuristic label assignment that correlates with fraud signals."""
    prob = base_rate

    if features.get("is_large_amount", 0) > 0:
        prob += 0.1
    if features.get("is_high_risk_country", 0) > 0:
        prob += 0.2
    if features.get("is_night", 0) > 0:
        prob += 0.05
    if features.get("is_new_account", 0) > 0:
        prob += 0.05
    if features.get("is_micro_amount", 0) > 0:
        prob += 0.1
    if features.get("country_change", 0) > 0:
        prob += 0.1

    return rng.random() < min(prob, 0.8)


def split_dataset(
    dataset: list[dict], *, train_ratio: float = 0.8, seed: int = 42
) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    shuffled = list(dataset)
    rng.shuffle(shuffled)
    split = int(len(shuffled) * train_ratio)
    return shuffled[:split], shuffled[split:]
