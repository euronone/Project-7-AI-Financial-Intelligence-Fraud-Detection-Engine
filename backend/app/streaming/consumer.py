from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()


class EventConsumer:
    """Consumes transaction events from Azure Event Hubs (Kafka-compatible).

    In development mode this acts as a no-op stub that logs messages instead of
    connecting to a real broker.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = False

    async def start(self) -> None:
        """Begin consuming events.  In dev mode, log and return immediately."""
        if self._settings.app_env == "development":
            logger.info(
                "event_consumer_skipped",
                reason="Event Hubs not configured in development",
            )
            return

        self._running = True
        logger.info("event_consumer_started")
        asyncio.ensure_future(self._consume_loop())

    async def stop(self) -> None:
        """Gracefully shut down the consumer."""
        self._running = False
        logger.info("event_consumer_stopped")

    async def _consume_loop(self) -> None:
        """Poll events from the broker until stopped.

        In production this would iterate over Event Hub partitions, commit
        offsets, and route events to `process_event`.
        """

        retry_delay = 1.0
        max_delay = 30.0

        while self._running:
            try:
                # Placeholder: real implementation would read from
                # azure.eventhub.aio.EventHubConsumerClient here.
                await asyncio.sleep(1.0)
                retry_delay = 1.0
            except Exception:
                logger.exception("event_consumer_error")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    async def process_event(self, event: dict[str, Any]) -> None:
        """Route an incoming event to the stream processor."""
        from app.streaming.processor import stream_processor

        event_type = event.get("type", "transaction")
        logger.info("event_received", event_type=event_type)

        if event_type == "transaction":
            await stream_processor.process_transaction(event.get("data", {}))
        else:
            logger.warning("event_type_unknown", event_type=event_type)


event_consumer = EventConsumer()
