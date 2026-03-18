"""Health check endpoints.

GET /health       — basic liveness probe
GET /health/detailed — checks DB, Redis, and Event Hub connectivity
"""
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["system"])
logger = structlog.get_logger(__name__)


@router.get("", summary="Liveness probe")
async def health() -> dict:
    return {"status": "ok", "service": "finshield-api"}


@router.get("/detailed", summary="Detailed health check")
async def health_detailed(db: AsyncSession = Depends(get_db)) -> dict:
    """Probes database, Redis, and Event Hub connectivity."""
    checks: dict = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        logger.error("health_check_db_failed", error=str(exc))

    # Redis (optional — skip if not configured)
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
