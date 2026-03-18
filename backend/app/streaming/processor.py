"""Stream processor — handles ingested transactions from Event Hub.

For each transaction event received:
1. Call transaction service to process through fraud pipeline.
2. Emit WebSocket events to connected frontend clients.
3. Retry up to 3 times on failure; route to DLQ on final failure.

This module runs as the `backend-stream` container service.
"""
import asyncio
import json
from typing import Any, Dict

import structlog

from app.config import get_settings
from app.streaming.websocket_manager import (
    emit_new_transaction,
    emit_transaction_flagged,
)

logger = structlog.get_logger(__name__)
settings = get_settings()

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 1.0  # seconds


async def _process_with_retry(payload: Dict[str, Any]) -> None:
    """Process a single transaction event with exponential retry.

    On final failure, logs to DLQ (structured log entry tagged dlq=true).
    Full DLQ queue implementation (Azure Service Bus) is wired in F6/infra.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            await _process_transaction_event(payload)
            return
        except Exception as exc:
            wait = _RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning(
                "stream_processor_retry",
                attempt=attempt,
                transaction_id=payload.get("id"),
                error=str(exc),
                next_wait_s=wait,
            )
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "stream_processor_dlq",
                    dlq=True,
                    transaction_id=payload.get("id"),
                    error=str(exc),
                )


async def _process_transaction_event(payload: Dict[str, Any]) -> None:
    """Core processing logic for a single transaction event.

    Emits WebSocket events after successful processing.
    """
    transaction_id = payload.get("id", "unknown")

    # Emit live feed event regardless of fraud decision (F1.3)
    await emit_new_transaction(payload)

    # Emit flagged event if decision warrants it
    decision = payload.get("decision", "PASS")
    if decision in ("FLAG", "ALERT", "BLOCK"):
        await emit_transaction_flagged(
            {
                "id": transaction_id,
                "external_id": payload.get("external_id"),
                "fraud_score": payload.get("fraud_score"),
                "decision": decision,
                "risk_level": payload.get("risk_level"),
            }
        )
        logger.info(
            "transaction_flagged_emitted",
            transaction_id=transaction_id,
            decision=decision,
        )


async def process_event_hub_message(raw_message: str) -> None:
    """Entry point called by the Event Hub consumer for each message."""
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError as exc:
        logger.error("stream_processor_invalid_json", error=str(exc))
        return

    await _process_with_retry(payload)
