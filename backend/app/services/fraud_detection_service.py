"""
FinShield AI -- Fraud Detection Service
==========================================
Orchestrates the full fraud scoring pipeline for a single transaction.

Flow:
  1. Load customer history from DB
  2. Run rules engine (stub score for now, real rules in Phase 5)
  3. Run ML pipeline (feature engineering -> anomaly -> classifier -> ensemble)
  4. Persist fraud fields to transaction row
  5. If score >= 0.30 -> create FraudAlert
  6. Broadcast via WebSocket (non-blocking)
"""
from __future__ import annotations

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
            _pipeline = FraudScoringPipeline()
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
# Simple deterministic rules (pre-ML layer)
# ---------------------------------------------------------------------------

def _run_simple_rules(txn: Transaction, recent_txns: list[Transaction]) -> tuple[float, list[str]]:
    """
    Fast deterministic checks that run before ML inference.
    Returns (rules_score 0-1, list of triggered rule names).
    """
    score = 0.0
    triggered: list[str] = []

    amount = float(txn.amount or 0)

    # Rule 1: Very large transaction (>50,000 INR)
    if amount > 50_000:
        score = max(score, 0.40)
        triggered.append("large_amount")

    # Rule 2: Transaction at unusual hour (1 AM - 5 AM)
    hour = txn.transaction_timestamp.hour if txn.transaction_timestamp else -1
    if 1 <= hour <= 5:
        score = max(score, 0.30)
        triggered.append("unusual_hour")

    # Rule 3: Foreign transaction (non-IN)
    if txn.country_code and txn.country_code != "IN":
        score = max(score, 0.35)
        triggered.append("foreign_transaction")

    # Rule 4: Velocity check - count recent transactions in last hour
    if recent_txns:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_count = sum(
            1 for t in recent_txns
            if t.transaction_timestamp and t.transaction_timestamp >= one_hour_ago
        )
        if recent_count >= 5:
            score = max(score, 0.60)
            triggered.append("velocity_spike_1h")
        elif recent_count >= 3:
            score = max(score, 0.35)
            triggered.append("velocity_moderate")

    # Rule 5: Impossible travel (very basic: if last txn was foreign and this is domestic or vice versa within 30 min)
    if recent_txns:
        last = recent_txns[0]  # Most recent
        if last.transaction_timestamp and txn.transaction_timestamp:
            minutes_diff = (txn.transaction_timestamp - last.transaction_timestamp).total_seconds() / 60
            if 0 < minutes_diff < 30 and last.country_code and txn.country_code:
                if last.country_code != txn.country_code:
                    score = max(score, 0.85)
                    triggered.append("impossible_travel")

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
            # Build minimal customer dict for feature engineering
            customer_dict = {"customer_id": customer_id or "unknown"}
            # Build transaction dict compatible with feature engineering
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
            # Recent history as list of dicts
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
                for t in recent_txns[:50]  # Limit to 50 for performance
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
        final_score = rules_score if rules_score > 0 else 0.05  # Baseline for unscored
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
