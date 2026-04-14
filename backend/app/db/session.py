"""Async SQLAlchemy session factory."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Create async engine — works with PostgreSQL (asyncpg) and SQLite (aiosqlite)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    pool_pre_ping=True,
    # SQLite-specific: disable pool for file-based DBs
    **({} if not settings.is_sqlite else {"connect_args": {"check_same_thread": False}}),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """Create all tables (used in dev/test — production uses Alembic).

    Also applies additive column migrations for SQLite which doesn't support
    ALTER TABLE ADD COLUMN IF NOT EXISTS — we use try/except instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # ── Additive SQLite column migrations ────────────────────────────────
        # Run each ALTER TABLE in its own try/except so a duplicate column
        # error on subsequent startups is silently ignored.
        _new_columns = [
            "ALTER TABLE tenants ADD COLUMN schema_mapping_json TEXT",
            # training_jobs table columns (added progressively; create_all handles the table)
            "ALTER TABLE training_jobs ADD COLUMN parent_job_id TEXT",
            "ALTER TABLE training_jobs ADD COLUMN use_custom_columns INTEGER DEFAULT 1",
            "ALTER TABLE training_jobs ADD COLUMN feature_count INTEGER DEFAULT 0",
        ]
        for ddl in _new_columns:
            try:
                await conn.execute(text(ddl))
            except Exception:
                pass  # Column already exists — safe to ignore
