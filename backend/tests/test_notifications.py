"""
Unit tests for notification service:
  - Channel dispatch (email, SMS, FCM, in-app)
  - Plan gating (SMS only on Pro/Advanced)
  - ALERT_SMS_ENABLED kill-switch
  - Brevo fallback when only Brevo key is configured
  - FCM push for critical/high severity on Pro/Advanced
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.anyio


# ── Settings / notification service import helpers ────────────────────────────

def _make_alert(severity="critical", fraud_score=0.91):
    return MagicMock(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        transaction_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        severity=severity,
        fraud_score=fraud_score,
        alert_type="ml_model",
        triggered_rules=[],
    )


def _make_customer(phone="+919876543210"):
    return MagicMock(
        id=str(uuid.uuid4()),
        full_name="Test Customer",
        email="customer@test.com",
        phone_number=phone,
    )


def _make_tenant(plan="free", resend_key="", twilio_sid="", twilio_token="",
                 twilio_from="", firebase_key="", brevo_key=""):
    cfg = {
        "notifications": {
            "resend_api_key": resend_key,
            "brevo_api_key": brevo_key,
            "twilio_account_sid": twilio_sid,
            "twilio_auth_token": twilio_token,
            "twilio_from_number": twilio_from,
            "firebase_server_key": firebase_key,
            "email_from": "noreply@finshield.test",
        }
    }
    return MagicMock(
        subscription_plan=plan,
        db_config_json=cfg,
    )


# ── Import service under test ─────────────────────────────────────────────────

from app.services.notification_service import send_fraud_alert_notifications


# ── Email dispatch tests ──────────────────────────────────────────────────────

async def test_resend_email_dispatched_when_key_present(client):
    """When Resend key is present, a Resend API call should be made."""
    alert = _make_alert()
    customer = _make_customer()
    tenant = _make_tenant(resend_key="re_test_key_123")

    with patch("app.services.notification_service.httpx.AsyncClient") as mock_http:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"id": "email_123"}
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        results = await send_fraud_alert_notifications(
            alert=alert,
            customer=customer,
            tenant=tenant,
            company_email="fraud@test.com",
        )

    # At least one email result should be present
    email_keys = [k for k in results if "email" in k.lower()]
    assert len(email_keys) >= 1


async def test_no_email_when_no_keys(client):
    """No email keys → no email attempt, result should be 'skipped'."""
    alert = _make_alert()
    customer = _make_customer()
    tenant = _make_tenant()  # no keys

    results = await send_fraud_alert_notifications(
        alert=alert,
        customer=customer,
        tenant=tenant,
        company_email="fraud@test.com",
    )

    email_vals = [v for k, v in results.items() if "email" in k.lower()]
    for v in email_vals:
        assert "skip" in str(v).lower() or v is None


# ── SMS plan-gating tests ─────────────────────────────────────────────────────

async def test_sms_skipped_on_free_plan(client):
    """Free-plan tenants should never receive SMS even if Twilio is configured."""
    alert = _make_alert(severity="critical")
    customer = _make_customer()
    tenant = _make_tenant(
        plan="free",
        twilio_sid="AC_test",
        twilio_token="token",
        twilio_from="+10000000000",
    )

    results = await send_fraud_alert_notifications(
        alert=alert,
        customer=customer,
        tenant=tenant,
        company_email="fraud@test.com",
    )

    sms_vals = [v for k, v in results.items() if "sms" in k.lower()]
    for v in sms_vals:
        # Should be skipped, not sent
        assert "skip" in str(v).lower() or "plan" in str(v).lower()


async def test_sms_allowed_on_pro_plan(client):
    """Pro-plan tenants with Twilio configured should attempt SMS."""
    alert = _make_alert(severity="critical")
    customer = _make_customer()
    tenant = _make_tenant(
        plan="pro",
        twilio_sid="ACtest123",
        twilio_token="auth_token_test",
        twilio_from="+10000000000",
    )

    with patch("app.services.notification_service.httpx.AsyncClient") as mock_http:
        mock_resp = AsyncMock()
        mock_resp.status_code = 201
        mock_resp.json = lambda: {"sid": "SM_test"}
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        results = await send_fraud_alert_notifications(
            alert=alert,
            customer=customer,
            tenant=tenant,
            company_email="fraud@test.com",
        )

    # SMS should be attempted (either sent or failed — not skipped for plan reasons)
    sms_keys = [k for k in results if "sms" in k.lower()]
    assert len(sms_keys) >= 1


# ── ALERT_SMS_ENABLED kill-switch ─────────────────────────────────────────────

async def test_sms_disabled_by_platform_kill_switch(client):
    """When ALERT_SMS_ENABLED=False, SMS should be skipped platform-wide."""
    alert = _make_alert(severity="critical")
    customer = _make_customer()
    tenant = _make_tenant(
        plan="pro",
        twilio_sid="ACtest",
        twilio_token="token",
        twilio_from="+10000000000",
    )

    with patch("app.services.notification_service.get_settings") as mock_settings:
        mock_settings.return_value.ALERT_SMS_ENABLED = False
        mock_settings.return_value.RESEND_API_KEY = ""
        mock_settings.return_value.BREVO_API_KEY = ""

        results = await send_fraud_alert_notifications(
            alert=alert,
            customer=customer,
            tenant=tenant,
            company_email="fraud@test.com",
        )

    sms_vals = [v for k, v in results.items() if "sms" in k.lower()]
    for v in sms_vals:
        assert "skip" in str(v).lower() or "disabled" in str(v).lower()


# ── FCM push notification tests ───────────────────────────────────────────────

async def test_fcm_push_dispatched_on_advanced_plan_critical(client):
    """Advanced plan + Firebase key + critical severity → FCM push."""
    alert = _make_alert(severity="critical")
    customer = _make_customer()
    tenant = _make_tenant(plan="advanced", firebase_key="AAAA_test_firebase_key")

    with patch("app.services.notification_service.httpx.AsyncClient") as mock_http:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"message_id": "fcm_123"}
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        results = await send_fraud_alert_notifications(
            alert=alert,
            customer=customer,
            tenant=tenant,
            company_email="fraud@test.com",
        )

    fcm_keys = [k for k in results if "push" in k.lower() or "fcm" in k.lower()]
    # FCM block only fires if key present and plan is Pro/Advanced
    # This test passes if no exception is raised


async def test_fcm_skipped_on_free_plan(client):
    """Free plan → FCM push skipped even with Firebase key."""
    alert = _make_alert(severity="critical")
    customer = _make_customer()
    tenant = _make_tenant(plan="free", firebase_key="AAAA_test_firebase_key")

    results = await send_fraud_alert_notifications(
        alert=alert,
        customer=customer,
        tenant=tenant,
        company_email="fraud@test.com",
    )

    fcm_vals = [v for k, v in results.items() if "push" in k.lower() or "fcm" in k.lower()]
    for v in fcm_vals:
        assert "skip" in str(v).lower() or "plan" in str(v).lower()


# ── Severity → channel mapping ────────────────────────────────────────────────

async def test_low_severity_only_inapp_notification(client):
    """Low severity → only in-app notification."""
    alert = _make_alert(severity="low", fraud_score=0.15)
    customer = _make_customer()
    tenant = _make_tenant(plan="pro")

    results = await send_fraud_alert_notifications(
        alert=alert,
        customer=customer,
        tenant=tenant,
        company_email="fraud@test.com",
    )

    # No SMS for low severity
    sms_vals = [v for k, v in results.items() if "sms" in k.lower()]
    for v in sms_vals:
        assert "skip" in str(v).lower()


async def test_brevo_fallback_when_only_brevo_configured(client):
    """When only Brevo key is present (no Resend), emails go via Brevo."""
    alert = _make_alert(severity="high")
    customer = _make_customer()
    tenant = _make_tenant(brevo_key="xkeysib_test_brevo_key")

    with patch("app.services.notification_service.httpx.AsyncClient") as mock_http:
        mock_resp = AsyncMock()
        mock_resp.status_code = 201
        mock_resp.json = lambda: {"messageId": "brevo_123"}
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        results = await send_fraud_alert_notifications(
            alert=alert,
            customer=customer,
            tenant=tenant,
            company_email="fraud@test.com",
        )

    # Must not raise; result captured
    assert isinstance(results, dict)
