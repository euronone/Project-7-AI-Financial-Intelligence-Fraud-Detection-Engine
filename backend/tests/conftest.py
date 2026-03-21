from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
def mock_rate_limit():
    with patch("app.core.rate_limiter.check_rate_limit") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_db_session():
    with patch("app.api.v1.auth.get_db") as mock:
        yield mock

@pytest.fixture(autouse=True)
def mock_audit_service():
    with patch("app.services.audit_service.log_action") as mock:
        mock.return_value = None
        yield mock

@pytest.fixture(autouse=True)
def mock_auth_service():
    with patch("app.services.auth_service.authenticate_user") as mock:
        from app.core.exceptions import UnauthorizedError
        mock.side_effect = UnauthorizedError("Invalid credentials")
        yield mock

@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
