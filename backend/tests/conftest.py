"""pytest fixtures — test DB, async client, and shared test data."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Patch PostgreSQL-specific types → SQLite-compatible equivalents BEFORE any
# model module is imported, so SQLite can create the schema in-memory.
# ---------------------------------------------------------------------------
from sqlalchemy.dialects import postgresql as _pg

_pg.JSONB = JSON          # JSONB → JSON
_pg.INET = String(45)     # INET → VARCHAR(45)  (fits IPv4 + IPv6)

from app.db.session import get_db  # noqa: E402
from app.models.base import Base   # noqa: E402
from app.models import entity       # noqa: F401,E402 — ensure models are registered
from app.models import transaction  # noqa: F401,E402

# Use an in-memory SQLite database for unit/integration tests.
# NOTE: Some PostgreSQL-specific features (INET, JSONB, partitioning) are not
# supported by SQLite. Tests that require full PG behaviour should use a
# real test database via TEST_DATABASE_URL env variable.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncSession:
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncClient:
    """HTTP test client with DB session overridden."""
    from app.main import _fastapi_app

    _fastapi_app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(
        transport=ASGITransport(app=_fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    _fastapi_app.dependency_overrides.clear()
