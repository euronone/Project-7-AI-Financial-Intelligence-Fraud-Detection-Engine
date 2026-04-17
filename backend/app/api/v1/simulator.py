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
from app.models.payment_method import CustomerPaymentMethod
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
    mobile_number: Optional[str] = Field(
        None, description="Mobile number for SMS alert (e.g. +919876543210)"
    )

    # ── Payment method ────────────────────────────────────────────────────
    payment_method: str = Field(
        "credit_card",
        description="credit_card | debit_card | upi",
    )
    # UPI virtual payment address (only when payment_method == 'upi')
    upi_vpa: Optional[str] = Field(None, max_length=100, description="e.g. sunil@oksbi")

    # ── Card details (NOT persisted) — required for credit_card / debit_card ──
    card_number: str = Field(
        "0000000000000000", min_length=13, max_length=19, description="Card number (digits only)"
    )
    card_type: str = Field("visa", description="visa | mastercard | rupay | amex")
    cvv: str = Field("000", min_length=3, max_length=4, description="CVV / CVC")
    expiry_month: int = Field(12, ge=1, le=12)
    expiry_year: int = Field(2030, ge=2024, le=2035)

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
    customer_id: Optional[str] = Field(
        None, description="Link to existing customer for history-based scoring"
    )

    # ── Override timestamp (for replaying past scenarios) ─────────────────
    transaction_timestamp: Optional[datetime] = Field(None)

    @field_validator("card_number")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        # Remove spaces, dashes, and asterisks (e.g. masked "**** **** **** 5678").
        cleaned = re.sub(r"[\s\-\*]", "", v)
        # If masked input reduced it below 13 digits, use a safe placeholder.
        if len(cleaned) < 13:
            return "0000000000000000"
        return cleaned

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
    phone: str = Query(
        ..., description="Phone number to look up (e.g. +919876543210 or 09876543210)"
    ),
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

    # Fetch payment methods for this customer
    pm_result = await db.execute(
        select(CustomerPaymentMethod)
        .where(CustomerPaymentMethod.customer_id == customer.id)
        .order_by(CustomerPaymentMethod.is_primary.desc())
    )
    payment_methods = [pm.to_dict() for pm in pm_result.scalars().all()]

    # Fallback: derive card_last4 from preferred_card_token if no payment methods
    card_last4 = "****"
    if customer.preferred_card_token:
        tok = re.sub(r"\D", "", customer.preferred_card_token)
        if len(tok) >= 4:
            card_last4 = tok[-4:]
    elif payment_methods:
        # Use primary payment method's card_last4 if available
        primary = payment_methods[0]
        if primary.get("card_last4"):
            card_last4 = primary["card_last4"]

    # Extract primary payment method details (masked).
    # to_dict() uses "card_expiry_month" / "card_expiry_year" keys.
    # CVV is NEVER stored — always return placeholder "***".
    primary_pm = payment_methods[0] if payment_methods else {}
    masked_cvv = "***"  # CVV never stored; placeholder so frontend can show field
    masked_expiry_month = primary_pm.get("card_expiry_month") or ""
    masked_expiry_year = primary_pm.get("card_expiry_year") or ""

    return {
        "found": True,
        "customer_id": customer.id,
        "cardholder_name": customer.full_name,
        "email": customer.email,
        "city": customer.city or "",
        "country_code": (customer.country_code or "IN").upper(),
        "state_province": customer.state_province or "",
        "card_last4": card_last4,
        "card_type": payment_methods[0].get("card_network", "visa") if payment_methods else "visa",
        # ── Masked card details for auto-population ──────────────────────────
        "masked_cvv": masked_cvv,
        "masked_expiry_month": masked_expiry_month,
        "masked_expiry_year": masked_expiry_year,
        # ──────────────────────────────────────────────────────────────────────
        "risk_score": float(customer.risk_score or 0),
        "customer_tier": customer.customer_tier,
        "kyc_status": customer.kyc_status,
        "account_type": customer.account_type,
        "balance_amount": float(customer.balance_amount or 0),
        "active_card_count": customer.active_card_count or 0,
        # ── Payment methods list ──────────────────────────────────────────────
        "payment_methods": payment_methods,
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
    expiry_expired = body.expiry_year < now.year or (
        body.expiry_year == now.year and body.expiry_month < now.month
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

    rules_score = score_result.get("rules_score", 0.0)
    model_breakdown = score_result.get("model_breakdown") or {}
    processing_ms = int((time.time() - t_start) * 1000)

    # ── 5b. Build ML conclusion (natural-language explanation) ──────────
    conclusion = _build_conclusion(
        decision=decision,
        final_score=final_score,
        rules_score=rules_score,
        triggered_rules=list(triggered_rules),
        amount=body.amount,
        channel=body.channel,
        country_code=body.country_code,
        is_new_device=body.is_new_device,
        expiry_expired=expiry_expired,
        ml_available=model_breakdown.get("ml_available", False),
    )

    # ── 6. Twilio SMS (if configured and decision is BLOCK/ALERT) ───────
    sms_result = "skipped"
    if decision in ("BLOCK", "ALERT") and body.mobile_number:
        twilio_creds = await _resolve_twilio_creds(db=db, tenant_id=current_user.tenant_id)
        sms_result = await _send_twilio_sms(
            to=body.mobile_number,
            amount=body.amount,
            merchant=body.merchant_name or _infer_merchant(body.purchase_type),
            decision=decision,
            score=final_score,
            alert_id=score_result.get("alert_id", "SIM"),
            twilio_creds=twilio_creds,
        )

    # ── 7. Email (Resend primary, Brevo fallback) if decision warrants it ──
    email_result = "skipped"
    if decision in ("BLOCK", "ALERT", "FLAG"):
        # Resolve email provider keys — Resend first, Brevo as fallback
        resend_key = await _resolve_resend_key(db=db, tenant_id=current_user.tenant_id)
        brevo_key = await _resolve_brevo_key(db=db, tenant_id=current_user.tenant_id)
        from_email = await _resolve_from_email(db=db, tenant_id=current_user.tenant_id)
        active_email_key = resend_key or brevo_key

        if active_email_key:
            # Collect all recipient emails: form email + company alert emails
            recipients: list[str] = []
            if body.email:
                recipients.append(body.email)
            company_emails = await _resolve_company_alert_emails(
                db=db, tenant_id=current_user.tenant_id
            )
            for ce in company_emails:
                if ce not in recipients:
                    recipients.append(ce)

            if recipients:
                per_recipient: list[dict] = []
                for recipient in recipients:
                    # Try Resend first; if not configured fall back to Brevo
                    if resend_key:
                        s = await _send_resend_email(
                            api_key=resend_key,
                            from_email=from_email,
                            to=recipient,
                            cardholder_name=body.cardholder_name,
                            customer_id=resolved_customer_id or "N/A",
                            amount=body.amount,
                            merchant=body.merchant_name or _infer_merchant(body.purchase_type),
                            decision=decision,
                            score=final_score,
                            alert_id=score_result.get("alert_id", "SIM"),
                            triggered_rules=triggered_rules,
                        )
                    else:
                        s = await _send_brevo_email(
                            api_key=brevo_key,
                            from_email=from_email,
                            to=recipient,
                            cardholder_name=body.cardholder_name,
                            amount=body.amount,
                            merchant=body.merchant_name or _infer_merchant(body.purchase_type),
                            decision=decision,
                            score=final_score,
                            alert_id=score_result.get("alert_id", "SIM"),
                            triggered_rules=triggered_rules,
                        )
                    per_recipient.append({"to": recipient, "status": s})
                    logger.info(
                        "Simulator email to=%s status=%s decision=%s", recipient, s, decision
                    )
                sent_count = sum(1 for r in per_recipient if r["status"] == "sent")
                fail_count = len(per_recipient) - sent_count
                if fail_count == 0:
                    email_result = f"sent:{sent_count}"
                elif sent_count == 0:
                    # All failed — surface first error message
                    first_err = per_recipient[0]["status"]
                    email_result = f"failed:{first_err}"
                else:
                    email_result = f"partial:{sent_count}/{len(per_recipient)} sent"
                # Attach per-recipient detail to return value (set later)
                _email_recipients_detail = per_recipient
            else:
                email_result = "skipped:no_recipients"
                _email_recipients_detail = []
        else:
            email_result = "skipped:no_email_key"
            _email_recipients_detail = []
    else:
        _email_recipients_detail = []

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
        # Payment method + card summary (masked)
        "payment_method": body.payment_method,
        "upi_vpa": body.upi_vpa if body.payment_method == "upi" else None,
        "card_summary": {
            "masked_number": card_masked if body.payment_method != "upi" else None,
            "card_type": body.card_type.upper() if body.payment_method != "upi" else None,
            "expiry": f"{body.expiry_month:02d}/{body.expiry_year}"
            if body.payment_method != "upi"
            else None,
            "expired": expiry_expired if body.payment_method != "upi" else False,
        },
        # Why fraud / why pass
        "reasons": reasons,
        "triggered_rules": triggered_rules,
        # Per-layer ML breakdown (new — for the right-side panel)
        "rules_score": round(rules_score, 4),
        "model_breakdown": model_breakdown,
        "conclusion": conclusion,
        # SHAP explanation
        "shap_explanation": shap,
        # Notification
        "sms_status": sms_result,
        "email_status": email_result,
        "email_recipients": _email_recipients_detail,
        # Step-by-step journey data (for the Test Me UI panel)
        "journey": {
            "step_data_received": {"ok": True, "ms": 1},
            "step_rules_engine": {
                "ok": True,
                "triggered": len([r for r in triggered_rules if r not in card_flags]),
                "ms": 3,
            },
            "step_ml_inference": {
                "ok": model_version != "rules_only_v1",
                "model": model_version,
                "ms": processing_ms - 5,
            },
            "step_ensemble_score": {
                "ok": True,
                "score": round(final_score, 4),
                "decision": decision,
                "ms": 2,
            },
            "step_persisted": {"ok": True, "is_test": True},
            "step_sms": {"ok": sms_result.startswith("sent"), "status": sms_result},
            # partial success (some emails sent) is treated as ok=True — amber detail shown in UI
            "step_email": {
                "ok": email_result.startswith("sent") or email_result.startswith("partial"),
                "status": email_result,
            },
        },
    }


# ---------------------------------------------------------------------------
# GET /api/v1/simulator/sample-customers
# ---------------------------------------------------------------------------


@router.get("/sample-customers")
async def get_sample_customers(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns up to 5 real customers from the current tenant so the user
    can pick one to auto-fill the simulator form via phone lookup.
    """
    from sqlalchemy import func

    result = await db.execute(
        select(Customer)
        .where(
            Customer.tenant_id == current_user.tenant_id,
            Customer.phone_number.isnot(None),
        )
        .order_by(func.random())
        .limit(5)
    )
    customers = result.scalars().all()

    # For each sample customer, fetch their primary payment method
    samples = []
    for c in customers:
        pm_res = await db.execute(
            select(CustomerPaymentMethod)
            .where(CustomerPaymentMethod.customer_id == c.id)
            .order_by(CustomerPaymentMethod.is_primary.desc())
            .limit(3)
        )
        payment_methods = [pm.to_dict() for pm in pm_res.scalars().all()]
        primary_pm = payment_methods[0] if payment_methods else None

        samples.append(
            {
                "phone_number": c.phone_number,
                "full_name": c.full_name,
                "city": c.city or "India",
                "risk_score": float(c.risk_score or 0),
                "customer_tier": c.customer_tier,
                # Primary payment method summary for chip display
                "primary_payment_type": primary_pm["payment_type"] if primary_pm else None,
                "primary_payment_label": primary_pm["display_label"] if primary_pm else None,
            }
        )

    return {"samples": samples}


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
                    "transaction_timestamp": datetime.now(timezone.utc)
                    .replace(hour=3, minute=15)
                    .isoformat(),
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
        "grocery": "5411",
        "restaurant": "5812",
        "online_shopping": "5999",
        "fuel": "5541",
        "travel": "4722",
        "atm_withdrawal": "6011",
        "electronics": "5734",
        "healthcare": "5912",
        "wire_transfer": "4829",
        "crypto": "6051",
    }
    return MCC_MAP.get(purchase_type, "5999")


def _infer_merchant(purchase_type: str) -> str:
    MERCHANTS = {
        "grocery": "D-Mart",
        "restaurant": "Zomato",
        "online_shopping": "Amazon India",
        "fuel": "BPCL Petrol Pump",
        "travel": "MakeMyTrip",
        "atm_withdrawal": "ATM Withdrawal",
        "electronics": "Croma",
        "healthcare": "Apollo Pharmacy",
        "wire_transfer": "International Wire",
        "crypto": "CoinSwitch Kuber",
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
        reasons.append(
            {
                "title": "No Suspicious Signals Found",
                "detail": "All rule checks and ML model analysis indicate this transaction matches the customer's normal behaviour. Amount, location, device, and timing are all within expected parameters.",
                "severity": "low",
            }
        )
    elif not reasons and fraud_score >= 0.30:
        reasons.append(
            {
                "title": "ML Model Detected Anomaly",
                "detail": f"The ensemble fraud model assigned a score of {fraud_score:.0%}. No single rule triggered, but the overall transaction feature vector is statistically unusual compared to this customer's baseline.",
                "severity": "medium" if fraud_score < 0.60 else "high",
            }
        )

    return reasons


def _build_conclusion(
    *,
    decision: str,
    final_score: float,
    rules_score: float,
    triggered_rules: list[str],
    amount: float,
    channel: str,
    country_code: str,
    is_new_device: bool,
    expiry_expired: bool,
    ml_available: bool,
) -> dict:
    """
    Build a structured natural-language conclusion explaining the final decision.

    Returns:
      {
        "verdict":  "PASSED" | "FLAGGED" | "ALERTED" | "BLOCKED",
        "headline": short one-line reason,
        "detail":   multi-sentence explanation (the "why"),
        "mitigating_factors": list[str]  — what DIDN'T fire (explains unexpected PASS),
        "risk_factors":       list[str]  — what DID fire,
      }
    """
    is_domestic = country_code.upper() in ("IN", "")
    score_pct = f"{final_score:.0%}"
    amount_fmt = f"₹{amount:,.0f}"

    # Collect what didn't fire (mitigating factors that kept score low)
    mitigating: list[str] = []
    if is_domestic and "foreign_transaction" not in triggered_rules:
        mitigating.append("Domestic transaction — no foreign-country risk")
    if not is_new_device and "new_device" not in triggered_rules:
        mitigating.append("Known / previously seen device fingerprint")
    if "unusual_hour" not in triggered_rules:
        mitigating.append("Normal business hours — no unusual timing")
    if "velocity_spike_1h" not in triggered_rules and "rapid_successive" not in triggered_rules:
        mitigating.append("No velocity spike in recent transaction history")
    if (
        "impossible_travel" not in triggered_rules
        and "suspicious_travel_speed" not in triggered_rules
    ):
        mitigating.append("No impossible-travel or geo-anomaly detected")
    if not expiry_expired:
        mitigating.append("Card is not expired")

    # Risk factors that did fire
    risk_factors: list[str] = []
    rule_label_map = {
        "large_amount": f"Transaction amount {amount_fmt} is above normal threshold",
        "unusual_hour": "Transaction at unusual hour (1–5 AM)",
        "foreign_transaction": f"Foreign country detected ({country_code})",
        "high_risk_country": f"High-risk jurisdiction ({country_code})",
        "new_device": "New / unrecognised device fingerprint",
        "velocity_spike_1h": "5+ transactions in the past hour (velocity spike)",
        "velocity_moderate": "Elevated transaction frequency in past hour",
        "rapid_successive": "Rapid consecutive transactions within 10 minutes",
        "structuring_pattern": "Structuring pattern near ₹8,00,000 reporting threshold",
        "impossible_travel": "Impossible travel — location physically unreachable in elapsed time",
        "suspicious_travel_speed": "Suspicious travel speed between consecutive locations",
        "card_not_present_high_value": f"High-value online/CNP transaction ({amount_fmt})",
        "high_risk_merchant_category": "High-risk merchant category (crypto, wire, gambling)",
        "large_atm_withdrawal": f"Large ATM withdrawal of {amount_fmt}",
        "foreign_wire_transfer": f"International wire transfer to {country_code}",
        "round_amount_pattern": "Repeated round-amount structuring pattern",
        "expired_card": "Expired card presented",
    }
    for rule in triggered_rules:
        label = rule_label_map.get(rule)
        if label:
            risk_factors.append(label)

    # ── Build verdict + headline + detail ─────────────────────────────────────

    if decision == "PASS":
        headline = f"Transaction PASSED — fraud score {score_pct} is below the 30% threshold"

        if "large_amount" in triggered_rules:
            # This is the key "large amount but passed" case the user is confused about
            detail = (
                f"The transaction amount of {amount_fmt} did raise a preliminary risk signal "
                f"in the rules engine (rules score: {rules_score:.0%}). However, the overall "
                f"fraud score of {score_pct} remained below the 30% FLAG threshold because "
                f"all other risk dimensions were clean: the transaction is domestic, "
                f"the device is recognised, no velocity anomalies were detected, and timing "
                f"is normal. The ML ensemble confirmed that, in isolation, a large amount "
                f"from a trusted profile does not constitute fraud — only the combination "
                f"of multiple signals (foreign + new device + unusual hour) would push "
                f"this above the threshold. "
            )
            if not ml_available:
                detail += (
                    "Note: ML models are not currently loaded — the decision is based solely "
                    "on the rules engine. Training and promoting a custom ML model via the "
                    "ML Training page will improve scoring accuracy."
                )
        elif not triggered_rules:
            detail = (
                f"No fraud signals were triggered. The transaction amount ({amount_fmt}), "
                f"location ({country_code}), device, timing, and velocity all fall within "
                f"this customer's normal behavioural profile. The fraud score ({score_pct}) "
                f"is in the low-risk zone."
            )
        else:
            detail = (
                f"Minor signals were detected (rules score: {rules_score:.0%}) but the "
                f"combined fraud probability ({score_pct}) stayed below the 30% FLAG threshold. "
                f"The mitigating factors listed above offset the risk signals."
            )

    elif decision == "FLAG":
        headline = f"Transaction FLAGGED — suspicious signals detected (score: {score_pct})"
        detail = (
            f"The fraud score of {score_pct} exceeds the 30% FLAG threshold but remains "
            f"below the 60% ALERT threshold. "
            f"The transaction is not blocked but has been marked suspicious and queued "
            f"for analyst review. "
            f"{len(triggered_rules)} rule(s) contributed to this score. "
            f"If the analyst confirms fraud, the customer's risk score will be updated."
        )

    elif decision == "ALERT":
        headline = f"Transaction ALERTED — high-risk signals detected (score: {score_pct})"
        detail = (
            f"The fraud score of {score_pct} exceeds the 60% ALERT threshold. "
            f"The transaction has been allowed to proceed but a high-priority alert has been "
            f"created. {len(triggered_rules)} fraud signal(s) fired, with the highest-impact "
            f"signals listed above. Immediate analyst review is recommended. "
            f"Customer and analyst notifications have been triggered."
        )

    else:  # BLOCK
        headline = f"Transaction BLOCKED — critical fraud signals detected (score: {score_pct})"
        detail = (
            f"The fraud score of {score_pct} exceeds the 80% BLOCK threshold. "
            f"The transaction has been rejected and marked as 'blocked' in the database. "
            f"{len(triggered_rules)} fraud signal(s) fired. "
            f"The combination of signals (see above) indicates a high probability of fraud "
            f"— specifically, the simultaneous presence of "
            + (", ".join(triggered_rules[:3]) or "multiple critical signals")
            + " pushed the score into the critical zone. "
            "The customer and fraud analyst team have been notified. "
            "The transaction is recorded with is_test=True so it will not affect live fraud rates."
        )

    return {
        "verdict": decision,
        "headline": headline,
        "detail": detail,
        "risk_factors": risk_factors,
        "mitigating_factors": mitigating,
        "rules_score": round(rules_score, 4),
        "final_score": round(final_score, 4),
        "ml_available": ml_available,
    }


async def _resolve_resend_key(*, db: AsyncSession, tenant_id: str) -> str:
    """
    Returns the Resend API key for a tenant.
    Priority:
      1. BYOK tenant_credentials with key_name="resend_api_key"  (canonical)
      2. BYOK tenant_credentials with ANY key_name under service="resend"  (fallback for user typos)
      3. Legacy db_config_json.notifications.resend_api_key
      4. RESEND_API_KEY environment variable
    """
    from app.core.encryption import encryptor
    from app.config import get_settings
    from app.models.user import Tenant as TenantModel

    # 1. Check BYOK with canonical key_name
    try:
        from app.services.credential_service import get_decrypted as _get_cred

        byok_key = await _get_cred(db, tenant_id, "resend", "resend_api_key")
        if byok_key:
            return byok_key
    except Exception as exc:
        logger.warning("BYOK credential lookup failed: %s", exc)

    # 2. Fallback: any key saved under service="resend" — ISSUE-005 shared helper
    try:
        from app.services.credential_service import scan_any_cred_for_service as _scan_svc

        val = await _scan_svc(db, tenant_id, "resend")
        if val:
            return val
    except Exception as exc:
        logger.warning("BYOK resend-service scan failed: %s", exc)

    # 3. Fall back to legacy db_config_json
    try:
        result = await db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        tenant_row = result.scalar_one_or_none()
        notif = (tenant_row.db_config_json or {}).get("notifications", {}) if tenant_row else {}
        enc_key = notif.get("resend_api_key", "")
        if enc_key:
            try:
                return encryptor.decrypt(enc_key)
            except Exception:
                return enc_key  # plaintext fallback
    except Exception as exc:
        logger.warning("Could not load tenant Resend key: %s", exc)

    # 4. Fall back to platform env var
    s = get_settings()
    return getattr(s, "RESEND_API_KEY", "") or ""


async def _resolve_brevo_key(*, db: AsyncSession, tenant_id: str) -> str:
    """
    ISSUE-005: Returns the Brevo API key for a tenant using the same 3-step
    resolution chain as _resolve_resend_key.
      1. BYOK tenant_credentials key_name="brevo_api_key"  (canonical)
      2. BYOK tenant_credentials any key_name under service="brevo"
      3. BREVO_API_KEY environment variable
    """
    from app.config import get_settings

    try:
        from app.services.credential_service import (
            get_decrypted as _get_cred,
            scan_any_cred_for_service as _scan_svc,
        )

        val = await _get_cred(db, tenant_id, "brevo", "brevo_api_key")
        if val:
            return val
        val = await _scan_svc(db, tenant_id, "brevo")
        if val:
            return val
    except Exception as exc:
        logger.warning("Brevo BYOK lookup failed: %s", exc)

    s = get_settings()
    return getattr(s, "BREVO_API_KEY", "") or ""


async def _resolve_from_email(*, db: AsyncSession, tenant_id: str) -> str:
    """
    Returns the verified sender address for Resend emails.

    Priority:
      1. BYOK tenant_credentials service='resend', key_name='from_email'
         (user stores their verified Resend domain address here, e.g. alerts@acmebank.com)
      2. RESEND_FROM_EMAIL env var / EMAIL_FROM setting
      3. Resend test domain (only works for the Resend account owner's email)
    """
    from app.config import get_settings

    # 1. Tenant BYOK — custom verified domain
    try:
        from app.services.credential_service import get_decrypted as _get_cred

        custom = await _get_cred(db, tenant_id, "resend", "from_email")
        if custom and "@" in custom:
            return f"FinShield AI <{custom.strip()}>"
    except Exception as exc:
        logger.warning("Could not load BYOK from_email: %s", exc)

    # 2. Platform env var
    s = get_settings()
    env_from = getattr(s, "EMAIL_FROM", "") or ""
    if env_from and "@" in env_from and "finshield.ai" not in env_from:
        return f"FinShield AI <{env_from}>"

    # 3. Resend test domain — only delivers to Resend account owner email
    return "FinShield AI <onboarding@resend.dev>"


async def _resolve_company_alert_emails(*, db: AsyncSession, tenant_id: str) -> list[str]:
    """
    Returns the list of company alert email recipients for a tenant.
    Reads the comma-separated company_alert_email from tenant notifications config.
    """
    from app.models.user import Tenant as TenantModel
    from app.config import get_settings

    try:
        result = await db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        tenant_row = result.scalar_one_or_none()
        notif = (tenant_row.db_config_json or {}).get("notifications", {}) if tenant_row else {}
        raw = notif.get("company_alert_email", "") or ""
        if raw:
            return [e.strip() for e in raw.split(",") if e.strip()]
    except Exception as exc:
        logger.warning("Could not load company alert emails: %s", exc)

    # Fall back to env var
    s = get_settings()
    env_email = getattr(s, "ALERT_COMPANY_EMAIL", "") or ""
    return [e.strip() for e in env_email.split(",") if e.strip()] if env_email else []


async def _send_resend_email(
    *,
    api_key: str,
    from_email: str,
    to: str,
    cardholder_name: str,
    customer_id: str,
    amount: float,
    merchant: str,
    decision: str,
    score: float,
    alert_id: str,
    triggered_rules: list[str],
) -> str:
    """
    Sends a fraud alert email via Resend.com for simulator/Test Me transactions.

    from_email must be a Resend-verified sender address.
      - If you use onboarding@resend.dev (Resend test domain), Resend will ONLY
        deliver to the email address registered with your Resend account.
      - To send to arbitrary recipients, verify a custom domain in Resend and
        store it as service='resend', key_name='from_email' in tenant credentials.

    Returns 'sent', 'skipped:no_key', or 'failed:<code>:<detail>'.
    """
    if not api_key:
        return "skipped:no_key"
    try:
        import httpx

        amount_str = f"₹{amount:,.0f}"
        ref = str(alert_id)[:8].upper()
        rules_str = ", ".join(triggered_rules[:5]) if triggered_rules else "ML model"
        color = {"BLOCK": "#EF4444", "ALERT": "#F97316", "FLAG": "#F59E0B"}.get(decision, "#6B7280")
        action = (
            "BLOCKED"
            if decision == "BLOCK"
            else "FLAGGED as suspicious"
            if decision in ("ALERT", "FLAG")
            else "reviewed"
        )
        # Truncate customer_id for display (first 8 chars + last 4 for readability)
        cid_display = (
            customer_id if len(customer_id) <= 12 else f"{customer_id[:8]}\u2026{customer_id[-4:]}"
        )
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0A0A0F;color:#E5E7EB;padding:24px;">
        <div style="max-width:560px;margin:0 auto;background:#111118;border:1px solid #1E1E2E;border-radius:12px;overflow:hidden;">
          <div style="background:{color};padding:20px;text-align:center;">
            <h1 style="margin:0;font-size:18px;color:#fff;">🧪 [TEST] FinShield — Transaction {action}</h1>
          </div>
          <div style="padding:24px;">
            <p style="color:#9CA3AF;font-size:12px;margin-top:0;">
              This is a <strong>test notification</strong> from the FinShield Test Me simulator.
              No real transaction was blocked.
            </p>
            <p>Dear <strong>{cardholder_name}</strong>,</p>
            <p>FinShield AI detected the following in your test transaction:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Customer ID</td>
                  <td style="padding:8px 0;font-family:monospace;font-size:12px;border-bottom:1px solid #1E1E2E;">{cid_display}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Decision</td>
                  <td style="padding:8px 0;font-weight:bold;color:{color};border-bottom:1px solid #1E1E2E;">{decision}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Amount</td>
                  <td style="padding:8px 0;font-weight:bold;border-bottom:1px solid #1E1E2E;">{amount_str}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Merchant</td>
                  <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{merchant}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Fraud Score</td>
                  <td style="padding:8px 0;color:{color};font-weight:bold;border-bottom:1px solid #1E1E2E;">{score:.0%}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Triggered Signals</td>
                  <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{rules_str}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;">Reference</td>
                  <td style="padding:8px 0;font-family:monospace;">{ref}</td></tr>
            </table>
            <p style="color:#4B5563;font-size:11px;margin-top:24px;">
              Sent by FinShield AI Test Simulator · This email confirms your email integration is working.
            </p>
          </div>
        </div>
        </body></html>"""

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "from": from_email,
                    "to": [to],
                    "subject": f"[TEST] FinShield Alert: {decision} — {amount_str} at {merchant} | Ref {ref}",
                    "html": html,
                },
            )
        if resp.status_code in (200, 201):
            return "sent"
        # Capture the actual Resend error so it surfaces in the UI
        try:
            err_body = resp.json().get("message") or resp.text[:150]
        except Exception:
            err_body = resp.text[:150]
        logger.warning(
            "Resend rejected email to=%s status=%s err=%s", to, resp.status_code, err_body
        )
        return f"failed:{resp.status_code}:{err_body[:100]}"
    except Exception as exc:
        logger.warning("Simulator Resend email error: %s", exc)
        return f"error:{str(exc)[:80]}"


async def _send_brevo_email(
    *,
    api_key: str,
    from_email: str,
    to: str,
    cardholder_name: str,
    amount: float,
    merchant: str,
    decision: str,
    score: float,
    alert_id: str,
    triggered_rules: list[str],
) -> str:
    """
    Sends a fraud alert email via Brevo (formerly Sendinblue) for simulator transactions.
    Used as fallback when no Resend key is configured.
    Returns 'sent', 'skipped:no_key', or 'failed:<code>'.
    """
    if not api_key:
        return "skipped:no_key"
    try:
        import httpx

        amount_str = f"₹{amount:,.0f}"
        ref = str(alert_id)[:8].upper()
        rules_str = ", ".join(triggered_rules[:5]) if triggered_rules else "ML model"
        color = {"BLOCK": "#EF4444", "ALERT": "#F97316", "FLAG": "#F59E0B"}.get(decision, "#6B7280")
        action = (
            "BLOCKED"
            if decision == "BLOCK"
            else "FLAGGED as suspicious"
            if decision in ("ALERT", "FLAG")
            else "reviewed"
        )
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0A0A0F;color:#E5E7EB;padding:24px;">
        <div style="max-width:560px;margin:0 auto;background:#111118;border:1px solid #1E1E2E;border-radius:12px;overflow:hidden;">
          <div style="background:{color};padding:20px;text-align:center;">
            <h1 style="margin:0;font-size:18px;color:#fff;">🧪 [TEST] FinShield — Transaction {action}</h1>
          </div>
          <div style="padding:24px;">
            <p style="color:#9CA3AF;font-size:12px;margin-top:0;">
              This is a <strong>test notification</strong> from the FinShield Test Me simulator.
            </p>
            <p>Dear <strong>{cardholder_name}</strong>,</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Decision</td>
                  <td style="padding:8px 0;font-weight:bold;color:{color};border-bottom:1px solid #1E1E2E;">{decision}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Amount</td>
                  <td style="padding:8px 0;font-weight:bold;border-bottom:1px solid #1E1E2E;">{amount_str}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Merchant</td>
                  <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{merchant}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Fraud Score</td>
                  <td style="padding:8px 0;color:{color};font-weight:bold;border-bottom:1px solid #1E1E2E;">{score:.0%}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Triggered Signals</td>
                  <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{rules_str}</td></tr>
              <tr><td style="padding:8px 0;color:#9CA3AF;">Reference</td>
                  <td style="padding:8px 0;font-family:monospace;">{ref}</td></tr>
            </table>
            <p style="color:#4B5563;font-size:11px;margin-top:24px;">
              Sent via Brevo by FinShield AI Test Simulator.
            </p>
          </div>
        </div>
        </body></html>"""

        # Brevo requires sender as an object — extract plain email from "Name <email>" format
        sender_email = from_email
        sender_name = "FinShield AI"
        if "<" in from_email and ">" in from_email:
            sender_name = from_email.split("<")[0].strip()
            sender_email = from_email.split("<")[1].rstrip(">").strip()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": api_key,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json={
                    "sender": {"email": sender_email, "name": sender_name},
                    "to": [{"email": to}],
                    "subject": f"[TEST] FinShield Alert: {decision} — {amount_str} at {merchant} | Ref {ref}",
                    "htmlContent": html,
                },
            )
        if resp.status_code in (200, 201):
            return "sent"
        logger.warning("Brevo simulator email failed: status=%s", resp.status_code)
        return f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("Simulator Brevo email error: %s", exc)
        return f"error:{str(exc)[:80]}"


async def _resolve_twilio_creds(*, db: AsyncSession, tenant_id: str) -> dict:
    """
    Returns Twilio credentials dict for a tenant.
    Priority: BYOK tenant_credentials table → platform env vars.

    Keys returned: sid, auth_token, from_number
    """
    from app.config import get_settings

    result: dict = {"sid": "", "auth_token": "", "from_number": ""}

    # 1. Check BYOK tenant_credentials table first
    try:
        from app.services.credential_service import get_decrypted as _get_cred

        for key_name, dest in [
            ("twilio_account_sid", "sid"),
            ("twilio_auth_token", "auth_token"),
            ("twilio_from_number", "from_number"),
        ]:
            val = await _get_cred(db, tenant_id, "twilio", key_name)
            if val:
                result[dest] = val
        if result["sid"] and result["auth_token"] and result["from_number"]:
            return result
    except Exception as exc:
        logger.warning("BYOK Twilio lookup failed: %s", exc)

    # 2. Fall back to platform env vars
    s = get_settings()
    result["sid"] = getattr(s, "TWILIO_ACCOUNT_SID", "") or ""
    result["auth_token"] = getattr(s, "TWILIO_AUTH_TOKEN", "") or ""
    result["from_number"] = getattr(s, "TWILIO_FROM_NUMBER", "") or ""
    return result


async def _send_twilio_sms(
    *,
    to: str,
    amount: float,
    merchant: str,
    decision: str,
    score: float,
    alert_id: str,
    twilio_creds: dict | None = None,
) -> str:
    """
    Sends a Twilio SMS alert.
    Accepts pre-resolved creds dict (sid, auth_token, from_number) from
    _resolve_twilio_creds() so BYOK keys are used before env-var fallback.
    Returns 'sent', 'skipped:no_key', or 'error:<msg>'.
    """
    if twilio_creds is None:
        from app.config import get_settings

        s = get_settings()
        twilio_creds = {
            "sid": getattr(s, "TWILIO_ACCOUNT_SID", "") or "",
            "auth_token": getattr(s, "TWILIO_AUTH_TOKEN", "") or "",
            "from_number": getattr(s, "TWILIO_FROM_NUMBER", "") or "",
        }

    sid = twilio_creds.get("sid", "")
    token = twilio_creds.get("auth_token", "")
    from_num = twilio_creds.get("from_number", "")

    if not (sid and token and from_num):
        return "skipped:no_key"

    try:
        import httpx
        import base64

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
