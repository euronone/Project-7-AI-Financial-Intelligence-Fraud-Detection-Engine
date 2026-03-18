"""Unit tests for TransactionService — mocks DB session."""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.entity import Entity, EntityType, KYCStatus, RiskLevel
from app.models.transaction import (
    Transaction,
    TransactionChannel,
    TransactionRiskLevel,
    TransactionStatus,
    TransactionType,
)
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import (
    _decision_from_score,
    _risk_level_from_score,
    _status_from_decision,
)


# ── Pure helper tests (no DB needed) ─────────────────────────────────────────

@pytest.mark.parametrize(
    "score, expected",
    [
        (0.0, TransactionRiskLevel.low),
        (0.25, TransactionRiskLevel.low),
        (0.3, TransactionRiskLevel.medium),
        (0.5, TransactionRiskLevel.medium),
        (0.6, TransactionRiskLevel.high),
        (0.75, TransactionRiskLevel.high),
        (0.8, TransactionRiskLevel.critical),
        (1.0, TransactionRiskLevel.critical),
    ],
)
def test_risk_level_from_score(score, expected):
    assert _risk_level_from_score(score) == expected


@pytest.mark.parametrize(
    "score, expected",
    [
        (0.1, "PASS"),
        (0.29, "PASS"),
        (0.3, "FLAG"),
        (0.59, "FLAG"),
        (0.6, "ALERT"),
        (0.79, "ALERT"),
        (0.8, "BLOCK"),
        (1.0, "BLOCK"),
    ],
)
def test_decision_from_score(score, expected):
    assert _decision_from_score(score) == expected


@pytest.mark.parametrize(
    "decision, expected_status",
    [
        ("BLOCK", TransactionStatus.blocked),
        ("ALERT", TransactionStatus.flagged),
        ("FLAG", TransactionStatus.flagged),
        ("PASS", TransactionStatus.pending),
    ],
)
def test_status_from_decision(decision, expected_status):
    result = _status_from_decision(TransactionStatus.pending, decision)
    assert result == expected_status


# ── TransactionService ingest (mocked DB) ────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_raises_conflict_on_duplicate_external_id():
    from app.core.exceptions import ConflictError
    from app.services.transaction_service import TransactionService

    db = AsyncMock()

    # Simulate existing transaction found
    existing_txn = MagicMock(spec=Transaction)
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing_txn
    db.execute = AsyncMock(return_value=execute_result)

    svc = TransactionService(db)
    data = TransactionCreate(
        external_id="TXN-001",
        source_entity_id=uuid.uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        transaction_type=TransactionType.payment,
        channel=TransactionChannel.online,
        processed_at="2026-03-17T10:00:00Z",
    )

    with pytest.raises(ConflictError):
        await svc.ingest(data)


@pytest.mark.asyncio
async def test_ingest_raises_not_found_for_missing_source_entity():
    from app.core.exceptions import NotFoundError
    from app.services.transaction_service import TransactionService

    db = AsyncMock()

    # No duplicate
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=execute_result)

    # Source entity not found
    db.get = AsyncMock(return_value=None)

    svc = TransactionService(db)
    data = TransactionCreate(
        external_id="TXN-002",
        source_entity_id=uuid.uuid4(),
        amount=Decimal("500.00"),
        currency="USD",
        transaction_type=TransactionType.transfer,
        channel=TransactionChannel.mobile,
        processed_at="2026-03-17T10:00:00Z",
    )

    with pytest.raises(NotFoundError):
        await svc.ingest(data)
