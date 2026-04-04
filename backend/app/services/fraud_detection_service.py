"""
FinShield AI -- Fraud Detection Service
==========================================
Orchestrates the full fraud scoring pipeline for a single transaction.

Flow:
  1. Load customer history from DB
  2. Run rules engine (12+ deterministic rules with compound scoring)
  3. Run ML pipeline (feature engineering -> anomaly -> classifier -> ensemble)
  4. Persist fraud fields to transaction row
  5. If score >= 0.30 -> create FraudAlert
  6. Broadcast via WebSocket (non-blocking)

Rules Engine Coverage:
  R01 - Tiered large amount (4 thresholds)
  R02 - Unusual hour (1–5 AM)
  R03 - Foreign transaction + high-risk country list
  R04 - New / unrecognised device
  R05 - Velocity spike (10 min / 1 h windows)
  R06 - Structuring pattern (multiple txns near ₹8L threshold)
  R07 - Impossible travel (haversine distance ÷ elapsed time)
  R08 - Suspicious travel speed (improbable but not impossible)
  R09 - Card-not-present high-value (online, amount > threshold)
  R10 - High-risk MCC (crypto, cash advance, gambling, adult, pharma)
  R11 - Large ATM cash withdrawal
  R12 - Foreign wire transfer
  R13 - Round-amount pattern (structuring variant)
  R14 - Compound boosters (foreign+new-device, night+large+new-device, etc.)
"""
from __future__ import annotations

import math
import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert

logger = logging.getLogger(__name__)

# Lazy-loaded ML pipeline (loaded once on first call)
_pipeline = None


def _get_pipeline():
    """Load the ML scoring pipeline (singleton, lazy)."""
    global _pipeline
    if _pipeline is None:
        try:
            from app.ml.pipeline import FraudScoringPipeline
            _pipeline = FraudScoringPipeline.get_instance()
            logger.info("ML pipeline loaded successfully")
        except Exception as exc:
            logger.warning("ML pipeline unavailable, using rule-only mode: %s", exc)
            _pipeline = None
    return _pipeline


# ---------------------------------------------------------------------------
# Scoring thresholds -> decision
# ---------------------------------------------------------------------------
def _score_to_category(score: float) -> str:
    if score < 0.30:
        return "legitimate"
    if score < 0.60:
        return "suspicious"
    return "fraudulent"


def _score_to_risk_level(score: float) -> str:
    if score < 0.30:
        return "low"
    if score < 0.60:
        return "medium"
    if score < 0.80:
        return "high"
    return "critical"


def _score_to_decision(score: float) -> str:
    if score < 0.30:
        return "PASS"
    if score < 0.60:
        return "FLAG"
    if score < 0.80:
        return "ALERT"
    return "BLOCK"


def _severity_for_score(score: float) -> str:
    if score < 0.30:
        return "low"
    if score < 0.60:
        return "medium"
    if score < 0.80:
        return "high"
    return "critical"


