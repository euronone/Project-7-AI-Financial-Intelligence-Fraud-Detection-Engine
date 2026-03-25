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
    severity: str,            # low|medium|high|critical
    decision: str,            # PASS|FLAG|ALERT|BLOCK
    amount: float,
    merchant_name: Optional[str],
    triggered_rules: list[str],
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    analyst_email: Optional[str] = None,
) -> dict:
    """
    Fire all applicable notification channels.
    Returns a dict summarising what was sent.
    """
    from app.config import get_settings
    settings = get_settings()

    results: dict[str, str] = {}

    channels_by_severity = {
        "critical": ["email", "sms"],
        "high":     ["email"],
        "medium":   ["email"],
        "low":      [],
    }
    channels = channels_by_severity.get(severity, [])

    amount_str = f"Rs.{amount:,.0f}"
    merchant_str = merchant_name or "Unknown Merchant"
    rules_str = ", ".join(triggered_rules) if triggered_rules else "ML model"

    # -------------------------------------------------------------------------
    # Email via Resend.com
    # -------------------------------------------------------------------------
    if "email" in channels:
        email_target = analyst_email or getattr(settings, "ALERT_EMAIL", None)
        resend_key = getattr(settings, "RESEND_API_KEY", None)

        if resend_key and email_target:
            try:
                import httpx
                body = {
                    "from": getattr(settings, "EMAIL_FROM", "alerts@finshield.ai"),
                    "to": [email_target],
                    "subject": f"[FinShield] {severity.upper()} Fraud Alert -- {amount_str} at {merchant_str}",
                    "html": _build_email_html(
                        alert_id=alert_id,
                        fraud_score=fraud_score,
                        severity=severity,
                        decision=decision,
                        amount_str=amount_str,
                        merchant_str=merchant_str,
                        rules_str=rules_str,
                    ),
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_key}"},
                        json=body,
                    )
                if resp.status_code in (200, 201):
                    results["email"] = "sent"
                    logger.info("Alert email sent | alert=%s to=%s", alert_id, email_target)
                else:
                    results["email"] = f"failed:{resp.status_code}"
                    logger.warning("Resend email failed: %s %s", resp.status_code, resp.text[:200])
            except Exception as exc:
                results["email"] = f"error:{exc}"
                logger.warning("Email notification error: %s", exc)
        else:
            results["email"] = "skipped:no_key"

    # -------------------------------------------------------------------------
    # SMS via Twilio
    # -------------------------------------------------------------------------
    if "sms" in channels and customer_phone:
        twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        twilio_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        twilio_from = getattr(settings, "TWILIO_FROM_NUMBER", None)

        if twilio_sid and twilio_token and twilio_from:
            try:
                import httpx, base64
                message = (
                    f"FinShield Alert: {decision} - {amount_str} at {merchant_str}. "
                    f"Score: {fraud_score:.0%}. Ref: {alert_id[:8]}"
                )
                creds = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json",
                        headers={"Authorization": f"Basic {creds}"},
                        data={"From": twilio_from, "To": customer_phone, "Body": message},
                    )
                if resp.status_code in (200, 201):
                    results["sms"] = "sent"
                    logger.info("Alert SMS sent | alert=%s to=%s", alert_id, customer_phone)
                else:
                    results["sms"] = f"failed:{resp.status_code}"
                    logger.warning("Twilio SMS failed: %s", resp.status_code)
            except Exception as exc:
                results["sms"] = f"error:{exc}"
                logger.warning("SMS notification error: %s", exc)
        else:
            results["sms"] = "skipped:no_key"

    results["in_app"] = "always_available"
    return results


def _build_email_html(
    *,
    alert_id: str,
    fraud_score: float,
    severity: str,
    decision: str,
    amount_str: str,
    merchant_str: str,
    rules_str: str,
) -> str:
    severity_color = {
        "critical": "#EF4444",
        "high":     "#F97316",
        "medium":   "#EAB308",
        "low":      "#22C55E",
    }.get(severity, "#6B7280")

    return f"""
    <html><body style="font-family:sans-serif;background:#0A0A0F;color:#E5E7EB;padding:24px;">
      <div style="max-width:560px;margin:0 auto;background:#111118;border:1px solid #1E1E2E;border-radius:8px;padding:24px;">
        <h2 style="color:{severity_color};margin-top:0;">
          FinShield AI -- Fraud Alert
        </h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#9CA3AF;">Alert ID</td>
              <td style="padding:6px 0;font-family:monospace;">{alert_id[:16]}...</td></tr>
          <tr><td style="padding:6px 0;color:#9CA3AF;">Decision</td>
              <td style="padding:6px 0;font-weight:bold;color:{severity_color};">{decision}</td></tr>
          <tr><td style="padding:6px 0;color:#9CA3AF;">Fraud Score</td>
              <td style="padding:6px 0;">{fraud_score:.1%}</td></tr>
          <tr><td style="padding:6px 0;color:#9CA3AF;">Amount</td>
              <td style="padding:6px 0;">{amount_str}</td></tr>
          <tr><td style="padding:6px 0;color:#9CA3AF;">Merchant</td>
              <td style="padding:6px 0;">{merchant_str}</td></tr>
          <tr><td style="padding:6px 0;color:#9CA3AF;">Triggered Rules</td>
              <td style="padding:6px 0;">{rules_str}</td></tr>
        </table>
        <p style="margin-bottom:0;color:#6B7280;font-size:12px;">
          Log in to your FinShield dashboard to review and take action on this alert.
        </p>
      </div>
    </body></html>
    """
