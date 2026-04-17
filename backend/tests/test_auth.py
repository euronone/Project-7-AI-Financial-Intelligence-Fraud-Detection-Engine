"""
Unit tests for authentication endpoints:
  POST /auth/signup
  POST /auth/login
  POST /auth/refresh
  GET  /auth/me
  POST /auth/logout
  POST /auth/forgot-password
  POST /auth/change-password
"""

import pytest
import uuid

pytestmark = pytest.mark.anyio


# ── Helpers ────────────────────────────────────────────────────────────────────

def _unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@finshield.test"


async def _signup(client, email: str | None = None, password: str = "TestPass123!@#"):
    email = email or _unique_email()
    resp = await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
        "organization_name": f"Test Org {uuid.uuid4().hex[:6]}",
        "institution_type": "fintech",
        "subscription_plan": "free",
    })
    return resp, email


async def _login(client, email: str, password: str = "TestPass123!@#"):
    resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    return resp


async def _signup_and_login(client):
    email = _unique_email()
    await _signup(client, email)
    login_resp = await _login(client, email)
    tokens = login_resp.json()
    return tokens, email


# ── Signup tests ──────────────────────────────────────────────────────────────

async def test_signup_success(client):
    resp, email = await _signup(client)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email
    assert "id" in data


async def test_signup_duplicate_email_rejected(client):
    email = _unique_email()
    r1, _ = await _signup(client, email)
    assert r1.status_code == 201
    r2, _ = await _signup(client, email)
    assert r2.status_code == 409  # ConflictException


async def test_signup_missing_fields_rejected(client):
    resp = await client.post("/api/v1/auth/signup", json={"email": "missing@test.com"})
    assert resp.status_code == 422


async def test_signup_invalid_email_rejected(client):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "not-an-email",
        "password": "TestPass123!@#",
        "full_name": "X",
        "organization_name": "Y",
        "institution_type": "fintech",
    })
    assert resp.status_code == 422


async def test_signup_weak_password_rejected(client):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": _unique_email(),
        "password": "123",
        "full_name": "X",
        "organization_name": "Y",
        "institution_type": "fintech",
    })
    # Either 422 (validation) or 400 (business logic)
    assert resp.status_code in (400, 422)


# ── Login tests ───────────────────────────────────────────────────────────────

async def test_login_success_returns_tokens(client):
    tokens, _ = await _signup_and_login(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens.get("token_type") == "bearer"


async def test_login_wrong_password_rejected(client):
    email = _unique_email()
    await _signup(client, email)
    resp = await _login(client, email, password="WrongPass999!")
    assert resp.status_code == 401


async def test_login_unknown_email_rejected(client):
    resp = await _login(client, "nobody@unknown.test")
    assert resp.status_code == 401


async def test_login_sets_correct_token_type(client):
    tokens, _ = await _signup_and_login(client)
    assert tokens["token_type"].lower() == "bearer"


# ── /me tests ────────────────────────────────────────────────────────────────

async def test_me_returns_current_user(client):
    tokens, email = await _signup_and_login(client)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == email


async def test_me_unauthenticated_rejected(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token_rejected(client):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


# ── Token refresh tests ──────────────────────────────────────────────────────

async def test_refresh_returns_new_access_token(client):
    tokens, _ = await _signup_and_login(client)
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    # New token must differ (timestamp embedded)
    assert new_tokens["access_token"] != tokens["access_token"]


async def test_refresh_invalid_token_rejected(client):
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "not-a-real-token",
    })
    assert resp.status_code == 401


# ── Change password tests ─────────────────────────────────────────────────────

async def test_change_password_success(client):
    tokens, email = await _signup_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post("/api/v1/auth/change-password", json={
        "current_password": "TestPass123!@#",
        "new_password": "NewPass456!@#",
    }, headers=headers)
    assert resp.status_code == 200

    # Old password should now fail
    old_login = await _login(client, email, "TestPass123!@#")
    assert old_login.status_code == 401

    # New password should succeed
    new_login = await _login(client, email, "NewPass456!@#")
    assert new_login.status_code == 200


async def test_change_password_wrong_current_rejected(client):
    tokens, _ = await _signup_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post("/api/v1/auth/change-password", json={
        "current_password": "WrongOldPass!",
        "new_password": "NewPass456!@#",
    }, headers=headers)
    assert resp.status_code in (400, 401)


# ── Forgot password tests ─────────────────────────────────────────────────────

async def test_forgot_password_valid_email_returns_200(client):
    email = _unique_email()
    await _signup(client, email)
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    # Always 200 to not leak whether email exists
    assert resp.status_code == 200


async def test_forgot_password_unknown_email_still_returns_200(client):
    resp = await client.post("/api/v1/auth/forgot-password", json={
        "email": "unknown@unknown.test"
    })
    assert resp.status_code == 200
