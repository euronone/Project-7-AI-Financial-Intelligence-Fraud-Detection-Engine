from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


class AppError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource", resource_id: str = "") -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=detail, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestError(AppError):
    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_exception_handler(_request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_exception", message=exc.message, status_code=exc.status_code, details=exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )
