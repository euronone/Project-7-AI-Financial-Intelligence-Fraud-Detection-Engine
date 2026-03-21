"""Feature engineering for fraud detection.

Extracts 50+ features from raw transaction data for model consumption.
Features span amount, velocity, geography, temporal, device, and entity categories.
"""

import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


def extract_features(txn: dict, history: list[dict] | None = None) -> dict[str, float]:
    """Extract a full feature vector from a transaction and optional entity history."""
    features: dict[str, float] = {}
    history = history or []

    _amount_features(txn, history, features)
    _velocity_features(txn, history, features)
    _temporal_features(txn, features)
    _geo_features(txn, history, features)
    _device_features(txn, history, features)
    _entity_features(txn, history, features)
    _channel_features(txn, features)

    return features


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _amount_features(txn: dict, history: list[dict], features: dict[str, float]) -> None:
    amount = _safe_float(txn.get("amount"))
    features["amount"] = amount
    features["amount_log"] = math.log1p(amount)
    features["is_round_amount"] = 1.0 if amount > 0 and amount % 100 == 0 else 0.0
    features["is_micro_amount"] = 1.0 if 0 < amount < 1.0 else 0.0
    features["is_large_amount"] = 1.0 if amount >= 10000 else 0.0

    if history:
        amounts = [_safe_float(h.get("amount")) for h in history]
        avg = sum(amounts) / len(amounts) if amounts else 0
        features["amount_mean_hist"] = avg
        features["amount_std_hist"] = _std(amounts) if len(amounts) > 1 else 0.0
        features["amount_max_hist"] = max(amounts) if amounts else 0.0
        features["amount_min_hist"] = min(amounts) if amounts else 0.0
        features["amount_zscore"] = (amount - avg) / features["amount_std_hist"] if features["amount_std_hist"] > 0 else 0.0
        features["amount_to_avg_ratio"] = amount / avg if avg > 0 else 0.0
    else:
        for k in ["amount_mean_hist", "amount_std_hist", "amount_max_hist", "amount_min_hist", "amount_zscore", "amount_to_avg_ratio"]:
            features[k] = 0.0


def _velocity_features(txn: dict, history: list[dict], features: dict[str, float]) -> None:
    features["txn_count_total"] = float(len(history))
    features["txn_count_1h"] = _safe_float(txn.get("txn_count_1h"))
    features["txn_count_24h"] = _safe_float(txn.get("txn_count_24h"))
    features["txn_count_7d"] = _safe_float(txn.get("txn_count_7d"))

    if len(history) >= 2:
        amounts = [_safe_float(h.get("amount")) for h in history]
        features["velocity_amount_1h"] = sum(amounts[-5:])
        features["avg_time_between_txn"] = _safe_float(txn.get("avg_time_between_txn"))
    else:
        features["velocity_amount_1h"] = 0.0
        features["avg_time_between_txn"] = 0.0


def _temporal_features(txn: dict, features: dict[str, float]) -> None:
    ts = txn.get("processed_at")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            dt = datetime.now(UTC)
    elif isinstance(ts, datetime):
        dt = ts
    else:
        dt = datetime.now(UTC)

    features["hour_of_day"] = float(dt.hour)
    features["day_of_week"] = float(dt.weekday())
    features["is_weekend"] = 1.0 if dt.weekday() >= 5 else 0.0
    features["is_night"] = 1.0 if dt.hour < 6 or dt.hour >= 22 else 0.0
    features["is_business_hours"] = 1.0 if 9 <= dt.hour < 17 and dt.weekday() < 5 else 0.0
    features["month"] = float(dt.month)
    features["is_month_end"] = 1.0 if dt.day >= 28 else 0.0


def _geo_features(txn: dict, history: list[dict], features: dict[str, float]) -> None:
    country = txn.get("country_code", "")
    features["has_country"] = 1.0 if country else 0.0

    high_risk = {"KP", "IR", "SY", "CU", "SD", "MM", "LY", "VE", "ZW", "AF"}
    features["is_high_risk_country"] = 1.0 if country in high_risk else 0.0

    if history and country:
        prev_countries = {h.get("country_code") for h in history if h.get("country_code")}
        features["country_change"] = 0.0 if country in prev_countries else 1.0
        features["unique_countries"] = float(len(prev_countries | {country}))
    else:
        features["country_change"] = 0.0
        features["unique_countries"] = 1.0 if country else 0.0

    lat = _safe_float(txn.get("geolocation_lat"))
    lng = _safe_float(txn.get("geolocation_lng"))
    features["has_geolocation"] = 1.0 if lat != 0 or lng != 0 else 0.0


def _device_features(txn: dict, history: list[dict], features: dict[str, float]) -> None:
    fp = txn.get("device_fingerprint", "")
    features["has_device_fp"] = 1.0 if fp else 0.0
    features["is_new_device"] = 1.0 if txn.get("is_new_device") else 0.0

    if history and fp:
        known = {h.get("device_fingerprint") for h in history if h.get("device_fingerprint")}
        features["device_seen_before"] = 1.0 if fp in known else 0.0
        features["unique_devices"] = float(len(known | {fp}))
    else:
        features["device_seen_before"] = 0.0
        features["unique_devices"] = 1.0 if fp else 0.0

    features["has_ip"] = 1.0 if txn.get("ip_address") else 0.0


def _entity_features(txn: dict, history: list[dict], features: dict[str, float]) -> None:
    features["account_age_days"] = _safe_float(txn.get("account_age_days"))
    features["is_new_account"] = 1.0 if features["account_age_days"] < 30 else 0.0
    features["recent_info_change"] = 1.0 if txn.get("recent_info_change") else 0.0

    if history:
        unique_dest = {h.get("destination_entity_id") for h in history if h.get("destination_entity_id")}
        features["unique_destinations"] = float(len(unique_dest))
    else:
        features["unique_destinations"] = 0.0


def _channel_features(txn: dict, features: dict[str, float]) -> None:
    channel = txn.get("channel", "")
    for ch in ["online", "pos", "atm", "mobile", "wire", "ach"]:
        features[f"channel_{ch}"] = 1.0 if channel == ch else 0.0
    features["card_present"] = 1.0 if txn.get("card_present") else 0.0

    txn_type = txn.get("transaction_type", "")
    for tt in ["payment", "transfer", "withdrawal", "deposit", "refund"]:
        features[f"type_{tt}"] = 1.0 if txn_type == tt else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
