"""
FinShield AI -- Notification Service
======================================
Sends fraud alerts via email (Resend.com) and SMS (Twilio).

All channels are optional -- the platform degrades gracefully when
API keys are not configured.

Priority matrix:
  critical -> email + SMS + in-app
  high     -> email + in-app
  medium   -> email + in-app
  low      -> in-app only
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_fraud_alert_notifications(
    *,
    alert_id: str,
    tenant_id: str,
    transaction_id: str,
    fraud_score: float,
    severity: str,  # low|medium|high|critical
    decision: str,  # PASS|FLAG|ALERT|BLOCK
    amount: float,
    merchant_name: Optional[str],
    triggered_rules: list[str],
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    analyst_email: Optional[str] = None,
    is_test: bool = False,
    # BYOK overrides — pre-fetched from tenant_credentials before the task fires
    override_resend_key: Optional[str] = None,
    override_brevo_key: Optional[str] = None,
    override_twilio_sid: Optional[str] = None,
    override_twilio_token: Optional[str] = None,
    override_twilio_from: Optional[str] = None,
    override_from_email: Optional[str] = None,
    override_firebase_server_key: Optional[str] = None,
    # Channel toggles — read from tenant settings, honoured here (ISSUE-003)
    sms_enabled: bool = True,
    email_customer_enabled: bool = True,
    email_company_enabled: bool = True,
    # Plan gate — SMS is Pro+ only (ISSUE-006)
    tenant_plan: str = "free",
) -> dict:
    """
    Fire all applicable notification channels.

    Channels fired:
      - Twilio SMS → customer phone (critical/high)
      - Resend email → customer email (medium+)
      - Resend email → company ALERT_COMPANY_EMAIL (medium+)
      - Resend email → analyst_email override if provided

    Returns a dict summarising what was sent.
    """
    from app.config import get_settings

    settings = get_settings()

    results: dict[str, str] = {}

    # Never send real notifications for test transactions
    if is_test:
        return {"skipped": "is_test=true"}

    # Base channels from severity
    channels_by_severity = {
        "critical": ["email", "sms"],
        "high": ["email", "sms"],
        "medium": ["email"],
        "low": [],
    }
    channels = list(channels_by_severity.get(severity, []))

    # Platform-level SMS kill-switch (ALERT_SMS_ENABLED env var)
    if "sms" in channels and not getattr(settings, "ALERT_SMS_ENABLED", True):
        channels.remove("sms")
        results["sms_customer"] = "skipped:sms_disabled_by_platform"

    # ISSUE-003: honour tenant-level toggles
    if not sms_enabled and "sms" in channels:
        channels.remove("sms")
        results["sms_customer"] = "skipped:sms_disabled_by_tenant"
    # ISSUE-006: SMS only on Pro / Advanced plans
    if tenant_plan not in ("pro", "advanced") and "sms" in channels:
        channels.remove("sms")
        results["sms_customer"] = "skipped:plan_upgrade_required"

    amount_str = f"₹{amount:,.0f}"
    merchant_str = merchant_name or "Unknown Merchant"
    rules_str = ", ".join(triggered_rules) if triggered_rules else "ML model"
    cust_name = customer_name or "Customer"
    ref = alert_id[:8].upper()

    # Tenant BYOK key takes priority; fall back to platform-level env var.
    # If Resend isn't configured, Brevo is tried next (same fallback chain).
    resend_key = override_resend_key or getattr(settings, "RESEND_API_KEY", "") or ""
    brevo_key = override_brevo_key or getattr(settings, "BREVO_API_KEY", "") or ""
    email_from_name = getattr(settings, "EMAIL_FROM_NAME", "FinShield AI")

    # ISSUE-008: use pre-resolved verified sender when provided, else fall
    # back to the Resend sandbox domain so delivery doesn't silently 403.
    if override_from_email:
        email_from = override_from_email
    else:
        _env_from = getattr(settings, "EMAIL_FROM", "") or ""
        # If the platform EMAIL_FROM is still the unowned placeholder, swap to
        # Resend's sandbox (only delivers to the Resend account owner's inbox).
        email_from = (
            _env_from
            if (_env_from and "finshield.ai" not in _env_from)
            else "onboarding@resend.dev"
        )

    async def _send_email(*, to: str, subject: str, html: str) -> str:
        """Provider-agnostic email dispatch: Resend first, Brevo fallback."""
        if resend_key:
            return await _send_resend(
                api_key=resend_key,
                from_addr=f"{email_from_name} <{email_from}>",
                to=to,
                subject=subject,
                html=html,
            )
        if brevo_key:
            return await _send_brevo(
                api_key=brevo_key,
                from_email=email_from,
                from_name=email_from_name,
                to=to,
                subject=subject,
                html=html,
            )
        return "skipped:no_key"

    # ── Email → Company (one email per configured recipient) ─────────────────
    if "email" in channels and not email_company_enabled:
        results["email_company"] = "skipped:email_company_disabled_by_tenant"
    elif "email" in channels:
        raw_company_email = analyst_email or getattr(settings, "ALERT_COMPANY_EMAIL", "") or ""
        # Support comma-separated list of alert recipients
        company_emails = [e.strip() for e in raw_company_email.split(",") if e.strip()]
        if (resend_key or brevo_key) and company_emails:
            html_body = _company_email_html(
                alert_id=alert_id,
                fraud_score=fraud_score,
                severity=severity,
                decision=decision,
                amount_str=amount_str,
                merchant_str=merchant_str,
                rules_str=rules_str,
                customer_name=cust_name,
                customer_email=customer_email or "—",
                customer_phone=customer_phone or "—",
                transaction_id=transaction_id,
                ref=ref,
            )
            subject = f"[FinShield] {severity.upper()} — {decision} | {amount_str} · {cust_name} · Ref {ref}"
            for recipient in company_emails:
                status = await _send_email(to=recipient, subject=subject, html=html_body)
                logger.info(
                    "Company alert email sent | alert=%s to=%s status=%s",
                    alert_id,
                    recipient,
                    status,
                )
            results["email_company"] = f"sent:{len(company_emails)}"
        else:
            results["email_company"] = "skipped:no_key_or_email"

    # ── Email → Customer ─────────────────────────────────────────────────────
    if "email" in channels and customer_email and not email_customer_enabled:
        results["email_customer"] = "skipped:email_customer_disabled_by_tenant"
    elif "email" in channels and customer_email:
        results["email_customer"] = await _send_email(
            to=customer_email,
            subject=f"Security Alert: {decision} — {amount_str} at {merchant_str} | Ref {ref}",
            html=_customer_email_html(
                customer_name=cust_name,
                amount_str=amount_str,
                merchant_str=merchant_str,
                decision=decision,
                fraud_score=fraud_score,
                ref=ref,
            ),
        )

    # ── SMS → Customer (Twilio) ──────────────────────────────────────────────
    if "sms" in channels and customer_phone:
        twilio_sid = override_twilio_sid or getattr(settings, "TWILIO_ACCOUNT_SID", "") or ""
        twilio_token = override_twilio_token or getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
        twilio_from = override_twilio_from or getattr(settings, "TWILIO_FROM_NUMBER", "") or ""

        if twilio_sid and twilio_token and twilio_from:
            if decision == "BLOCK":
                sms_body = (
                    f"FinShield Security: Your transaction of {amount_str} at {merchant_str} "
                    f"was BLOCKED due to fraud risk. If authorised, contact support. Ref: {ref}"
                )
            else:
                sms_body = (
                    f"FinShield Alert: Suspicious transaction of {amount_str} at {merchant_str} flagged. "
                    f"Score: {fraud_score:.0%}. If not you, contact your bank. Ref: {ref}"
                )
            results["sms_customer"] = await _send_twilio_sms(
                sid=twilio_sid,
                token=twilio_token,
                from_num=twilio_from,
                to=customer_phone,
                body=sms_body,
            )
            logger.info("Alert SMS sent | alert=%s to=%s", alert_id, customer_phone)
        else:
            results["sms_customer"] = "skipped:no_key"

    # ── Push Notification → Firebase FCM (critical/high) ────────────────────
    # FCM is opt-in — only fires when a firebase server_key is configured.
    # On Pro/Advanced plans, critical and high alerts trigger push.
    if severity in ("critical", "high") and tenant_plan in ("pro", "advanced"):
        firebase_key = override_firebase_server_key or getattr(settings, "FIREBASE_SERVER_KEY", "") or ""
        if firebase_key:
            results["push_fcm"] = await _send_fcm_push(
                server_key=firebase_key,
                title=f"FinShield: {decision} — {amount_str} at {merchant_str}",
                body=f"Fraud score {fraud_score:.0%} · {severity.upper()} risk · Ref {ref}",
                data={
                    "alert_id": alert_id,
                    "transaction_id": transaction_id,
                    "severity": severity,
                    "decision": decision,
                },
            )
        else:
            results["push_fcm"] = "skipped:no_firebase_key"

    results["in_app"] = "always_available"
    return results


# ── HTTP helpers ─────────────────────────────────────────────────────────────


async def _send_resend(*, api_key: str, from_addr: str, to: str, subject: str, html: str) -> str:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"from": from_addr, "to": [to], "subject": subject, "html": html},
            )
        return "sent" if resp.status_code in (200, 201) else f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("Resend error: %s", exc)
        return f"error:{str(exc)[:60]}"


async def _send_brevo(
    *, api_key: str, from_email: str, from_name: str, to: str, subject: str, html: str
) -> str:
    """Send a transactional email via Brevo (formerly Sendinblue)."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": api_key,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json={
                    "sender": {"email": from_email, "name": from_name},
                    "to": [{"email": to}],
                    "subject": subject,
                    "htmlContent": html,
                },
            )
        return "sent" if resp.status_code in (200, 201) else f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("Brevo error: %s", exc)
        return f"error:{str(exc)[:60]}"


