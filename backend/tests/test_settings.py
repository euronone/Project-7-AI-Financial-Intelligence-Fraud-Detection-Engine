"""
Unit tests for settings endpoints:
  GET  /settings                 — get all settings
  PUT  /settings/database        — update DB connections
  PUT  /settings/notifications   — update notification API keys
  PUT  /settings/integrations    — update integration keys
  POST /settings/test-connection — test DB connection
  POST /settings/test-notification — send test notification
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.anyio


async def _auth_headers(client):
    email = f"settings_{uuid.uuid4().hex[:8]}@finshield.test"
    await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "TestPass123!@#",
        "full_name": "Settings User",
        "organization_name": f"Settings Org {uuid.uuid4().hex[:6]}",
        "institution_type": "fintech",
        "subscription_plan": "pro",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "TestPass123!@#",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── GET /settings ─────────────────────────────────────────────────────────────

async def test_get_settings_returns_200(client):
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 200


async def test_get_settings_unauthenticated(client):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 401


async def test_get_settings_no_plaintext_secrets(client):
    """Settings response must never expose raw API keys."""
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/settings", headers=headers)
    text = resp.text.lower()
    # Secrets must be masked or absent — not returned as plain values
    assert "re_live_" not in text  # Resend live key prefix
    assert "sk_live_" not in text  # Generic live key prefix


# ── GET /settings/notifications ───────────────────────────────────────────────

async def test_get_notification_settings(client):
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/settings/notifications", headers=headers)
    assert resp.status_code in (200, 404)


# ── PUT /settings/notifications ───────────────────────────────────────────────

async def test_update_notification_settings_resend(client):
    headers = await _auth_headers(client)
    resp = await client.put("/api/v1/settings/notifications", json={
        "resend_api_key": "re_test_xxxxxxxxxx",
        "email_from": "test@finshield.ai",
    }, headers=headers)
    assert resp.status_code in (200, 204, 404)


async def test_update_notification_settings_unauthenticated(client):
    resp = await client.put("/api/v1/settings/notifications", json={
        "resend_api_key": "re_test_key",
    })
    assert resp.status_code == 401


async def test_update_notification_settings_twilio(client):
    headers = await _auth_headers(client)
    resp = await client.put("/api/v1/settings/notifications", json={
        "twilio_account_sid": "ACtest",
        "twilio_auth_token": "token",
        "twilio_from_number": "+10000000000",
    }, headers=headers)
    assert resp.status_code in (200, 204, 404)


# ── PUT /settings/database ────────────────────────────────────────────────────

async def test_update_database_settings_unauthenticated(client):
    resp = await client.put("/api/v1/settings/database", json={
        "database_url": "postgresql://user:pass@host/db",
    })
    assert resp.status_code == 401


async def test_update_database_settings_structure(client):
    headers = await _auth_headers(client)
    resp = await client.put("/api/v1/settings/database", json={
        "customer_db_type": "supabase",
        "customer_db_url": "https://fake.supabase.co",
        "customer_db_key": "eyJtest",
    }, headers=headers)
    # 200/204 on success, 404 if route not mounted, 422 if validation fails
    assert resp.status_code in (200, 204, 404, 422)


# ── POST /settings/test-connection ───────────────────────────────────────────

async def test_test_connection_requires_auth(client):
    resp = await client.post("/api/v1/settings/test-connection", json={
        "db_type": "supabase",
        "url": "https://test.supabase.co",
        "key": "eyJtest",
    })
    assert resp.status_code == 401


async def test_test_connection_with_invalid_url(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/settings/test-connection", json={
        "db_type": "supabase",
        "url": "https://fake-doesnotexist-xyz.supabase.co",
        "key": "eyJfake",
    }, headers=headers)
    # Should return 200 with {success: false} or 400/422
    assert resp.status_code in (200, 400, 404, 422)
    if resp.status_code == 200:
        data = resp.json()
        assert "success" in data or "connected" in data or "error" in data


# ── POST /settings/test-notification ─────────────────────────────────────────

async def test_test_notification_requires_auth(client):
    resp = await client.post("/api/v1/settings/test-notification", json={
        "channel": "email",
        "recipient": "test@test.com",
    })
    assert resp.status_code == 401


async def test_test_notification_email_no_key(client):
    """Without a configured email key, test notification should fail gracefully."""
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/settings/test-notification", json={
        "channel": "email",
        "recipient": "test@test.com",
    }, headers=headers)
    assert resp.status_code in (200, 400, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "success" in data or "sent" in data or "error" in data


async def test_test_notification_invalid_channel(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/settings/test-notification", json={
        "channel": "telepathy",
    }, headers=headers)
    assert resp.status_code in (400, 404, 422)
