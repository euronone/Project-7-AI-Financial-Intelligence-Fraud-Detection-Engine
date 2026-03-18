"""Azure Event Hub consumer — reads from the transactions hub and routes to processor.

Runs as the `backend-stream` container (separate from the API container).
Maintains reliable offset checkpointing via Azure Blob Storage.
Falls back gracefully when Event Hub is not configured (dev environment).
"""
import asyncio
import signal
import sys

import structlog

from app.config import get_settings
from app.core.middleware import configure_structlog
from app.streaming.processor import process_event_hub_message

logger = structlog.get_logger(__name__)
settings = get_settings()

_shutdown_event = asyncio.Event()


def _handle_signal(sig) -> None:
    logger.info("consumer_shutdown_signal", signal=sig)
    _shutdown_event.set()


async def run_consumer() -> None:
    """Main consumer loop — reads from Azure Event Hub and dispatches to processor."""
    if not settings.event_hub_connection_string:
        logger.info(
            "event_hub_consumer_disabled",
            reason="EVENT_HUB_CONNECTION_STRING not configured — running in stub mode",
        )
        await _stub_consumer()
        return

    try:
        from azure.eventhub.aio import EventHubConsumerClient
        from azure.eventhub.extensions.checkpointstoreblob.aio import (
            BlobCheckpointStore,
        )
    except ImportError:
        logger.warning(
            "event_hub_consumer_disabled",
            reason="azure-eventhub or azure-storage-blob not installed",
        )
        await _stub_consumer()
        return

    checkpoint_store = None
    if settings.azure_storage_connection_string:
        checkpoint_store = BlobCheckpointStore.from_connection_string(
            settings.azure_storage_connection_string,
            container_name="eventhub-checkpoints",
        )

    client = EventHubConsumerClient.from_connection_string(
        settings.event_hub_connection_string,
        consumer_group=settings.event_hub_consumer_group,
        eventhub_name=settings.event_hub_transactions_name,
        checkpoint_store=checkpoint_store,
    )

    async def on_event(partition_context, event) -> None:
        raw = event.body_as_str(encoding="utf-8")
        await process_event_hub_message(raw)
        await partition_context.update_checkpoint(event)

    async def on_error(partition_context, error) -> None:
        logger.error(
            "event_hub_consumer_error",
            partition=partition_context.partition_id if partition_context else None,
            error=str(error),
        )

    logger.info(
        "event_hub_consumer_started",
        hub=settings.event_hub_transactions_name,
        consumer_group=settings.event_hub_consumer_group,
    )

    async with client:
        receive_task = asyncio.create_task(
            client.receive(
                on_event=on_event,
                on_error=on_error,
                starting_position="-1",  # Start from latest
            )
        )
        await _shutdown_event.wait()
        receive_task.cancel()

    logger.info("event_hub_consumer_stopped")


async def _stub_consumer() -> None:
    """No-op consumer used in development when Event Hub is not configured."""
    logger.info("event_hub_stub_consumer_running")
    await _shutdown_event.wait()


def main() -> None:
    """Entry point for the stream processor container."""
    configure_structlog()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

    try:
        loop.run_until_complete(run_consumer())
    finally:
        loop.close()
        logger.info("consumer_exit")


if __name__ == "__main__":
    main()