async def _send_twilio_sms(*, sid: str, token: str, from_num: str, to: str, body: str) -> str:
    try:
        import httpx
        import base64

        creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                headers={"Authorization": f"Basic {creds}"},
                data={"From": from_num, "To": to, "Body": body},
            )
        return "sent" if resp.status_code in (200, 201) else f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("Twilio SMS error: %s", exc)
        return f"error:{str(exc)[:60]}"


async def _send_fcm_push(
    *, server_key: str, title: str, body: str, data: dict
) -> str:
    """
    Send a push notification via Firebase Cloud Messaging (Legacy HTTP API).

    Uses the /fcm/send endpoint with a topic broadcast so no device tokens are
    needed at the platform level.  Institutions can subscribe their mobile app
    to the topic 'finshield_fraud_alerts_{tenant_id}' to receive pushes.

    For targeted per-device delivery, store FCM registration tokens in the
    customer profile and pass them here.
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={
                    "Authorization": f"key={server_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": "/topics/finshield_fraud_alerts",
                    "notification": {"title": title, "body": body},
                    "data": data,
                    "priority": "high",
                },
            )
        if resp.status_code in (200, 201):
            return "sent"
        return f"failed:{resp.status_code}"
    except Exception as exc:
        logger.warning("FCM push error: %s", exc)
        return f"error:{str(exc)[:60]}"


def _company_email_html(
    *,
    alert_id: str,
    fraud_score: float,
    severity: str,
    decision: str,
    amount_str: str,
    merchant_str: str,
    rules_str: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    transaction_id: str,
    ref: str,
) -> str:
    color = {"critical": "#EF4444", "high": "#F97316", "medium": "#F59E0B", "low": "#22C55E"}.get(
        severity, "#6B7280"
    )
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#0A0A0F;color:#E5E7EB;padding:24px;">
    <div style="max-width:600px;margin:0 auto;background:#111118;border:1px solid #1E1E2E;border-radius:12px;overflow:hidden;">
      <div style="background:{color};padding:20px;"><h1 style="margin:0;font-size:18px;color:#fff;">
        🚨 FinShield — Fraud Alert: {decision} | Ref {ref}</h1></div>
      <div style="padding:24px;">
        <p style="color:#9CA3AF;font-size:13px;">A fraud event has been automatically detected and requires attention.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Decision</td>
              <td style="padding:8px 0;font-weight:bold;color:{color};border-bottom:1px solid #1E1E2E;">{decision}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Customer</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{customer_name}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Email</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{customer_email}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Phone</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{customer_phone}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Amount</td>
              <td style="padding:8px 0;font-weight:bold;border-bottom:1px solid #1E1E2E;">{amount_str}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Merchant</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{merchant_str}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Fraud Score</td>
              <td style="padding:8px 0;color:{color};font-weight:bold;border-bottom:1px solid #1E1E2E;">{fraud_score:.1%}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Triggered Rules</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{rules_str}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;">Transaction ID</td>
              <td style="padding:8px 0;font-family:monospace;font-size:12px;">{transaction_id}</td></tr>
        </table>
        <p style="color:#4B5563;font-size:11px;margin-top:24px;">Sent by FinShield AI · Log in to your dashboard to investigate this alert.</p>
      </div></div></body></html>"""


