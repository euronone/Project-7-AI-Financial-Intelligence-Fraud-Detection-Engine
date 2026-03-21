"""Model evaluation utilities.

Computes standard classification metrics from predictions and labels.
"""

from typing import Any


def evaluate_model(predictions: list[float], labels: list[int], threshold: float = 0.5) -> dict[str, Any]:
    """Compute accuracy, precision, recall, F1, and AUC proxy from predictions."""
    if not predictions or not labels or len(predictions) != len(labels):
        return _empty_metrics()

    tp = fp = tn = fn = 0
    for pred, label in zip(predictions, labels, strict=False):
        pred_label = 1 if pred >= threshold else 0
        if pred_label == 1 and label == 1:
            tp += 1
        elif pred_label == 1 and label == 0:
            fp += 1
        elif pred_label == 0 and label == 0:
            tn += 1
        else:
            fn += 1

    total = len(predictions)
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    auc_proxy = _auc_proxy(predictions, labels)

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "auc_roc": round(auc_proxy, 4),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "total_samples": total,
        "fraud_rate": round(sum(labels) / len(labels), 4) if labels else 0,
    }


def _auc_proxy(predictions: list[float], labels: list[int]) -> float:
    """Approximate AUC-ROC using the Mann-Whitney U statistic."""
    pos_scores = [p for p, l in zip(predictions, labels, strict=False) if l == 1]
    neg_scores = [p for p, l in zip(predictions, labels, strict=False) if l == 0]

    if not pos_scores or not neg_scores:
        return 0.5

    concordant = sum(1 for p in pos_scores for n in neg_scores if p > n)
    tied = sum(0.5 for p in pos_scores for n in neg_scores if p == n)
    total = len(pos_scores) * len(neg_scores)

    return (concordant + tied) / total if total > 0 else 0.5


def _empty_metrics() -> dict[str, Any]:
    return {
        "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0, "auc_roc": 0,
        "true_positives": 0, "false_positives": 0, "true_negatives": 0,
        "false_negatives": 0, "total_samples": 0, "fraud_rate": 0,
    }
