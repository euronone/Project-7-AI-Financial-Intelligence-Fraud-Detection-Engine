"""
FinShield AI -- WebSocket Connection Manager
=============================================
Manages all live WebSocket connections, tenant-isolated broadcasts.

Usage in routes:
    from app.streaming.websocket_manager import ws_manager

    @app.websocket("/ws/{tenant_id}")
    async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
        conn_id = await ws_manager.connect(websocket, tenant_id)
        try:
            while True:
                await websocket.receive_text()  # keep alive
        except WebSocketDisconnect:
            ws_manager.disconnect(conn_id)
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class WsConnection:
    connection_id: str
    websocket: WebSocket
    tenant_id: str


class ConnectionManager:
    """Thread-safe (asyncio) manager for WebSocket connections."""

    def __init__(self):
        # connection_id -> WsConnection
        self._connections: dict[str, WsConnection] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str) -> str:
        """Accept a new connection and register it. Returns connection_id."""
        await websocket.accept()
        conn_id = str(uuid.uuid4())
        self._connections[conn_id] = WsConnection(
            connection_id=conn_id,
            websocket=websocket,
            tenant_id=tenant_id,
        )
        logger.info(
            "WS connected | conn=%s tenant=%s total=%d", conn_id, tenant_id, len(self._connections)
        )
        return conn_id

    def disconnect(self, connection_id: str):
        """Remove a connection."""
        self._connections.pop(connection_id, None)
        logger.info("WS disconnected | conn=%s remaining=%d", connection_id, len(self._connections))

    async def send_to_connection(self, connection_id: str, payload: dict):
        """Send a message to a specific connection."""
        conn = self._connections.get(connection_id)
        if conn:
            try:
                await conn.websocket.send_text(json.dumps(payload, default=str))
            except Exception as exc:
                logger.warning("WS send failed conn=%s: %s", connection_id, exc)
                self.disconnect(connection_id)

    async def broadcast_to_tenant(self, tenant_id: str, payload: dict):
        """Broadcast a message to all connections for a specific tenant."""
        message = json.dumps(payload, default=str)
        dead: list[str] = []

        for conn_id, conn in list(self._connections.items()):
            if conn.tenant_id == tenant_id:
                try:
                    await conn.websocket.send_text(message)
                except Exception:
                    dead.append(conn_id)

        for conn_id in dead:
            self.disconnect(conn_id)

    async def broadcast_all(self, payload: dict):
        """Broadcast to every connected client (admin use)."""
        message = json.dumps(payload, default=str)
        dead: list[str] = []

        for conn_id, conn in list(self._connections.items()):
            try:
                await conn.websocket.send_text(message)
            except Exception:
                dead.append(conn_id)

        for conn_id in dead:
            self.disconnect(conn_id)

    def connection_count(self, tenant_id: Optional[str] = None) -> int:
        if tenant_id:
            return sum(1 for c in self._connections.values() if c.tenant_id == tenant_id)
        return len(self._connections)


# Global singleton — import this wherever you need to broadcast
ws_manager = ConnectionManager()
