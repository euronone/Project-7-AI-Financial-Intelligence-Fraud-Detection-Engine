"""
F5 — Risk Scoring: RiskScorer ML component.

Computes a composite risk score (0.0–1.0) by combining:
  - ML fraud probability  (weight 0.35)
  - Rules engine score    (weight 0.25)
  - Velocity score        (weight 0.15)
  - Behavioral deviation  (weight 0.15)
  - Network / graph score (weight 0.10)

Classifies into: Low (0–0.3), Medium (0.3–0.6), High (0.6–0.8), Critical (0.8–1.0).
Thresholds are configurable (F5.2).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Default configurable thresholds (F5.2)
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "low_max": 0.3,
    "medium_max": 0.6,
    "high_max": 0.8,
    "critical_max": 1.0,
}

# Component weights — must sum to 1.0
COMPONENT_WEIGHTS: Dict[str, float] = {
    "ml_score": 0.35,
    "rule_score": 0.25,
    "velocity_score": 0.15,
    "behavioral_score": 0.15,
    "network_score": 0.10,
}

MODEL_VERSION = "risk_scorer_v1.0.0"


class RiskScorer:
    """
    F5.1 / F5.2 / F5.3: Composite risk score calculator.

    Usage::
        scorer = RiskScorer()
        score, level, factors, explanation = scorer.compute(
            ml_score=0.72,
            rule_score=0.80,
            velocity_score=0.40,
            behavioral_score=0.55,
            network_score=0.20,
            watchlist_match=False,
        )
    """

    def __init__(self, thresholds: Dict[str, float] | None = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self.weights = COMPONENT_WEIGHTS.copy()
        self.model_version = MODEL_VERSION

    # ── Public API ────────────────────────────────────────────────────────

    def compute(
        self,
        ml_score: float,
        rule_score: float,
        velocity_score: float,
        behavioral_score: float,
        network_score: float,
        watchlist_match: bool = False,
        entity_history_count: int = 0,
    ) -> Tuple[float, str, List[str], str]:
        """
        Returns (overall_score, risk_level, risk_factors, explanation).
        """
        components = {
            "ml_score": self._clamp(ml_score),
            "rule_score": self._clamp(rule_score),
            "velocity_score": self._clamp(velocity_score),
            "behavioral_score": self._clamp(behavioral_score),
            "network_score": self._clamp(network_score),
        }

        # Weighted composite (F5.1)
        composite = sum(components[k] * self.weights[k] for k in components)

        # Hard boost for watchlist matches (F5.1 — watchlist contribution)
        if watchlist_match:
            composite = max(composite, 0.70)

        # Penalise entities with long fraud history
        if entity_history_count >= 5:
            composite = min(1.0, composite + 0.05)

        overall = round(self._clamp(composite), 4)
        risk_level = self.classify(overall)
        risk_factors = self._identify_factors(components, watchlist_match, entity_history_count)
        explanation = self._build_explanation(overall, risk_level, components, risk_factors)

        return overall, risk_level, risk_factors, explanation

    def classify(self, score: float) -> str:
        """F5.2: Map a 0–1 score to a named risk level."""
        if score <= self.thresholds["low_max"]:
            return "low"
        if score <= self.thresholds["medium_max"]:
            return "medium"
        if score <= self.thresholds["high_max"]:
            return "high"
        return "critical"

    def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """F5.2 / F14.1: Allow runtime reconfiguration of tier boundaries."""
        for key in ("low_max", "medium_max", "high_max"):
            if key in new_thresholds:
                self.thresholds[key] = new_thresholds[key]

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _identify_factors(
        self,
        components: Dict[str, float],
        watchlist_match: bool,
        history_count: int,
    ) -> List[str]:
        factors: List[str] = []

        if components["ml_score"] >= 0.6:
            factors.append("High ML fraud probability")
        if components["rule_score"] >= 0.5:
            factors.append("Rules engine triggered")
        if components["velocity_score"] >= 0.5:
            factors.append("Unusual transaction velocity")
        if components["behavioral_score"] >= 0.5:
            factors.append("Significant behavioral deviation")
        if components["network_score"] >= 0.4:
            factors.append("Connected to suspicious network nodes")
        if watchlist_match:
            factors.append("Watchlist / sanctions match")
        if history_count >= 5:
            factors.append("Repeated fraud history")

        if not factors:
            factors.append("No significant risk factors identified")

        return factors

    def _build_explanation(
        self,
        score: float,
        level: str,
        components: Dict[str, float],
        factors: List[str],
    ) -> str:
        dominant = max(components, key=components.__getitem__)
        dominant_labels = {
            "ml_score": "ML model output",
            "rule_score": "rules engine",
            "velocity_score": "transaction velocity",
            "behavioral_score": "behavioral profile",
            "network_score": "network analysis",
        }
        return (
            f"Composite risk score {score:.4f} ({level.upper()}). "
            f"Primary driver: {dominant_labels[dominant]} ({components[dominant]:.4f}). "
            f"Key factors: {'; '.join(factors[:3])}."
        )
