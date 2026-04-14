"""
FinShield AI — Model Evaluation
==================================
Computes and prints comprehensive metrics for the fraud classifier.
"""

import json
import os
from datetime import datetime, timezone

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
)


MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "models"
)


def evaluate_model(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.50,
    model_name: str = "ensemble",
    feature_count: int = 0,
    training_samples: int = 0,
) -> dict:
    """
    Full evaluation report for a binary fraud classifier.

    Returns a dict with all metrics (also prints a formatted table).
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    try:
        auc_roc = roc_auc_score(y_true, y_pred_proba)
    except Exception:
        auc_roc = 0.0

    try:
        avg_precision = average_precision_score(y_true, y_pred_proba)
    except Exception:
        avg_precision = 0.0

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    metrics = {
        "model_name": model_name,
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "auc_roc": round(auc_roc, 4),
        "avg_precision": round(avg_precision, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "false_negative_rate": round(false_negative_rate, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "test_samples": int(len(y_true)),
        "fraud_samples": int(y_true.sum()),
        "feature_count": feature_count,
        "training_samples": training_samples,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    _print_report(metrics)
    return metrics


def _print_report(m: dict):
    """Pretty-print the evaluation report."""
    print("\n  " + "=" * 60)
    print(f"  MODEL EVALUATION — {m['model_name'].upper()}")
    print("  " + "=" * 60)
    print(f"  Precision:           {m['precision']:.4f}  (target >0.85)")
    print(f"  Recall:              {m['recall']:.4f}  (target >0.75)")
    print(f"  F1 Score:            {m['f1_score']:.4f}  (target >0.80)")
    print(f"  AUC-ROC:             {m['auc_roc']:.4f}  (target >0.92)")
    print(f"  Avg Precision:       {m['avg_precision']:.4f}")
    print(f"  False Positive Rate: {m['false_positive_rate']:.4f}  (target <0.05)")
    print(f"  False Negative Rate: {m['false_negative_rate']:.4f}")
    print(f"\n  Confusion Matrix (threshold={m['threshold']}):")
    print(f"    True  Positive: {m['true_positives']:>5}  (Fraud caught)")
    print(f"    False Positive: {m['false_positives']:>5}  (Legit flagged as fraud)")
    print(f"    True  Negative: {m['true_negatives']:>5}  (Legit correctly passed)")
    print(f"    False Negative: {m['false_negatives']:>5}  (Fraud missed)")
    print(f"\n  Test samples:    {m['test_samples']:,}  (fraud: {m['fraud_samples']})")
    print(f"  Features used:   {m['feature_count']}")

    # Pass/fail vs targets
    targets_met = (
        m["precision"] > 0.85
        and m["recall"] > 0.75
        and m["f1_score"] > 0.80
        and m["auc_roc"] > 0.92
        and m["false_positive_rate"] < 0.05
    )
    status_str = "[PASS] ALL TARGETS MET" if targets_met else "[WARN] Some below target"
    print(f"\n  Target benchmarks: {status_str}")
    print("  " + "=" * 60)


def save_evaluation_report(metrics: dict, filename: str = "evaluation_report.json"):
    """Save metrics dict to models directory."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(MODELS_DIR, filename)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"  Saved evaluation report -> {path}")
    return path
