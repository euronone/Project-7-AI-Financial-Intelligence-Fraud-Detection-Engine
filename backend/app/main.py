"""FinShield AI — FastAPI application entry point."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.router import api_router
from app.db.session import create_all_tables
from app.streaming.websocket_manager import ws_manager
from app.middleware.timeout import timeout_middleware
from app.middleware.error_handler import validation_exception_handler

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown events."""
    logger.info("FinShield AI starting", env=settings.APP_ENV, version=settings.APP_VERSION)

    # Auto-create tables in development (production uses Alembic migrations)
    if settings.is_development:
        await create_all_tables()
        logger.info("Database tables ensured")

    yield  # App runs here

    logger.info("FinShield AI shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ML-powered fraud detection API for financial institutions",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timeout (30s default, 10 min for ML training) ────────────────
    app.middleware("http")(timeout_middleware)

    # ── Validation error handler (structured JSON with error_id) ─────────────
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── WebSocket — live transaction feed ────────────────────────────────────
    @app.websocket("/ws/{tenant_id}")
    async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
        """
        Real-time feed for a specific tenant.
        Connect with:  ws://host/ws/{tenant_id}
        Events pushed: transaction_scored, fraud_alert_created
        """
        conn_id = await ws_manager.connect(websocket, tenant_id)
        try:
            # Send a welcome ping so client knows it's connected
            await ws_manager.send_to_connection(
                conn_id,
                {
                    "event": "connected",
                    "data": {"tenant_id": tenant_id, "connection_id": conn_id},
                },
            )
            while True:
                # Keep connection alive; client can send pings
                data = await websocket.receive_text()
                if data == "ping":
                    await ws_manager.send_to_connection(conn_id, {"event": "pong"})
        except WebSocketDisconnect:
            ws_manager.disconnect(conn_id)

    # ── Root ─────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    # ── Global exception handler ─────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