def _customer_email_html(
    *,
    customer_name: str,
    amount_str: str,
    merchant_str: str,
    decision: str,
    fraud_score: float,
    ref: str,
) -> str:
    color = "#EF4444" if decision == "BLOCK" else "#F97316" if decision == "ALERT" else "#F59E0B"
    action = "BLOCKED" if decision == "BLOCK" else "FLAGGED as suspicious"
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#0A0A0F;color:#E5E7EB;padding:24px;">
    <div style="max-width:560px;margin:0 auto;background:#111118;border:1px solid #1E1E2E;border-radius:12px;overflow:hidden;">
      <div style="background:{color};padding:20px;text-align:center;">
        <h1 style="margin:0;font-size:20px;color:#fff;">⚠️ Transaction {action}</h1></div>
      <div style="padding:24px;">
        <p>Dear <strong>{customer_name}</strong>,</p>
        <p>FinShield AI has detected a potentially fraudulent transaction on your account.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Amount</td>
              <td style="padding:8px 0;font-weight:bold;border-bottom:1px solid #1E1E2E;">{amount_str}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Merchant</td>
              <td style="padding:8px 0;border-bottom:1px solid #1E1E2E;">{merchant_str}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;border-bottom:1px solid #1E1E2E;">Risk Score</td>
              <td style="padding:8px 0;color:{color};font-weight:bold;border-bottom:1px solid #1E1E2E;">{fraud_score:.0%}</td></tr>
          <tr><td style="padding:8px 0;color:#9CA3AF;">Reference</td>
              <td style="padding:8px 0;font-family:monospace;">{ref}</td></tr>
        </table>
        <p style="color:#9CA3AF;font-size:13px;">If you authorised this transaction, no action is required. If you did <strong>not</strong> make this transaction, contact your bank immediately.</p>
        <p style="color:#4B5563;font-size:11px;margin-top:24px;">This alert was generated automatically by FinShield AI. Do not reply.</p>
      </div></div></body></html>"""
