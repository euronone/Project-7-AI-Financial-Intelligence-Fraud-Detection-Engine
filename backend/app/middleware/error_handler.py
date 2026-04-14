"""
Enhanced error handling middleware — logs errors with unique error_id,
includes stack trace, exposes error_id to client for support team to trace.
"""

import uuid
import traceback
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standard error response format."""

    def __init__(self, error_id: str, message: str, status_code: int, detail: str | None = None):
        self.error_id = error_id
        self.message = message
        self.status_code = status_code
        self.detail = detail


async def error_handler_middleware(request: Request, exc: Exception):
    """Handle all exceptions with structured logging and error tracking."""

    # Generate unique error ID for support team
    error_id = str(uuid.uuid4())[:8]

    # Get request context
    method = request.method
    path = request.url.path
    query = str(request.url.query) if request.url.query else None

    # Log with full stack trace
    logger.error(
        "Request error",
        extra={
            "error_id": error_id,
            "method": method,
            "path": path,
            "query": query,
            "exception": str(exc),
            "exc_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
    )

    # Handle specific exception types
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error_id": error_id,
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )

    # Generic 500 error
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "detail": "Internal server error — reference error_id in support tickets",
            "message": "An unexpected error occurred. Please contact support with error_id above.",
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors with structured response."""
    error_id = str(uuid.uuid4())[:8]

    logger.warning(
        "Validation failed",
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "error_id": error_id,
            "detail": "Request validation failed",
            "errors": [
                {"field": str(e["loc"]), "message": e["msg"], "type": e["type"]}
                for e in exc.errors()
            ],
        },
    )
