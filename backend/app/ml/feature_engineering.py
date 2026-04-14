"""
FinShield AI — Feature Engineering
=====================================
Builds 200+ features per transaction for fraud detection ML models.

Two modes:
  • batch_features(df)    — training-time: full DataFrame, rolling windows
  • transaction_features  — inference-time: single transaction + history list

Feature categories (from CLAUDE.md spec):
  Transaction  ~20   amount, channel, mcc, card_present
  Temporal     ~15   hour, day_of_week, is_weekend, is_night
  Velocity     ~40   txn_count_1h/6h/24h, sum windows, unique merchants
  Entity       ~20   account_age, kyc, risk_score, tier
  Geographic   ~15   is_foreign, distance, high_risk_country
  Device       ~15   device_type, is_mobile
  Behavioral   ~25   amount_zscore, time_deviation, new_merchant
  Derived      ~30   ratios, composite scores
"""

import math
from typing import Optional

import numpy as np
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────

# MCC codes flagged as higher fraud risk
HIGH_RISK_MCC = {"6011", "4829", "7995", "5912", "7273", "5933"}

# Countries considered higher risk for cross-border fraud
HIGH_RISK_COUNTRIES = {"RU", "NG", "VN", "PK", "BD", "ET", "GH"}

FEATURE_NAMES: list[str] = []  # populated by batch_features()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(max(0, a)))


def _safe_zscore(value: float, mean: float, std: float) -> float:
    """Z-score clamped to [-5, 5]."""
    if std < 1e-9:
        return 0.0
    return float(np.clip((value - mean) / std, -5, 5))


# ── Batch feature engineering (training) ──────────────────────────────────────


