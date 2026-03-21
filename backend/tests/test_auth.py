"""Tests for the authentication endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "http://test"


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        yield c


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_without_token(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_bad_token(async_client: AsyncClient):
    resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_users_list_without_token(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/users")
    assert resp.status_code == 401
