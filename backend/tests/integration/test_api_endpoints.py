"""Integration tests for transaction API endpoints.

Uses the httpx AsyncClient fixture from conftest.py with a real in-memory DB.
"""
import uuid
from datetime import datetime, timezone

import pytest


def make_entity_payload(name: str = "Test Entity", entity_type: str = "individual") -> dict:
    return {
        "name": name,
        "entity_type": entity_type,
        "external_id": str(uuid.uuid4()),
        "kyc_status": "verified",
    }


def make_transaction_payload(source_entity_id: str) -> dict:
    return {
        "external_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "source_entity_id": source_entity_id,
        "amount": "250.00",
        "currency": "USD",
        "transaction_type": "payment",
        "channel": "online",
        "status": "pending",
        "country_code": "US",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_transactions_empty(client):
    response = await client.post(
        "/api/v1/transactions/search",
        json={"page": 1, "page_size": 20},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_transaction_not_found(client):
    response = await client.get(f"/api/v1/transactions/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"