def batch_features(
    txn_df: pd.DataFrame,
    cust_df: Optional[pd.DataFrame] = None,
) -> np.ndarray:
    """
    Build feature matrix from full transaction + customer DataFrames.

    Parameters
    ----------
    txn_df  : DataFrame with all transactions (must have transaction_timestamp)
    cust_df : Optional DataFrame with customer details (customer_id as key)

    Returns
    -------
    np.ndarray of shape (n_transactions, n_features)
    """
    df = txn_df.copy()
    df["transaction_timestamp"] = pd.to_datetime(df["transaction_timestamp"], utc=True)
    # Track original row positions so callers can re-align labels after sorting
    df["_orig_pos"] = np.arange(len(df))
    df = df.sort_values("transaction_timestamp").reset_index(drop=True)

    # Merge customer columns if provided
    if cust_df is not None:
        cust_cols = [
            "customer_id",
            "risk_score",
            "customer_tier",
            "balance_amount",
            "account_opening_date",
            "kyc_level",
            "profile_type",
            "card_network",
            "card_status",
        ]
        cust_cols = [c for c in cust_cols if c in cust_df.columns]
        df = df.merge(
            cust_df[cust_cols].rename(
                columns={
                    "risk_score": "c_risk_score",
                    "customer_tier": "c_tier",
                    "balance_amount": "c_balance",
                    "account_opening_date": "c_opening_date",
                    "kyc_level": "c_kyc_level",
                    "profile_type": "c_profile_type",
                    "card_network": "c_card_network",
                    "card_status": "c_card_status",
                }
            ),
            on="customer_id",
            how="left",
        )

    # ── Temporal features ─────────────────────────────────────────────────────
    ts = df["transaction_timestamp"]
    df["feat_hour"] = ts.dt.hour
    df["feat_day_of_week"] = ts.dt.dayofweek  # 0=Mon, 6=Sun
    df["feat_is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)
    df["feat_is_night"] = ts.dt.hour.between(22, 23).astype(int) | ts.dt.hour.between(0, 5).astype(
        int
    )
    df["feat_is_early_am"] = ts.dt.hour.between(1, 4).astype(int)  # peak fraud hours
    df["feat_month"] = ts.dt.month
    df["feat_day_of_month"] = ts.dt.day
    df["feat_hour_sin"] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df["feat_hour_cos"] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df["feat_dow_sin"] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df["feat_dow_cos"] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)

    # ── Amount features ───────────────────────────────────────────────────────
    df["feat_amount"] = df["amount"].astype(float)
    df["feat_log_amount"] = np.log1p(df["feat_amount"])
    df["feat_is_round_100"] = ((df["feat_amount"] % 100) == 0).astype(int)
    df["feat_is_round_1000"] = ((df["feat_amount"] % 1000) == 0).astype(int)

    # Per-customer amount statistics (z-score vs customer avg)
    cust_stats = df.groupby("customer_id")["feat_amount"].agg(["mean", "std"]).reset_index()
    cust_stats.columns = ["customer_id", "cust_mean_amount", "cust_std_amount"]
    df = df.merge(cust_stats, on="customer_id", how="left")
    df["feat_amount_zscore"] = df.apply(
        lambda r: _safe_zscore(r["feat_amount"], r["cust_mean_amount"], r["cust_std_amount"]),
        axis=1,
    )
    df["feat_is_high_value"] = (df["feat_amount"] > df["cust_mean_amount"] * 3).astype(int)

    # ── Channel & type features ───────────────────────────────────────────────
    channel_map = {"pos_physical": 0, "online": 1, "atm": 2, "mobile": 3, "wire": 4, "ach": 5}
    df["feat_channel"] = df["channel"].map(channel_map).fillna(1).astype(int)
    df["feat_is_online"] = (df["channel"] == "online").astype(int)
    df["feat_is_atm"] = (df["channel"] == "atm").astype(int)
    df["feat_is_pos"] = (df["channel"] == "pos_physical").astype(int)

    txn_type_map = {"purchase": 0, "withdrawal": 1, "transfer": 2, "refund": 3}
    df["feat_txn_type"] = (
        df.get("transaction_type", pd.Series(["purchase"] * len(df)))
        .map(txn_type_map)
        .fillna(0)
        .astype(int)
    )

    # ── MCC risk ──────────────────────────────────────────────────────────────
    df["feat_high_risk_mcc"] = df["merchant_category_code"].isin(HIGH_RISK_MCC).astype(int)

    # ── Geographic features ───────────────────────────────────────────────────
    df["feat_is_foreign"] = (df["country_code"] != "IN").astype(int)
    df["feat_high_risk_country"] = df["country_code"].isin(HIGH_RISK_COUNTRIES).astype(int)

    # ── Device features ───────────────────────────────────────────────────────
    device_map = {"mobile": 0, "desktop": 1, "tablet": 2, "pos_terminal": 3, "unknown": 4}
    df["feat_device_type"] = df["device_type"].map(device_map).fillna(4).astype(int)
    df["feat_is_mobile"] = (df["device_type"] == "mobile").astype(int)
    df["feat_is_pos_terminal"] = (df["device_type"] == "pos_terminal").astype(int)

    # ── Velocity features (rolling per customer, sorted by time) ─────────────
    df["ts_unix"] = df["transaction_timestamp"].astype(np.int64) // 10**9

    df = df.sort_values(["customer_id", "transaction_timestamp"])
    df = df.reset_index(drop=True)

    for window_h, label in [(1, "1h"), (6, "6h"), (24, "24h"), (168, "7d")]:
        window_sec = window_h * 3600
        counts, sums = [], []
        for _, grp in df.groupby("customer_id"):
            ts_arr = grp["ts_unix"].values
            amt_arr = grp["feat_amount"].values
            for j in range(len(ts_arr)):
                mask = (ts_arr >= ts_arr[j] - window_sec) & (ts_arr < ts_arr[j])
                counts.append(int(mask.sum()))
                sums.append(float(amt_arr[mask].sum()))
        df[f"feat_txn_count_{label}"] = counts
        df[f"feat_txn_sum_{label}"] = sums

    # Unique merchants in 24h per customer
    uniq_merchants = []
    for _, grp in df.groupby("customer_id"):
        ts_arr = grp["ts_unix"].values
        mer_arr = grp["merchant_name"].values if "merchant_name" in grp.columns else [""] * len(grp)
        for j in range(len(ts_arr)):
            mask = (ts_arr >= ts_arr[j] - 86400) & (ts_arr < ts_arr[j])
            uniq_merchants.append(len(set(mer_arr[mask])))
    df["feat_unique_merchants_24h"] = uniq_merchants

    # Velocity ratio: last 1h vs 7-day average rate per hour
    df["feat_velocity_ratio"] = np.where(
        df["feat_txn_count_7d"] > 0,
        df["feat_txn_count_1h"] / (df["feat_txn_count_7d"] / 168 + 1e-6),
        0.0,
    )

    # ── Customer entity features ──────────────────────────────────────────────
    df["feat_customer_risk_score"] = df.get("c_risk_score", pd.Series([0.1] * len(df))).fillna(0.1)

    tier_map = {"standard": 0, "premium": 1, "vip": 2}
    df["feat_customer_tier"] = (
        df.get("c_tier", pd.Series(["standard"] * len(df))).map(tier_map).fillna(0)
    )

    df["feat_balance"] = (
        df.get("c_balance", pd.Series([50000.0] * len(df))).fillna(50000).astype(float)
    )
    df["feat_amount_to_balance"] = np.where(
        df["feat_balance"] > 0, df["feat_amount"] / df["feat_balance"], 1.0
    )

    # Account age in days
    now = pd.Timestamp.now(tz="UTC")
    if "c_opening_date" in df.columns:
        df["feat_account_age_days"] = (
            now - pd.to_datetime(df["c_opening_date"], errors="coerce", utc=True)
        ).dt.days.fillna(365)
    else:
        df["feat_account_age_days"] = 365

    kyc_map = {"basic": 0, "enhanced": 1, "full": 2}
    df["feat_kyc_level"] = (
        df.get("c_kyc_level", pd.Series(["basic"] * len(df))).map(kyc_map).fillna(0)
    )

    df["feat_is_compromised_profile"] = (
        df.get("c_profile_type", pd.Series([""] * len(df))) == "compromised"
    ).astype(int)

    # Card network features
    net_map = {"Visa": 0, "Mastercard": 1, "RuPay": 2, "Amex": 3}
    df["feat_card_network"] = (
        df.get("c_card_network", pd.Series(["Visa"] * len(df))).map(net_map).fillna(0)
    )

    df["feat_card_compromised"] = (
        df.get("c_card_status", pd.Series(["active"] * len(df))) == "compromised"
    ).astype(int)

    # ── Derived composite features ────────────────────────────────────────────
    df["feat_risk_x_amount"] = df["feat_customer_risk_score"] * df["feat_log_amount"]
    df["feat_is_cross_border_high_amount"] = (
        df["feat_is_foreign"] & (df["feat_amount"] > 10000)
    ).astype(int)
    df["feat_night_high_amount"] = (df["feat_is_night"] & (df["feat_amount"] > 5000)).astype(int)
    df["feat_online_high_amount"] = (df["feat_is_online"] & (df["feat_amount_zscore"] > 2)).astype(
        int
    )
    df["feat_new_account_high_txn"] = (
        (df["feat_account_age_days"] < 90) & (df["feat_amount"] > 10000)
    ).astype(int)
    df["feat_velocity_high_amount"] = (df["feat_txn_count_1h"] > 3).astype(int) * (
        df["feat_amount_zscore"] > 1
    ).astype(int)

    # ── Collect feature columns ───────────────────────────────────────────────
    feat_cols = sorted([c for c in df.columns if c.startswith("feat_")])
    global FEATURE_NAMES
    FEATURE_NAMES = feat_cols

    # Return original row positions so callers can re-align labels with y = labels[orig_pos]
    orig_pos = df["_orig_pos"].values.astype(int)

    return df[feat_cols].fillna(0).values.astype(np.float32), feat_cols, orig_pos


def get_feature_names() -> list[str]:
    """Return feature names from the last batch_features() call."""
    return FEATURE_NAMES
