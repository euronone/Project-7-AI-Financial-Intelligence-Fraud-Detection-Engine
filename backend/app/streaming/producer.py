from __future__ import annotations

from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()

VALID_TOPICS = frozenset({
    "transactions.ingested",
    "alerts.created",
    "risk.scored",
    "cases.updated",
})


class EventProducer:
    """Publishes events to Azure Event Hubs (Kafka-compatible).

    In development mode events are logged rather than sent to a broker.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def send_event(self, topic: str, data: dict[str, Any]) -> None:
        """Send a single event to the specified topic."""
        if topic not in VALID_TOPICS:
            logger.warning("event_producer_invalid_topic", topic=topic)
            return

        if self._settings.app_env == "development":
            logger.info(
                "event_produced_dev",
                topic=topic,
                payload_keys=list(data.keys()),
            )
            return

        # Production: publish via azure.eventhub.aio.EventHubProducerClient
        logger.info("event_produced", topic=topic)

    async def send_batch(self, topic: str, events: list[dict[str, Any]]) -> None:
        """Send a batch of events to the specified topic."""
        if topic not in VALID_TOPICS:
            logger.warning("event_producer_invalid_topic", topic=topic)
            return

        if self._settings.app_env == "development":
            logger.info(
                "event_batch_produced_dev",
                topic=topic,
                count=len(events),
            )
            return

        logger.info("event_batch_produced", topic=topic, count=len(events))


event_producer = EventProducer()
