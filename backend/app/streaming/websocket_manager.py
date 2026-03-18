"""Socket.IO WebSocket manager.

Manages namespaces and provides helpers to emit real-time events
to connected frontend clients.

Namespaces (per API spec):
- /transactions — live transaction feed (new_transaction, transaction_flagged)
- /alerts       — fraud alert notifications (new_alert, alert_updated)
- /dashboard    — dashboard metric updates (metrics_update, model_status)
"""
from typing import Any, Dict

import socketio
import structlog

logger = structlog.get_logger(__name__)

# Async Socket.IO server — mounted onto the FastAPI ASGI app in main.py
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Tightened via CORS middleware; Socket.IO CORS is separate
    logger=False,
    engineio_logger=False,
)


# ── Namespace: /transactions ──────────────────────────────────────────────────

class TransactionNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ: Dict) -> None:
        logger.info("ws_client_connected", namespace="/transactions", sid=sid)

    async def on_disconnect(self, sid: str) -> None:
        logger.info("ws_client_disconnected", namespace="/transactions", sid=sid)


# ── Namespace: /alerts ────────────────────────────────────────────────────────

class AlertsNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ: Dict) -> None:
        logger.info("ws_client_connected", namespace="/alerts", sid=sid)

    async def on_disconnect(self, sid: str) -> None:
        logger.info("ws_client_disconnected", namespace="/alerts", sid=sid)


# ── Namespace: /dashboard ─────────────────────────────────────────────────────

class DashboardNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ: Dict) -> None:
        logger.info("ws_client_connected", namespace="/dashboard", sid=sid)

    async def on_disconnect(self, sid: str) -> None:
        logger.info("ws_client_disconnected", namespace="/dashboard", sid=sid)


# Register namespaces
sio.register_namespace(TransactionNamespace("/transactions"))
sio.register_namespace(AlertsNamespace("/alerts"))
sio.register_namespace(DashboardNamespace("/dashboard"))


# ── Emit helpers ──────────────────────────────────────────────────────────────

async def emit_new_transaction(payload: Dict[str, Any]) -> None:
    """Emit a new_transaction event to all clients on /transactions."""
    await sio.emit("new_transaction", payload, namespace="/transactions")
    logger.debug("ws_emit", event="new_transaction", transaction_id=payload.get("id"))


async def emit_transaction_flagged(payload: Dict[str, Any]) -> None:
    """Emit a transaction_flagged event — decision is FLAG, ALERT, or BLOCK."""
    await sio.emit("transaction_flagged", payload, namespace="/transactions")
    logger.info(
        "ws_emit",
        event="transaction_flagged",
        transaction_id=payload.get("id"),
        decision=payload.get("decision"),
    )


async def emit_new_alert(payload: Dict[str, Any]) -> None:
    await sio.emit("new_alert", payload, namespace="/alerts")


async def emit_metrics_update(payload: Dict[str, Any]) -> None:
    await sio.emit("metrics_update", payload, namespace="/dashboard")
