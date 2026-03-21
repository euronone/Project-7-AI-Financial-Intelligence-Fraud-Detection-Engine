from __future__ import annotations

from typing import Any

import socketio
import structlog

from app.config import get_settings

logger = structlog.get_logger()

NAMESPACES = ("/alerts", "/transactions", "/dashboard")


class SocketIOManager:
    """Manages Socket.IO server lifecycle and event emission."""

    def __init__(self) -> None:
        settings = get_settings()
        self.server = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=settings.cors_origins,
            logger=False,
            engineio_logger=False,
        )
        self._register_handlers()

    def _register_handlers(self) -> None:
        for ns in NAMESPACES:
            self.server.on("connect", namespace=ns)(self._make_connect_handler(ns))
            self.server.on("disconnect", namespace=ns)(self._make_disconnect_handler(ns))
            self.server.on("join", namespace=ns)(self._make_join_handler(ns))

    def _make_connect_handler(self, namespace: str):
        async def _on_connect(sid: str, environ: dict, auth: dict | None = None) -> None:
            logger.info("ws_connected", sid=sid, namespace=namespace)

        return _on_connect

    def _make_disconnect_handler(self, namespace: str):
        async def _on_disconnect(sid: str) -> None:
            logger.info("ws_disconnected", sid=sid, namespace=namespace)

        return _on_disconnect

    def _make_join_handler(self, namespace: str):
        async def _on_join(sid: str, data: dict) -> None:
            user_id = data.get("user_id")
            if user_id:
                room = f"user:{user_id}"
                self.server.enter_room(sid, room, namespace=namespace)
                logger.info("ws_joined_room", sid=sid, room=room, namespace=namespace)

        return _on_join

    async def emit_alert(self, alert_data: dict[str, Any]) -> None:
        """Emit a fraud alert event to all clients on the /alerts namespace."""
        await self.server.emit("new_alert", alert_data, namespace="/alerts")
        logger.debug("ws_emit_alert", alert_id=alert_data.get("id"))

    async def emit_alert_updated(self, alert_data: dict[str, Any]) -> None:
        """Emit an alert status update to the /alerts namespace."""
        await self.server.emit("alert_updated", alert_data, namespace="/alerts")

    async def emit_transaction(self, txn_data: dict[str, Any]) -> None:
        """Emit a new transaction event to the /transactions namespace."""
        await self.server.emit("new_transaction", txn_data, namespace="/transactions")
        logger.debug("ws_emit_transaction", txn_id=txn_data.get("id"))

    async def emit_transaction_flagged(self, txn_data: dict[str, Any]) -> None:
        """Emit a flagged transaction event to the /transactions namespace."""
        await self.server.emit("transaction_flagged", txn_data, namespace="/transactions")

    async def emit_dashboard_update(self, data: dict[str, Any]) -> None:
        """Emit dashboard metric updates to the /dashboard namespace."""
        await self.server.emit("metrics_update", data, namespace="/dashboard")

    async def emit_model_status(self, data: dict[str, Any]) -> None:
        """Emit model training/deployment status to the /dashboard namespace."""
        await self.server.emit("model_status", data, namespace="/dashboard")

    async def emit_to_user(
        self, user_id: str, event: str, data: dict[str, Any], namespace: str = "/alerts"
    ) -> None:
        """Send an event to a specific user's room across the given namespace."""
        room = f"user:{user_id}"
        await self.server.emit(event, data, room=room, namespace=namespace)
        logger.debug("ws_emit_to_user", user_id=user_id, event=event, namespace=namespace)


ws_manager = SocketIOManager()


def get_socketio_app() -> socketio.ASGIApp:
    """Return the ASGI app to mount on the FastAPI application."""
    return socketio.ASGIApp(ws_manager.server, socketio_path="/ws/socket.io")