# ---------------------------------------------------------------------------
# Haversine distance helper
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance in kilometres between two GPS coordinates.
    Uses the Haversine formula — accurate to within 0.3% for all distances.
    """
    R = 6_371.0  # Earth mean radius (km)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


# ---------------------------------------------------------------------------
# High-risk country list  (ISO-3166-1 alpha-2)
# ---------------------------------------------------------------------------
_HIGH_RISK_COUNTRIES = {
    "NG", "GH", "CM", "CI",  # West Africa — high CNP fraud
    "UA", "RU", "BY",         # Eastern Europe — carding rings
    "PK", "BD",               # South Asia — synthetic identity
    "IR", "SY", "KP",         # Sanctioned jurisdictions
    "VE", "YE", "LY",         # High-risk / conflict zones
}

# High-risk Merchant Category Codes
_HIGH_RISK_MCC = {
    "6051",  # Non-financial institutions (crypto exchanges)
    "6010",  # Manual cash disbursement
    "6011",  # ATM / automated cash (handled separately too)
    "7995",  # Gambling / casinos
    "5912",  # Drug stores / pharmacies (card-not-present fraud)
    "5999",  # Miscellaneous retail (catch-all for CNP schemes)
    "7273",  # Dating / escort services
    "4829",  # Money orders / wire transfers
}


# ---------------------------------------------------------------------------
# Rules engine (12+ deterministic rules, additive + compound scoring)
# ---------------------------------------------------------------------------

def _run_simple_rules(txn: Transaction, recent_txns: list[Transaction]) -> tuple[float, list[str]]:
    """
    Multi-signal deterministic rule engine.

    Each triggered signal adds an independent score component.
    Compound boosters add additional weight when multiple signals fire together.
    Final score is clamped to [0, 1].

    Returns (rules_score, list[triggered_rule_names]).
    """
    score = 0.0
    triggered: list[str] = []

    amount = float(txn.amount or 0)
    country = (txn.country_code or "").upper().strip()
    channel = (txn.channel or "").lower()
    mcc = (txn.merchant_category_code or "").strip()
    device_fp = (txn.device_fingerprint or "")
    hour = txn.transaction_timestamp.hour if txn.transaction_timestamp else -1
    lat = float(txn.location_lat) if txn.location_lat is not None else None
    lng = float(txn.location_lng) if txn.location_lng is not None else None

    is_foreign = bool(country and country not in ("IN", ""))
    is_new_dev = device_fp.startswith("new_")
    is_online = channel in ("online", "mobile")

    # ── R01: Tiered large amount ────────────────────────────────────────────
    if amount > 500_000:
        score += 0.55
        triggered.append("large_amount")
    elif amount > 200_000:
        score += 0.45
        triggered.append("large_amount")
    elif amount > 100_000:
        score += 0.35
        triggered.append("large_amount")
    elif amount > 50_000:
        score += 0.22
        triggered.append("large_amount")
    elif amount > 20_000:
        score += 0.10

    # ── R02: Unusual hour ───────────────────────────────────────────────────
    if 1 <= hour <= 4:
        score += 0.20
        triggered.append("unusual_hour")
    elif hour == 0 or hour == 5:
        score += 0.10

    # ── R03: Foreign transaction + high-risk country ────────────────────────
    if is_foreign:
        score += 0.25
        triggered.append("foreign_transaction")
        if country in _HIGH_RISK_COUNTRIES:
            score += 0.25
            triggered.append("high_risk_country")

    # ── R04: New / unrecognised device ──────────────────────────────────────
    if is_new_dev:
        score += 0.18
        triggered.append("new_device")

    # ── R05: Velocity checks (10 min + 1 h windows) ─────────────────────────
    if recent_txns:
        now_utc = datetime.now(timezone.utc)
        ten_min_ago = now_utc - timedelta(minutes=10)
        one_hour_ago = now_utc - timedelta(hours=1)

        cnt_10m = sum(
            1 for t in recent_txns
            if t.transaction_timestamp and t.transaction_timestamp >= ten_min_ago
        )
        cnt_1h = sum(
            1 for t in recent_txns
            if t.transaction_timestamp and t.transaction_timestamp >= one_hour_ago
        )

        if cnt_1h >= 8:
            score += 0.70
            triggered.append("velocity_spike_1h")
        elif cnt_1h >= 5:
            score += 0.50
            triggered.append("velocity_spike_1h")
        elif cnt_1h >= 3:
            score += 0.22
            triggered.append("velocity_moderate")

        if cnt_10m >= 4:
            score += 0.40
            triggered.append("rapid_successive")
        elif cnt_10m >= 3:
            score += 0.25
            triggered.append("rapid_successive")

    # ── R06: Structuring pattern (multiple txns near ₹8L reporting threshold) ─
    if recent_txns:
        now_utc = datetime.now(timezone.utc)
        recent_24h = [
            t for t in recent_txns
            if t.transaction_timestamp
            and t.transaction_timestamp >= now_utc - timedelta(hours=24)
        ]
        near_threshold_prev = [
            t for t in recent_24h
            if 600_000 <= float(t.amount or 0) <= 799_999
        ]
        is_near_threshold_now = 600_000 <= amount <= 799_999
        if len(near_threshold_prev) >= 2 or (near_threshold_prev and is_near_threshold_now):
            score += 0.60
            triggered.append("structuring_pattern")

    # ── R07 / R08: Impossible / suspicious travel (haversine) ───────────────
    if recent_txns:
        _detected_travel = False
        if lat is not None and lng is not None:
            for prev in recent_txns[:10]:
                if (
                    prev.location_lat is not None
                    and prev.location_lng is not None
                    and prev.transaction_timestamp
                    and txn.transaction_timestamp
                ):
                    elapsed_min = abs(
                        (txn.transaction_timestamp - prev.transaction_timestamp).total_seconds() / 60
                    )
                    if elapsed_min < 180 and elapsed_min > 0:
                        dist_km = _haversine_km(
                            float(prev.location_lat), float(prev.location_lng),
                            lat, lng,
                        )
                        speed_kmh = (dist_km / elapsed_min) * 60
                        if speed_kmh > 900 and dist_km > 50:
                            # Faster than commercial aircraft → physically impossible
                            score += 0.85
                            triggered.append("impossible_travel")
                            _detected_travel = True
                            break
                        elif speed_kmh > 450 and dist_km > 100:
                            # Faster than a scheduled flight (improbable)
                            score += 0.45
                            triggered.append("suspicious_travel_speed")
                            _detected_travel = True
                            break

        # Fallback: country-code based travel check (when no GPS available)
        if not _detected_travel:
            last = recent_txns[0]
            if (
                last.transaction_timestamp
                and txn.transaction_timestamp
                and last.country_code
                and country
            ):
                elapsed_min = abs(
                    (txn.transaction_timestamp - last.transaction_timestamp).total_seconds() / 60
                )
                if elapsed_min < 90 and last.country_code.upper() != country:
                    score += 0.75
                    triggered.append("impossible_travel")

    # ── R09: Card-not-present (online) high-value ───────────────────────────
    if is_online and amount > 25_000:
        score += 0.12
        triggered.append("card_not_present_high_value")

    # ── R10: High-risk MCC ──────────────────────────────────────────────────
    if mcc in _HIGH_RISK_MCC and amount > 5_000:
        score += 0.18
        triggered.append("high_risk_merchant_category")

    # ── R11: Large ATM cash withdrawal ──────────────────────────────────────
    if channel == "atm" and amount > 30_000:
        score += 0.22
        triggered.append("large_atm_withdrawal")

    # ── R12: Foreign wire transfer ──────────────────────────────────────────
    if channel in ("wire", "ach") and is_foreign:
        score += 0.28
        triggered.append("foreign_wire_transfer")

    # ── R13: Repeated round-amount pattern ──────────────────────────────────
    if recent_txns and amount > 0 and amount % 1_000 == 0:
        round_prev = sum(
            1 for t in recent_txns[:15]
            if float(t.amount or 0) % 1_000 == 0 and float(t.amount or 0) > 0
        )
        if round_prev >= 3:
            score += 0.12
            triggered.append("round_amount_pattern")

    # ── R14: Compound boosters ───────────────────────────────────────────────
    # Foreign + new device + high value = elevated risk
    if is_foreign and is_new_dev and amount > 10_000:
        score += 0.30

    # Night + large + new device = account takeover signal
    if 0 <= hour <= 5 and amount > 20_000 and is_new_dev:
        score += 0.22

    # Foreign + unusual hour = geographic anomaly
    if is_foreign and 1 <= hour <= 4:
        score += 0.18

    # Online + new device + very high value
    if is_online and is_new_dev and amount > 50_000:
        score += 0.20

    # All three critical signals: foreign + new device + unusual hour
    if is_foreign and is_new_dev and 1 <= hour <= 4:
        score += 0.15

    return min(score, 1.0), triggered


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

async def score_transaction(
    txn: Transaction,
    db: AsyncSession,
    broadcast_fn=None,  # Optional WebSocket broadcast callable
) -> dict:
    """
    Run the full fraud detection pipeline on a transaction.

    Updates the transaction row in-place and returns a result dict.
    """
    t_start = time.time()
    customer_id = txn.customer_id

    # ---- Step 1: Load recent customer history (last 30 days, max 200) -------
    recent_txns: list[Transaction] = []
    if customer_id:
        try:
            since = datetime.now(timezone.utc) - timedelta(days=30)
            result = await db.execute(
                select(Transaction)
                .where(
                    Transaction.customer_id == customer_id,
                    Transaction.id != txn.id,
                    Transaction.transaction_timestamp >= since,
                    Transaction.is_test == False,
                )
                .order_by(Transaction.transaction_timestamp.desc())
                .limit(200)
            )
            recent_txns = list(result.scalars().all())
        except Exception as exc:
            logger.warning("Could not load customer history: %s", exc)

    # ---- Step 2: Rules engine -----------------------------------------------
    rules_score, triggered_rules = _run_simple_rules(txn, recent_txns)

    # ---- Step 3: ML inference (if pipeline available) -----------------------
    pipeline = _get_pipeline()
    ml_result: Optional[dict] = None

    if pipeline is not None:
        try:
            customer_dict = {"customer_id": customer_id or "unknown"}
            txn_dict = {
                "transaction_id": txn.id,
                "customer_id": customer_id or "unknown",
                "amount": float(txn.amount or 0),
                "channel": txn.channel or "online",
                "device_type": txn.device_type or "unknown",
                "merchant_category_code": txn.merchant_category_code or "5999",
                "merchant_name": txn.merchant_name or "Unknown",
                "country_code": txn.country_code or "IN",
                "transaction_timestamp": txn.transaction_timestamp or datetime.now(timezone.utc),
                "transaction_type": txn.transaction_type or "purchase",
            }
            history_dicts = [
                {
                    "transaction_id": t.id,
                    "customer_id": t.customer_id or "unknown",
                    "amount": float(t.amount or 0),
                    "channel": t.channel or "online",
                    "country_code": t.country_code or "IN",
                    "transaction_timestamp": t.transaction_timestamp,
                    "merchant_name": t.merchant_name or "",
                    "merchant_category_code": t.merchant_category_code or "5999",
                    "device_type": t.device_type or "unknown",
                    "transaction_type": t.transaction_type or "purchase",
                }
                for t in recent_txns[:50]
            ]
            ml_result = pipeline.score_transaction(
                transaction=txn_dict,
                customer=customer_dict,
                recent_transactions=history_dicts,
                rules_score=rules_score,
                triggered_rules=triggered_rules,
            )
        except Exception as exc:
            logger.warning("ML inference failed, using rules-only score: %s", exc)

    # ---- Step 4: Determine final score & decision ---------------------------
    if ml_result:
        final_score = float(ml_result.get("fraud_score", rules_score))
        fraud_category = ml_result.get("fraud_category", _score_to_category(final_score))
        risk_level = ml_result.get("fraud_risk_level", _score_to_risk_level(final_score))
        decision = ml_result.get("decision", _score_to_decision(final_score))
        shap_values = ml_result.get("shap_explanation")
        model_version = "ensemble_v1"
    else:
        # Rules-only mode: apply the same damping as EnsembleScorer
        # so thresholds are consistent regardless of code path.
        final_score = (rules_score * 0.90) if rules_score > 0 else 0.04
        fraud_category = _score_to_category(final_score)
        risk_level = _score_to_risk_level(final_score)
        decision = _score_to_decision(final_score)
        shap_values = None
        model_version = "rules_only_v1"

    processing_ms = int((time.time() - t_start) * 1000)

    # ---- Step 5: Persist fraud fields on transaction -----------------------
    txn.fraud_score = round(final_score, 4)
    txn.fraud_category = fraud_category
    txn.fraud_risk_level = risk_level
    txn.triggered_rule_ids = triggered_rules
    txn.shap_values = shap_values
    txn.model_version = model_version
    txn.fraud_scored_at = datetime.now(timezone.utc)

    if decision == "BLOCK":
        txn.status = "blocked"
        txn.is_blocked = True
        txn.is_flagged = True
    elif decision in ("ALERT", "FLAG"):
        txn.is_flagged = True

    await db.commit()
    await db.refresh(txn)

    # ---- Step 6: Create FraudAlert (if score >= FLAG threshold) -------------
    alert = None
    if final_score >= 0.30:
        alert = FraudAlert(
            id=str(uuid.uuid4()),
            tenant_id=txn.tenant_id,
            transaction_id=txn.id,
            customer_id=txn.customer_id,
            alert_type="ml_model" if ml_result else "rule",
            severity=_severity_for_score(final_score),
            status="open",
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        logger.info(
            "Fraud alert created | txn=%s score=%.3f severity=%s",
            txn.id, final_score, alert.severity,
        )

    # ---- Step 7: WebSocket broadcast (fire-and-forget) ----------------------
    if broadcast_fn is not None:
        try:
            import asyncio
            payload = {
                "event": "transaction_scored",
                "data": {
                    "transaction_id": txn.id,
                    "amount": float(txn.amount),
                    "fraud_score": txn.fraud_score,
                    "fraud_category": fraud_category,
                    "risk_level": risk_level,
                    "decision": decision,
                    "triggered_rules": triggered_rules,
                    "alert_id": alert.id if alert else None,
                    "processing_ms": processing_ms,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
            asyncio.create_task(broadcast_fn(payload))
        except Exception as exc:
            logger.debug("WebSocket broadcast skipped: %s", exc)

    return {
        "transaction_id": txn.id,
        "fraud_score": txn.fraud_score,
        "fraud_category": fraud_category,
        "fraud_risk_level": risk_level,
        "decision": decision,
        "triggered_rules": triggered_rules,
        "alert_id": alert.id if alert else None,
        "model_version": model_version,
        "processing_ms": processing_ms,
        "shap_explanation": shap_values,
    }
