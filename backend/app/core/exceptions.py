"""Custom exception hierarchy and FastAPI exception handlers.

All application-level errors inherit from AppException so they carry
a consistent HTTP status code and error code for API consumers.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        self.message = message or self.__class__.message
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed."


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "A conflict occurred with the current state of the resource."


class UnauthorizedError(AppException):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication is required."


class ForbiddenError(AppException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class RateLimitError(AppException):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Too many requests. Please slow down."


class ServiceUnavailableError(AppException):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
    message = "A downstream service is currently unavailable."


class FraudPipelineTimeoutError(AppException):
    status_code = 504
    error_code = "FRAUD_PIPELINE_TIMEOUT"
    message = "Fraud detection pipeline did not complete within the latency budget."


class BatchSizeLimitError(AppException):
    status_code = 400
    error_code = "BATCH_SIZE_EXCEEDED"
    message = "Batch size exceeds the maximum allowed limit."


def _build_error_response(exc: AppException) -> dict:
    body: dict = {
        "error": exc.error_code,
        "message": exc.message,
    }
    if exc.detail:
        body["detail"] = exc.detail
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_response(exc),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "NOT_FOUND", "message": "Resource not found."},
        )

    @app.exception_handler(500)
    async def internal_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )
