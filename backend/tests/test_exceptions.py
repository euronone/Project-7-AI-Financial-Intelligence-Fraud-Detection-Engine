"""Unit tests for custom application exception classes."""

from fastapi import status

from app.core.exceptions import (
    AppException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    ValidationException,
)


class TestAppException:
    def test_is_http_exception(self):
        from fastapi import HTTPException
        exc = AppException(status_code=400, detail="bad")
        assert isinstance(exc, HTTPException)

    def test_stores_status_and_detail(self):
        exc = AppException(status_code=418, detail="I'm a teapot")
        assert exc.status_code == 418
        assert exc.detail == "I'm a teapot"


class TestUnauthorizedException:
    def test_default_status_code(self):
        exc = UnauthorizedException()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_default_detail(self):
        exc = UnauthorizedException()
        assert exc.detail == "Not authenticated"

    def test_custom_detail(self):
        exc = UnauthorizedException("Token expired")
        assert exc.detail == "Token expired"


class TestForbiddenException:
    def test_default_status_code(self):
        exc = ForbiddenException()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_default_detail(self):
        exc = ForbiddenException()
        assert exc.detail == "Insufficient permissions"

    def test_custom_detail(self):
        exc = ForbiddenException("Admins only")
        assert exc.detail == "Admins only"


class TestNotFoundException:
    def test_default_status_code(self):
        exc = NotFoundException()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_default_detail_contains_resource(self):
        exc = NotFoundException()
        assert "not found" in exc.detail.lower()

    def test_custom_resource_name(self):
        exc = NotFoundException("Transaction")
        assert "Transaction" in exc.detail
        assert "not found" in exc.detail.lower()


class TestConflictException:
    def test_default_status_code(self):
        exc = ConflictException()
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_default_detail(self):
        exc = ConflictException()
        assert exc.detail == "Resource already exists"

    def test_custom_detail(self):
        exc = ConflictException("Email already registered")
        assert exc.detail == "Email already registered"


class TestValidationException:
    def test_default_status_code(self):
        exc = ValidationException()
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_default_detail(self):
        exc = ValidationException()
        assert exc.detail == "Validation error"

    def test_custom_detail(self):
        exc = ValidationException("Amount must be positive")
        assert exc.detail == "Amount must be positive"
