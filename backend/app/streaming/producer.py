"""Azure Event Hub producer — publishes transactions to the Event Hub.

Uses the Kafka-compatible endpoint of Azure Event Hubs.
Falls back silently in development if connection string is not configured.
"""
import json
from typing import Any, Dict

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class EventHubProducer:
    """Wraps the azure-eventhub SDK producer for transaction publishing."""

    def __init__(self) -> None:
        self._producer = None
        self._enabled = bool(settings.event_hub_connection_string)

    async def start(self) -> None:
        if not self._enabled:
            logger.info("event_hub_producer_disabled", reason="no connection string configured")
            return
        try:
            from azure.eventhub.aio import EventHubProducerClient

            self._producer = EventHubProducerClient.from_connection_string(
                settings.event_hub_connection_string,
                eventhub_name=settings.event_hub_transactions_name,
            )
            logger.info("event_hub_producer_started")
        except ImportError:
            logger.warning(
                "event_hub_producer_disabled",
                reason="azure-eventhub package not installed",
            )
            self._enabled = False

    async def stop(self) -> None:
        if self._producer:
            await self._producer.close()
            logger.info("event_hub_producer_stopped")

    async def publish_transaction(self, payload: Dict[str, Any]) -> None:
        """Publish a single transaction payload to the transactions Event Hub."""
        if not self._enabled or not self._producer:
            logger.debug("event_hub_skip_publish", payload_id=payload.get("id"))
            return

        try:
            from azure.eventhub import EventData

            async with self._producer:
                batch = await self._producer.create_batch()
                batch.add(EventData(json.dumps(payload, default=str)))
                await self._producer.send_batch(batch)

            logger.debug("event_hub_published", transaction_id=payload.get("id"))
        except Exception as exc:
            logger.error(
                "event_hub_publish_failed",
                transaction_id=payload.get("id"),
                error=str(exc),
            )


# Module-level singleton — shared across the application lifecycle
producer = EventHubProducer()
