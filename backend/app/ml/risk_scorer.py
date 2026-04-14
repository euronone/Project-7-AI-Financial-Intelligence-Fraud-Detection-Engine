"""
FinShield AI — Ensemble Risk Scorer (Layer 4)
===============================================
Combines outputs from all detection layers into a single
calibrated fraud_score (0.0–1.0).

Ensemble weights (from CLAUDE.md spec):
  Rules Engine:     0.25
  Anomaly (IF+DB):  0.20
  XGBoost:          0.30
  Random Forest:    0.15
  Neural Network:   0.10

Decision thresholds:
  < 0.30  -> PASS       (legitimate)
  0.30–0.59 -> FLAG     (suspicious, allow but flag)
  0.60–0.79 -> ALERT    (high risk, allow but alert)
  ≥ 0.80  -> BLOCK      (fraudulent, block transaction)
"""

import os
import pickle
from dataclasses import dataclass, field
from typing import Optional


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


@dataclass
class FraudDecision:
    """Full fraud scoring result for one transaction."""

    fraud_score: float
    fraud_category: str  # legitimate | suspicious | fraudulent
    fraud_risk_level: str  # low | medium | high | critical
    decision: str  # PASS | FLAG | ALERT | BLOCK
    # Per-layer scores
    rules_score: float = 0.0
    anomaly_score: float = 0.0
    xgb_score: float = 0.0
    rf_score: float = 0.0
    nn_score: float = 0.0
    # Triggered rules
    triggered_rules: list[str] = field(default_factory=list)
    # Confidence
    confidence: float = 0.0


class EnsembleScorer:
    """
    Weighted combination of all four detection layers.

    Usage:
        scorer = EnsembleScorer()
        decision = scorer.score(
            rules_score=0.8,
            anomaly_score=0.6,
            xgb_score=0.9,
            rf_score=0.85,
            nn_score=0.88,
            triggered_rules=["impossible_travel"],
        )
    """

    # Default ensemble weights (must sum to 1.0)
    WEIGHTS = {
        "rules": 0.25,
        "anomaly": 0.20,
        "xgb": 0.30,
        "rf": 0.15,
        "nn": 0.10,
    }

    def __init__(self, weights: Optional[dict] = None):
        if weights:
            self.WEIGHTS = weights

    def score(
        self,
        rules_score: float,
        anomaly_score: float,
        xgb_score: float,
        rf_score: float,
        nn_score: float,
        triggered_rules: list[str] | None = None,
    ) -> FraudDecision:
        """
        Compute the final ensemble fraud score and decision.

        All input scores should be in [0, 1].
        Returns a FraudDecision with all details.

        Adaptive weighting: when ML models produce near-zero scores
        (poorly trained or unavailable), their weight is redistributed
        to the rules engine so it can drive the full decision range.
        """
        ml_scores = [anomaly_score, xgb_score, rf_score, nn_score]
        ml_active_count = sum(1 for s in ml_scores if s > 0.05)

        if ml_active_count == 0:
            # ── ML models not contributing → rules-dominant mode ──────
            # Rules score drives the decision directly.
            # Apply a small damping factor (0.90) so a single-rule hit
            # doesn't immediately produce extreme scores; compound rules
            # still reach the full 0–1 range naturally.
            fraud_score = float(rules_score * 0.90)
        elif ml_active_count <= 2:
            # ── Partial ML availability → blended mode ────────────────
            # Redistribute weight from inactive ML models to rules.
            w = dict(self.WEIGHTS)  # copy
            ml_keys = ["anomaly", "xgb", "rf", "nn"]
            ml_vals = [anomaly_score, xgb_score, rf_score, nn_score]
            dead_weight = sum(w[k] for k, v in zip(ml_keys, ml_vals) if v <= 0.05)
            # Give half the dead weight to rules, spread rest among active
            w["rules"] += dead_weight * 0.6
            active_keys = [k for k, v in zip(ml_keys, ml_vals) if v > 0.05]
            if active_keys:
                bonus = (dead_weight * 0.4) / len(active_keys)
                for k in active_keys:
                    w[k] += bonus

            fraud_score = (
                w["rules"] * rules_score
                + w["anomaly"] * anomaly_score
                + w["xgb"] * xgb_score
                + w["rf"] * rf_score
                + w["nn"] * nn_score
            )
            fraud_score = float(max(0.0, min(1.0, fraud_score)))
        else:
            # ── Full ensemble mode (all ML models active) ─────────────
            w = self.WEIGHTS
            fraud_score = (
                w["rules"] * rules_score
                + w["anomaly"] * anomaly_score
                + w["xgb"] * xgb_score
                + w["rf"] * rf_score
                + w["nn"] * nn_score
            )
            fraud_score = float(max(0.0, min(1.0, fraud_score)))

        # ── ML reliability correction ────────────────────────────
        # Current ML models have low precision (~39%), producing high
        # scores for both clean and fraudulent transactions.  Until
        # models are retrained with better data, blend rules-dominant
        # scoring (70%) with the raw ensemble (30%) so the rules engine
        # drives decision boundaries while ML still contributes signal.
        # TODO: remove this correction once ML precision > 70%.
        fraud_score = rules_score * 0.70 + fraud_score * 0.30
        fraud_score = float(max(0.0, min(1.0, fraud_score)))

        # Boost score if multiple high-confidence signals agree
        high_signals = sum(1 for s in [rules_score, xgb_score, rf_score] if s > 0.70)
        if high_signals >= 2:
            fraud_score = min(1.0, fraud_score * 1.15)

        # Classify
        fraud_category, fraud_risk_level, decision = self._classify(fraud_score)

        # Confidence: how much individual scores agree (low variance = high confidence)
        import statistics

        scores = [rules_score, anomaly_score, xgb_score, rf_score, nn_score]
        try:
            confidence = 1.0 - min(1.0, statistics.stdev(scores))
        except Exception:
            confidence = 0.5

        return FraudDecision(
            fraud_score=round(fraud_score, 4),
            fraud_category=fraud_category,
            fraud_risk_level=fraud_risk_level,
            decision=decision,
            rules_score=round(rules_score, 4),
            anomaly_score=round(anomaly_score, 4),
            xgb_score=round(xgb_score, 4),
            rf_score=round(rf_score, 4),
            nn_score=round(nn_score, 4),
            triggered_rules=triggered_rules or [],
            confidence=round(confidence, 4),
        )

    @staticmethod
    def _classify(score: float) -> tuple[str, str, str]:
        """Map fraud_score to (fraud_category, risk_level, decision)."""
        if score < 0.30:
            return "legitimate", "low", "PASS"
        elif score < 0.60:
            return "suspicious", "medium", "FLAG"
        elif score < 0.80:
            return "suspicious", "high", "ALERT"
        else:
            return "fraudulent", "critical", "BLOCK"

    def save(self, path: str | None = None):
        os.makedirs(MODELS_DIR, exist_ok=True)
        path = path or os.path.join(MODELS_DIR, "ensemble_scorer_v1.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Saved EnsembleScorer -> {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "EnsembleScorer":
        path = path or os.path.join(MODELS_DIR, "ensemble_scorer_v1.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)
