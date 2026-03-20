from __future__ import annotations

from typing import Any

import structlog

from app.config import get_settings
from app.ml.pipeline import run_pipeline
from app.streaming.producer import event_producer
from app.streaming.websocket_manager import ws_manager

logger = structlog.get_logger()

ALERT_THRESHOLD = 0.3


class StreamProcessor:
    """Orchestrates the ingest → ML pipeline → emit flow for transactions."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def process_transaction(self, transaction_data: dict[str, Any]) -> dict[str, Any]:
        """Run a single transaction through the scoring pipeline and emit results.

        Returns the pipeline result dict augmented with the original transaction id.
        """
        txn_id = transaction_data.get("id", "unknown")
        logger.info("stream_process_start", txn_id=txn_id)

        pipeline_result = run_pipeline(transaction_data)

        overall_score = pipeline_result.get("overall_score", 0.0)
        risk_level = pipeline_result.get("risk_level", "low")

        txn_event = {
            "id": txn_id,
            "fraud_score": overall_score,
            "risk_level": risk_level,
            **{k: v for k, v in transaction_data.items() if k in ("amount", "currency", "channel")},
        }

        await ws_manager.emit_transaction(txn_event)
        await event_producer.send_event("transactions.ingested", txn_event)

        if overall_score >= ALERT_THRESHOLD:
            alert_event = {
                "transaction_id": txn_id,
                "score": overall_score,
                "risk_level": risk_level,
                "risk_factors": pipeline_result.get("risk_factors", []),
            }
            await ws_manager.emit_alert(alert_event)
            await ws_manager.emit_transaction_flagged(txn_event)
            await event_producer.send_event("alerts.created", alert_event)

        await event_producer.send_event("risk.scored", {
            "transaction_id": txn_id,
            "overall_score": overall_score,
            "component_scores": pipeline_result.get("component_scores", {}),
        })

        await ws_manager.emit_dashboard_update({
            "type": "transaction_scored",
            "txn_id": txn_id,
            "risk_level": risk_level,
        })

        logger.info(
            "stream_process_complete",
            txn_id=txn_id,
            score=overall_score,
            risk_level=risk_level,
        )
        return {**pipeline_result, "transaction_id": txn_id}

    async def process_batch(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process multiple transactions sequentially and return all results."""
        results: list[dict[str, Any]] = []
        for txn in transactions:
            result = await self.process_transaction(txn)
            results.append(result)
        logger.info("stream_batch_complete", count=len(results))
        return results


stream_processor = StreamProcessor()
