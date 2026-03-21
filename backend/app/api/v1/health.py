from typing import Any

import structlog
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check — confirms the API is running."""
    return {"status": "ok"}


@router.get("/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check — reports status of DB, Redis, and Event Hub."""
    settings = get_settings()
    checks: dict[str, Any] = {
        "api": {"status": "ok"},
        "environment": settings.app_env,
    }

    # Database check
    try:
        from app.db.session import async_engine

        from sqlalchemy import text

        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        logger.warning("health_db_fail", error=str(exc))
        checks["database"] = {"status": "degraded", "error": str(exc)}

    # Redis check
    try:
        from redis.asyncio import from_url as redis_from_url

        r = redis_from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        logger.warning("health_redis_fail", error=str(exc))
        checks["redis"] = {"status": "degraded", "error": str(exc)}

    has_degraded = any(
        v.get("status") == "degraded" for v in checks.values() if isinstance(v, dict)
    )
    checks["status"] = "degraded" if has_degraded else "ok"

    return checks
