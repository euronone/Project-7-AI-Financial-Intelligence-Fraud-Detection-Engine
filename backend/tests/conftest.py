"""
Shared pytest fixtures for FinShield backend tests.

Environment variables are set BEFORE any app imports so that:
  - get_settings() lru_cache picks up test values on first call
  - APIKeyEncryptor gets a valid Fernet key at import time
  - SQLite is used — no external DB or Redis required
"""

import base64
import os

# ── Set test env vars before ANY app module is imported ──────────────────────
# Fernet requires URL-safe base64 of exactly 32 bytes.
_FERNET_KEY = base64.urlsafe_b64encode(b"test-key-for-pytest-only-32bytes").decode()
os.environ.setdefault("ENCRYPTION_KEY", _FERNET_KEY)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./finshield_test.db")
os.environ.setdefault("APP_ENV", "development")  # triggers create_all_tables on startup
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-finshield-pytest-ci")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

# ── App imports (after env vars are in place) ─────────────────────────────────
import pytest  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402

from app.config import get_settings  # noqa: E402

# Clear cached settings so tests always use the env vars above.
get_settings.cache_clear()


@pytest.fixture
async def client():
    """
    HTTP test client backed by an in-process SQLite database.

    The FastAPI lifespan runs on context-manager entry, which calls
    create_all_tables() (because APP_ENV=development).  All ORM models
    are registered with Base when create_app() imports the routers.
    No external services are needed.
    """
    from app.main import create_app

    application = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as ac:
        yield ac
