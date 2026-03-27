"""
Fraud Simulator (enhanced Test Me) endpoints.

Provides:
  POST /api/v1/simulator/predict         – run full fraud pipeline on a simulated transaction
  GET  /api/v1/simulator/examples        – 4 prefilled fraud/legit scenarios
  GET  /api/v1/simulator/lookup-customer – look up customer by phone number for auto-fill

The simulator accepts card-level details (card number, CVV, expiry, cardholder name,
email, mobile) in addition to the standard transaction fields.  Card data is NEVER
persisted — only the scored transaction row (with is_test=TRUE) is written to the DB.

If Twilio credentials are configured, an SMS alert is sent automatically for BLOCK
and ALERT decisions to the mobile_number provided in the request.

Phone lookup:
  When the user enters a mobile number, GET /simulator/lookup-customer?phone=+919876543210
  resolves a matching Customer row (same tenant) and returns cardholder name, city,
  country, masked card, and risk profile for pre-filling the simulator form.
"""
from __future__ import annotations

import re
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.services.fraud_detection_service import (
    score_transaction,
    _score_to_category,
    _score_to_risk_level,
    _score_to_decision,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulator", tags=["Fraud Simulator"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SimulatorRequest(BaseModel):
    """Full card-level fraud simulation request."""

    # ── Cardholder identity ──────────────────────────────────────────────
    cardholder_name: str = Field(..., min_length=2, max_length=100, description="Name on the card")
    email: Optional[str] = Field(None, description="Cardholder email")
    mobile_number: Optional[str] = Field(None, description="Mobile number for SMS alert (e.g. +919876543210)")

    # ── Card details (NOT persisted) ─────────────────────────────────────
    card_number: str = Field(..., min_length=13, max_length=19, description="Card number (digits only)")
    card_type: str = Field("visa", description="visa | mastercard | rupay | amex")
    cvv: str = Field(..., min_length=3, max_length=4, description="CVV / CVC")
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024, le=2035)

    # ── Transaction details ───────────────────────────────────────────────
    amount: float = Field(..., gt=0, description="Transaction amount in INR")
    currency: str = Field("INR", max_length=3)
    purchase_type: str = Field(
        "online_shopping",
        description="grocery | restaurant | online_shopping | fuel | travel | atm_withdrawal | electronics | healthcare | wire_transfer | crypto",
    )
    channel: str = Field("online", description="online | pos_physical | atm | mobile | wire")
    merchant_name: Optional[str] = Field(None, max_length=255)

    # ── Location ──────────────────────────────────────────────────────────
    city: Optional[str] = Field(None, max_length=100)
    country_code: str = Field("IN", max_length=2)
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    ip_address: Optional[str] = Field(None)

    # ── Device ────────────────────────────────────────────────────────────
    device_type: str = Field("mobile", description="mobile | desktop | tablet | pos_terminal")
    is_new_device: bool = Field(False)

    # ── Optional customer linkage ─────────────────────────────────────────
    customer_id: Optional[str] = Field(None, description="Link to existing customer for history-based scoring")

    # ── Override timestamp (for replaying past scenarios) ─────────────────
    transaction_timestamp: Optional[datetime] = Field(None)

    @field_validator("card_number")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        return re.sub(r"\s+", "", v)

    @field_validator("mobile_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-()]", "", v)
        if not cleaned.startswith("+"):
            cleaned = "+91" + cleaned.lstrip("0")
        return cleaned


# ---------------------------------------------------------------------------
# GET /api/v1/simulator/lookup-customer
# ---------------------------------------------------------------------------

