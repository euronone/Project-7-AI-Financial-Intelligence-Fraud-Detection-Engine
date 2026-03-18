"""FastAPI application entry point — FinShield AI backend."""
from contextlib import asynccontextmanager

import socketio
import structlog
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import configure_structlog, register_middleware
from app.streaming.websocket_manager import sio

logger = structlog.get_logger(__name__)
settings = get_settings()

# Configure structured logging at startup
configure_structlog()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown with the modern lifespan API."""
    # Startup
    logger.info("app_startup", env=settings.app_env, version="1.0.0")
    from app.streaming.producer import producer
    await producer.start()
    yield
    # Shutdown
    logger.info("app_shutdown")
    from app.streaming.producer import producer
    await producer.stop()


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    application = FastAPI(
        title="FinShield AI API",
        description="AI Financial Intelligence & Fraud Detection Engine",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Middleware (order matters — CORS is innermost, timing is outermost)
    register_middleware(application)

    # Exception handlers
    register_exception_handlers(application)

    # API routers
    application.include_router(api_router)

    return application


# Build the FastAPI app
_fastapi_app = create_app()

# Mount Socket.IO ASGI app — WebSocket connections are handled by Socket.IO,
# regular HTTP requests fall through to FastAPI.
app = socketio.ASGIApp(sio, other_asgi_app=_fastapi_app)
