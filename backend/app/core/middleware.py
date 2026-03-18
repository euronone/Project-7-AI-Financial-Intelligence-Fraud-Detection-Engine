"""Custom middleware: request timing, correlation ID injection, and structured logging.

Each request receives a unique correlation_id that is propagated through
structlog context so all log lines for a request are linkable.
"""
import time
import uuid

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injects a correlation ID header into every request and response.

    The ID is read from `X-Correlation-ID` if present (for upstream propagation),
    otherwise a new UUID4 is generated.
    """

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Bind to structlog context for this request's lifecycle
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = await call_next(request)
        response.headers[self.HEADER_NAME] = correlation_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status code, and duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
        return response


def configure_structlog() -> None:
    """Configure structlog for JSON output in production, pretty output in dev."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_development:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.log_level.upper(), 20)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def register_middleware(app: FastAPI) -> None:
    """Attach all middleware in the correct order (outermost last)."""
    # CORS — must be registered before custom middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Response-Time-Ms"],
    )
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
