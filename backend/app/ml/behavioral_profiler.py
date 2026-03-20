"""Behavioral profiler builds per-entity baselines and detects deviations.

Compares current transaction behaviour against the entity's historical
profile to flag unusual patterns.
"""

import math
from typing import Any

import structlog

logger = structlog.get_logger()


class BehavioralProfiler:
    """Per-entity behavioral baseline and deviation detector."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("behavioral_profiler_loaded")

    def build_profile(self, history: list[dict]) -> dict[str, float]:
        """Build a behavioral profile from transaction history."""
        if not history:
            return _empty_profile()

        amounts = [float(h.get("amount", 0)) for h in history]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        std_amount = _std(amounts)

        channels: dict[str, int] = {}
        countries: set[str] = set()
        hours: list[int] = []

        for h in history:
            ch = h.get("channel", "unknown")
            channels[ch] = channels.get(ch, 0) + 1
            if c := h.get("country_code"):
                countries.add(c)
            if pa := h.get("processed_at"):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(pa)) if isinstance(pa, str) else pa
                    hours.append(dt.hour)
                except (ValueError, AttributeError):
                    pass

        avg_hour = sum(hours) / len(hours) if hours else 12.0
        dominant_channel = max(channels, key=channels.get) if channels else "unknown"

        return {
            "avg_amount": avg_amount,
            "std_amount": std_amount,
            "txn_count": float(len(history)),
            "unique_countries": float(len(countries)),
            "avg_hour": avg_hour,
            "dominant_channel": hash(dominant_channel) % 100 / 100.0,
        }

    def score_deviation(self, features: dict[str, float], profile: dict[str, float]) -> dict[str, Any]:
        """Score how much the current transaction deviates from the profile."""
        deviations: dict[str, float] = {}

        if profile.get("std_amount", 0) > 0:
            z = abs(features.get("amount", 0) - profile.get("avg_amount", 0)) / profile["std_amount"]
            deviations["amount_deviation"] = round(min(z / 3.0, 1.0), 4)
        else:
            deviations["amount_deviation"] = 0.0

        deviations["hour_deviation"] = round(
            abs(features.get("hour_of_day", 12) - profile.get("avg_hour", 12)) / 12.0, 4
        )

        deviations["country_novelty"] = features.get("country_change", 0.0)

        weights = {"amount_deviation": 0.5, "hour_deviation": 0.2, "country_novelty": 0.3}
        overall = sum(deviations.get(k, 0) * w for k, w in weights.items())

        return {
            "behavioral_score": round(min(overall, 1.0), 4),
            "deviations": deviations,
            "profile_txn_count": profile.get("txn_count", 0),
            "model_type": "behavioral_profiler",
            "model_version": "dev-1.0",
        }


def _empty_profile() -> dict[str, float]:
    return {
        "avg_amount": 0.0,
        "std_amount": 0.0,
        "txn_count": 0.0,
        "unique_countries": 0.0,
        "avg_hour": 12.0,
        "dominant_channel": 0.0,
    }


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
