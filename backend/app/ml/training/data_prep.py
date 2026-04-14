"""
FinShield AI — Training Data Preparation
==========================================
Loads CSV data, merges customer + transaction DataFrames,
builds feature matrix, and returns train/test splits.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "samples"
)


def load_data(
    transactions_csv: str = "transactions_10000.csv",
    customers_csv: str = "customers_100.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate CSV files. Returns (txn_df, cust_df)."""
    txn_path = os.path.join(DATA_DIR, transactions_csv)
    cust_path = os.path.join(DATA_DIR, customers_csv)

    if not os.path.exists(txn_path):
        raise FileNotFoundError(
            f"Transactions CSV not found: {txn_path}\n  Run: python scripts/seed_data.py"
        )
    if not os.path.exists(cust_path):
        raise FileNotFoundError(
            f"Customers CSV not found: {cust_path}\n  Run: python scripts/seed_data.py"
        )

    txn_df = pd.read_csv(txn_path)
    cust_df = pd.read_csv(cust_path)

    print(f"  Loaded {len(txn_df):,} transactions, {len(cust_df):,} customers")

    # Parse timestamps
    txn_df["transaction_timestamp"] = pd.to_datetime(
        txn_df["transaction_timestamp"], utc=True, errors="coerce"
    )

    # Build binary fraud label
    txn_df["is_fraud"] = (txn_df["fraud_category"] == "fraudulent").astype(int)

    fraud_count = txn_df["is_fraud"].sum()
    legit_count = len(txn_df) - fraud_count
    print(
        f"  Labels — Fraud: {fraud_count} ({fraud_count/len(txn_df)*100:.1f}%)  Legit: {legit_count}"
    )

    return txn_df, cust_df


def split_data(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Stratified train/test split preserving fraud ratio."""
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )
    print(
        f"  Split — Train: {len(X_train):,} (fraud: {y_train.sum()})  "
        f"Test: {len(X_test):,} (fraud: {y_test.sum()})"
    )
    return X_train, X_test, y_train, y_test


def get_class_weight(y: np.ndarray) -> float:
    """Return scale_pos_weight for XGBoost (negatives / positives)."""
    pos = y.sum()
    neg = len(y) - pos
    if pos == 0:
        return 1.0
    return round(float(neg / pos), 2)