@router.get("/lookup-customer")
async def lookup_customer_by_phone(
    current_user: CurrentUser,
    phone: str = Query(..., description="Phone number to look up (e.g. +919876543210 or 09876543210)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up a Customer by phone number within the current tenant.

    Normalises the phone to E.164 (+91…) before searching.
    Also tries a last-10-digit partial match as a fallback.

    Returns cardholder name, email, city, country, masked card token,
    and risk profile — all safe to surface in the simulator form.
    """
    # Normalise the input phone number
    cleaned = re.sub(r"[\s\-().]", "", phone)
    if not cleaned.startswith("+"):
        # Strip leading zeros and assume India (+91) if no country code
        stripped = cleaned.lstrip("0")
        if len(stripped) == 10:
            cleaned = "+91" + stripped
        else:
            cleaned = "+" + stripped

    last10 = re.sub(r"\D", "", cleaned)[-10:]

    # Try exact match first, then partial (last 10 digits)
    result = await db.execute(
        select(Customer)
        .where(
            Customer.tenant_id == current_user.tenant_id,
            or_(
                Customer.phone_number == cleaned,
                Customer.phone_number == phone,
            ),
        )
        .limit(1)
    )
    customer = result.scalar_one_or_none()

    if not customer and last10:
        result = await db.execute(
            select(Customer)
            .where(
                Customer.tenant_id == current_user.tenant_id,
                Customer.phone_number.like(f"%{last10}"),
            )
            .limit(1)
        )
        customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"No customer found with phone number '{phone}'. "
                   "Try a different number or fill the form manually.",
        )

    # Mask preferred card token for display (show only last 4)
    card_last4 = "****"
    if customer.preferred_card_token:
        tok = re.sub(r"\D", "", customer.preferred_card_token)
        if len(tok) >= 4:
            card_last4 = tok[-4:]

    return {
        "found": True,
        "customer_id": customer.id,
        "cardholder_name": customer.full_name,
        "email": customer.email,
        "city": customer.city or "",
        "country_code": (customer.country_code or "IN").upper(),
        "state_province": customer.state_province or "",
        "card_last4": card_last4,
        "card_type": "visa",          # Default — card network not stored separately
        "risk_score": float(customer.risk_score or 0),
        "customer_tier": customer.customer_tier,
        "kyc_status": customer.kyc_status,
        "account_type": customer.account_type,
        "balance_amount": float(customer.balance_amount or 0),
        "active_card_count": customer.active_card_count or 0,
    }


# ---------------------------------------------------------------------------
# POST /api/v1/simulator/predict
# ---------------------------------------------------------------------------

@router.post("/predict")
async def predict_fraud(
    body: SimulatorRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the full 4-layer fraud detection pipeline on a simulated transaction.

    Steps:
      1.  Validate & derive card metadata (masked card tail, expiry check)
      2.  Resolve or create customer (links to existing if customer_id provided)
      3.  Build Transaction object (is_test=True) and persist
      4.  Run fraud scoring pipeline (rules + ML ensemble)
      5.  Assemble human-readable reasons
      6.  Send Twilio SMS if BLOCK/ALERT and mobile_number provided
      7.  Return prediction, risk score, risk level, decision, reasons, SHAP
    """
    t_start = time.time()

    # ── 1. Card metadata ────────────────────────────────────────────────
    card_digits = re.sub(r"\D", "", body.card_number)
    card_last4 = card_digits[-4:] if len(card_digits) >= 4 else "****"
    card_masked = f"**** **** **** {card_last4}"

    # Expiry check
    now = datetime.now(timezone.utc)
    expiry_expired = (
        body.expiry_year < now.year or
        (body.expiry_year == now.year and body.expiry_month < now.month)
    )
    card_flags: list[str] = []
    if expiry_expired:
        card_flags.append("expired_card")

    # Device fingerprint (derived from card + device context)
    device_fp = f"sim_{body.card_type}_{card_last4}_{body.device_type}"
    if body.is_new_device:
        device_fp = f"new_{device_fp}_{uuid.uuid4().hex[:8]}"

    # ── 2. Resolve or create customer ──────────────────────────────────
    resolved_customer_id: Optional[str] = body.customer_id

    if not resolved_customer_id:
        temp_cust = Customer(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            full_name=body.cardholder_name,
            email=body.email,
            phone_number=body.mobile_number,
            account_type="personal",
            kyc_status="verified",
            risk_score=0.10,
            customer_tier="standard",
            balance_amount=50000.0,
            active_card_count=1,
            city=body.city,
            country_code=body.country_code or "IN",
        )
        db.add(temp_cust)
        await db.flush()
        resolved_customer_id = temp_cust.id

    # ── 3. Build Transaction ────────────────────────────────────────────
    txn = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        customer_id=resolved_customer_id,
        amount=body.amount,
        currency=body.currency,
        transaction_type="purchase",
        channel=body.channel,
        merchant_name=body.merchant_name or _infer_merchant(body.purchase_type),
        merchant_category_code=_purchase_type_to_mcc(body.purchase_type),
        city=body.city,
        country_code=body.country_code,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        ip_address=body.ip_address,
        device_fingerprint=device_fp,
        device_type=body.device_type,
        transaction_timestamp=body.transaction_timestamp or datetime.now(timezone.utc),
        is_test=True,
        fraud_category="unscored",
        status="completed",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    # ── 4. Run fraud scoring pipeline ───────────────────────────────────
    score_result = await score_transaction(txn, db, broadcast_fn=None)
    await db.refresh(txn)

    final_score = score_result.get("fraud_score", 0.04)
    decision = score_result.get("decision", "PASS")
    triggered_rules = score_result.get("triggered_rules", [])
    shap = score_result.get("shap_explanation")
    model_version = score_result.get("model_version", "rules_only_v1")

    # Merge in card-derived flags
    if card_flags:
        triggered_rules = list(triggered_rules) + card_flags
        if expiry_expired:
            final_score = min(1.0, final_score + 0.30)
            decision = _score_to_decision(final_score)

    # ── 5. Build human-readable reasons ─────────────────────────────────
    reasons = _build_reasons(
        triggered_rules=triggered_rules,
        amount=body.amount,
        channel=body.channel,
        country_code=body.country_code,
        is_new_device=body.is_new_device,
        expiry_expired=expiry_expired,
        fraud_score=final_score,
    )

    processing_ms = int((time.time() - t_start) * 1000)

    # ── 6. Twilio SMS (if configured and decision is BLOCK/ALERT) ───────
    sms_result = "skipped"
    if decision in ("BLOCK", "ALERT") and body.mobile_number:
        sms_result = await _send_twilio_sms(
            to=body.mobile_number,
            amount=body.amount,
            merchant=body.merchant_name or _infer_merchant(body.purchase_type),
            decision=decision,
            score=final_score,
            alert_id=score_result.get("alert_id", "SIM"),
        )

    risk_color = _score_color(final_score)

    return {
        "transaction_id": txn.id,
        "prediction": "fraud" if final_score >= 0.60 else "legitimate",
        "decision": decision,
        "risk_score": round(final_score, 4),
        "risk_score_pct": f"{final_score:.0%}",
        "risk_level": _score_to_risk_level(final_score),
        "risk_color": risk_color,
        "fraud_category": _score_to_category(final_score),
        "model_version": model_version,
        "processing_ms": processing_ms,

        # Card summary (masked)
        "card_summary": {
            "masked_number": card_masked,
            "card_type": body.card_type.upper(),
            "expiry": f"{body.expiry_month:02d}/{body.expiry_year}",
            "expired": expiry_expired,
        },

        # Why fraud / why pass
        "reasons": reasons,
        "triggered_rules": triggered_rules,

        # SHAP explanation
        "shap_explanation": shap,

        # Notification
        "sms_status": sms_result,

        # Step-by-step journey data (for the Test Me UI panel)
        "journey": {
            "step_data_received":   {"ok": True, "ms": 1},
            "step_rules_engine":    {
                "ok": True,
                "triggered": len([r for r in triggered_rules if r not in card_flags]),
                "ms": 3,
            },
            "step_ml_inference":    {
                "ok": model_version != "rules_only_v1",
                "model": model_version,
                "ms": processing_ms - 5,
            },
            "step_ensemble_score":  {"ok": True, "score": round(final_score, 4), "decision": decision, "ms": 2},
            "step_persisted":       {"ok": True, "is_test": True},
            "step_sms":             {"ok": sms_result == "sent", "status": sms_result},
        },
    }


# ---------------------------------------------------------------------------
# GET /api/v1/simulator/examples
# ---------------------------------------------------------------------------

@router.get("/examples")
async def get_examples(_: CurrentUser):
    """
    Returns 4 prefilled fraud simulation scenarios.
    Each example is a valid SimulatorRequest body ready to POST.
    """
    return {
        "examples": [
            {
                "id": "normal_purchase",
                "label": "Normal Grocery Purchase",
                "description": "Low-value daytime grocery purchase — expected PASS",
                "expected_outcome": "legitimate",
                "expected_decision": "PASS",
                "color": "#22C55E",
                "payload": {
                    "cardholder_name": "Priya Sharma",
                    "email": "priya.sharma@example.com",
                    "mobile_number": "+919876543210",
                    "card_number": "4111111111111111",
                    "card_type": "visa",
                    "cvv": "123",
                    "expiry_month": 12,
                    "expiry_year": 2027,
                    "amount": 2500.00,
                    "currency": "INR",
                    "purchase_type": "grocery",
                    "channel": "pos_physical",
                    "merchant_name": "D-Mart",
                    "city": "Mumbai",
                    "country_code": "IN",
                    "location_lat": 19.0760,
                    "location_lng": 72.8777,
                    "device_type": "pos_terminal",
                    "is_new_device": False,
                },
            },
            {
                "id": "impossible_travel",
                "label": "Impossible Travel (Mumbai → London)",
                "description": "Transaction in London 15 minutes after one in Mumbai — physically impossible",
                "expected_outcome": "fraud",
                "expected_decision": "BLOCK",
                "color": "#EF4444",
                "payload": {
                    "cardholder_name": "Rajesh Kumar",
                    "email": "rajesh.kumar@example.com",
                    "mobile_number": "+919123456780",
                    "card_number": "5500005555555559",
                    "card_type": "mastercard",
                    "cvv": "456",
                    "expiry_month": 8,
                    "expiry_year": 2026,
                    "amount": 45000.00,
                    "currency": "INR",
                    "purchase_type": "electronics",
                    "channel": "online",
                    "merchant_name": "Amazon UK",
                    "city": "London",
                    "country_code": "GB",
                    "location_lat": 51.5074,
                    "location_lng": -0.1278,
                    "device_type": "mobile",
                    "is_new_device": True,
                },
            },
            {
                "id": "high_value_night",
                "label": "Large ATM Withdrawal at 3 AM",
                "description": "₹98,000 ATM withdrawal at 3:15 AM from a new device",
                "expected_outcome": "fraud",
                "expected_decision": "ALERT",
                "color": "#F97316",
                "payload": {
                    "cardholder_name": "Anita Desai",
                    "email": "anita.desai@example.com",
                    "mobile_number": "+918765432109",
                    "card_number": "6011111111111117",
                    "card_type": "rupay",
                    "cvv": "789",
                    "expiry_month": 3,
                    "expiry_year": 2028,
                    "amount": 98000.00,
                    "currency": "INR",
                    "purchase_type": "atm_withdrawal",
                    "channel": "atm",
                    "merchant_name": "ATM Withdrawal",
                    "city": "Delhi",
                    "country_code": "IN",
                    "location_lat": 28.6139,
                    "location_lng": 77.2090,
                    "device_type": "pos_terminal",
                    "is_new_device": True,
                    "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=15).isoformat(),
                },
            },
            {
                "id": "velocity_fraud",
                "label": "Rapid Successive Transactions",
                "description": "6 online purchases at different merchants within 8 minutes — velocity fraud",
                "expected_outcome": "fraud",
                "expected_decision": "BLOCK",
                "color": "#EF4444",
                "payload": {
                    "cardholder_name": "Vijay Malhotra",
                    "email": "vijay.malhotra@example.com",
                    "mobile_number": "+917654321098",
                    "card_number": "378282246310005",
                    "card_type": "amex",
                    "cvv": "7890",
                    "expiry_month": 1,
                    "expiry_year": 2026,
                    "amount": 12000.00,
                    "currency": "INR",
                    "purchase_type": "online_shopping",
                    "channel": "online",
                    "merchant_name": "Flipkart",
                    "city": "Bangalore",
                    "country_code": "IN",
                    "location_lat": 12.9716,
                    "location_lng": 77.5946,
                    "device_type": "desktop",
                    "is_new_device": False,
                },
            },
        ]
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _purchase_type_to_mcc(purchase_type: str) -> str:
    MCC_MAP = {
        "grocery":         "5411",
        "restaurant":      "5812",
        "online_shopping": "5999",
        "fuel":            "5541",
        "travel":          "4722",
        "atm_withdrawal":  "6011",
        "electronics":     "5734",
        "healthcare":      "5912",
        "wire_transfer":   "4829",
        "crypto":          "6051",
    }
    return MCC_MAP.get(purchase_type, "5999")


def _infer_merchant(purchase_type: str) -> str:
    MERCHANTS = {
        "grocery":         "D-Mart",
        "restaurant":      "Zomato",
        "online_shopping": "Amazon India",
        "fuel":            "BPCL Petrol Pump",
        "travel":          "MakeMyTrip",
        "atm_withdrawal":  "ATM Withdrawal",
        "electronics":     "Croma",
        "healthcare":      "Apollo Pharmacy",
        "wire_transfer":   "International Wire",
        "crypto":          "CoinSwitch Kuber",
    }
    return MERCHANTS.get(purchase_type, "Online Merchant")


def _score_color(score: float) -> str:
    if score < 0.30:
        return "#22C55E"
    if score < 0.60:
        return "#EAB308"
    if score < 0.80:
        return "#F97316"
    return "#EF4444"


def _build_reasons(
    *,
    triggered_rules: list[str],
    amount: float,
    channel: str,
    country_code: str,
    is_new_device: bool,
    expiry_expired: bool,
    fraud_score: float,
) -> list[dict]:
    """Convert triggered rule names into human-readable reason cards."""

    RULE_DESCRIPTIONS: dict[str, dict] = {
        "large_amount": {
            "title": "Unusually Large Transaction Amount",
            "detail": f"₹{amount:,.0f} is significantly above the customer's historical spending average. Large amounts from new devices or foreign locations carry heightened risk.",
            "severity": "high",
        },
        "unusual_hour": {
            "title": "Transaction at Unusual Hour (1 AM – 5 AM)",
            "detail": "This transaction occurred during the 1–5 AM window, outside of the customer's normal activity hours. Late-night transactions are a strong account takeover signal.",
            "severity": "medium",
        },
        "foreign_transaction": {
            "title": "Foreign Country Detected",
            "detail": f"Transaction originated from {country_code}, which differs from the customer's registered home country (IN). Cross-border card-not-present fraud is a leading fraud vector.",
            "severity": "high",
        },
        "high_risk_country": {
            "title": f"High-Risk Jurisdiction — {country_code}",
            "detail": f"{country_code} is on the high-risk jurisdiction watchlist due to elevated card fraud, money laundering, or sanctions exposure. Transactions from this country carry additional scrutiny.",
            "severity": "critical",
        },
        "velocity_spike_1h": {
            "title": "Velocity Spike — 5+ Transactions in 1 Hour",
            "detail": "An unusually high number of transactions were detected in a short window. This pattern is consistent with card-testing attacks, where fraudsters rapidly probe a card before executing large purchases.",
            "severity": "critical",
        },
        "velocity_moderate": {
            "title": "Elevated Transaction Frequency",
            "detail": "3 or more transactions were recorded in the past hour, above the customer's baseline. Could indicate account sharing or an early-stage fraud attempt.",
            "severity": "medium",
        },
        "rapid_successive": {
            "title": "Rapid Successive Transactions (<10 Minutes)",
            "detail": "Multiple transactions occurred within a 10-minute window. Legitimate cardholders rarely transact this rapidly. This is a primary signal for card skimming and carding fraud.",
            "severity": "high",
        },
        "structuring_pattern": {
            "title": "Structuring / Smurfing Pattern Detected",
            "detail": "Multiple transactions near the ₹8,00,000 currency reporting threshold were detected within 24 hours. This is a classic money-laundering technique designed to avoid AML reporting obligations.",
            "severity": "critical",
        },
        "impossible_travel": {
            "title": "Impossible Travel Detected",
            "detail": "This transaction occurred in a location that cannot be physically reached from the last known location in the elapsed time. The computed travel speed exceeds 900 km/h — only possible if the card details were cloned.",
            "severity": "critical",
        },
        "suspicious_travel_speed": {
            "title": "Suspicious Travel Speed",
            "detail": "The travel speed between consecutive transaction locations is above 450 km/h — improbable for any ground or air transport. This may indicate card-present fraud or identity sharing.",
            "severity": "high",
        },
        "card_not_present_high_value": {
            "title": "High-Value Card-Not-Present Transaction",
            "detail": f"An online transaction of ₹{amount:,.0f} was submitted without physical card verification. CNP fraud accounts for over 75% of global card fraud losses.",
            "severity": "medium",
        },
        "high_risk_merchant_category": {
            "title": "High-Risk Merchant Category",
            "detail": "This transaction is with a merchant in a high-risk category (cryptocurrency exchange, cash advance, gambling, or wire transfer). These MCCs are disproportionately represented in fraud cases.",
            "severity": "high",
        },
        "large_atm_withdrawal": {
            "title": "Large ATM Cash Withdrawal",
            "detail": f"Cash withdrawal of ₹{amount:,.0f} exceeds the normal ATM usage threshold. Large ATM withdrawals — especially at unusual hours — are a common pattern in physical card theft.",
            "severity": "high",
        },
        "foreign_wire_transfer": {
            "title": "International Wire / ACH Transfer",
            "detail": f"An international wire transfer to {country_code} was initiated. Cross-border wire transfers are frequently used to move funds from compromised accounts to mule accounts overseas.",
            "severity": "critical",
        },
        "round_amount_pattern": {
            "title": "Repeated Round-Amount Pattern",
            "detail": "Multiple transactions with exact round amounts (e.g. ₹10,000, ₹20,000) were detected. Fraudsters often use round amounts during card-testing to verify stolen card limits.",
            "severity": "low",
        },
        "expired_card": {
            "title": "Expired Card Presented",
            "detail": "The card's expiry date has passed. Legitimate payment terminals automatically decline expired cards. A transaction appearing with an expired card suggests a fraudulent submission or system bypass.",
            "severity": "high",
        },
        "new_device": {
            "title": "New / Unrecognised Device",
            "detail": "This transaction was initiated from a device fingerprint not previously associated with this account. New device + high-value transaction is a primary account takeover indicator.",
            "severity": "medium",
        },
    }

    reasons = []
    seen = set()

    for rule in triggered_rules:
        if rule in RULE_DESCRIPTIONS and rule not in seen:
            reasons.append(RULE_DESCRIPTIONS[rule])
            seen.add(rule)

    if is_new_device and "new_device" not in seen:
        reasons.append(RULE_DESCRIPTIONS["new_device"])

    # Fallback summary reasons when no specific rule fired
    if not reasons and fraud_score < 0.30:
        reasons.append({
            "title": "No Suspicious Signals Found",
            "detail": "All rule checks and ML model analysis indicate this transaction matches the customer's normal behaviour. Amount, location, device, and timing are all within expected parameters.",
            "severity": "low",
        })
    elif not reasons and fraud_score >= 0.30:
        reasons.append({
            "title": "ML Model Detected Anomaly",
            "detail": f"The ensemble fraud model assigned a score of {fraud_score:.0%}. No single rule triggered, but the overall transaction feature vector is statistically unusual compared to this customer's baseline.",
            "severity": "medium" if fraud_score < 0.60 else "high",
        })

    return reasons


async def _send_twilio_sms(
    *,
    to: str,
    amount: float,
    merchant: str,
    decision: str,
    score: float,
    alert_id: str,
) -> str:
    """
    Sends a Twilio SMS alert.
    Returns 'sent', 'skipped:no_key', or 'error:<msg>'.
    """
    from app.config import get_settings
    settings = get_settings()

    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_num = getattr(settings, "TWILIO_FROM_NUMBER", "")

    if not (sid and token and from_num):
        return "skipped:no_key"

    try:
        import httpx, base64
        body_text = (
            f"FinShield Simulator: {decision} — ₹{amount:,.0f} at {merchant}. "
            f"Fraud Score: {score:.0%}. Ref: {str(alert_id)[:8]}"
        )
        creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                headers={"Authorization": f"Basic {creds}"},
                data={"From": from_num, "To": to, "Body": body_text},
            )
        if resp.status_code in (200, 201):
            logger.info("Simulator SMS sent to %s", to)
            return "sent"
        else:
            logger.warning("Twilio failed: %s", resp.status_code)
            return f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("Simulator SMS error: %s", exc)
        return f"error:{exc}"
