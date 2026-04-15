"""Tests for health-check endpoints."""

from httpx import AsyncClient


class TestHealthEndpoints:
    async def test_basic_health_returns_200(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_basic_health_response_schema(self, client: AsyncClient):
        data = (await client.get("/api/v1/health")).json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    async def test_basic_health_app_name(self, client: AsyncClient):
        data = (await client.get("/api/v1/health")).json()
        assert data["app"] == "FinShield AI"

    async def test_detailed_health_returns_200(self, client: AsyncClient):
        response = await client.get("/api/v1/health/detailed")
        assert response.status_code == 200

    async def test_detailed_health_has_checks(self, client: AsyncClient):
        data = (await client.get("/api/v1/health/detailed")).json()
        assert "status" in data
        assert "checks" in data
        assert "api" in data["checks"]
        assert "database" in data["checks"]

    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200

    async def test_root_contains_docs_link(self, client: AsyncClient):
        data = (await client.get("/")).json()
        assert "docs" in data
        assert "health" in data
