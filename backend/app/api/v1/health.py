"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("")
async def health():
    """Basic liveness check."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    """Detailed health check with DB connectivity."""
    checks = {"api": "ok", "database": "unknown", "env": settings.APP_ENV}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"

    overall = (
        "ok" if all(v == "ok" for v in checks.values() if v != settings.APP_ENV) else "degraded"
    )
    return {"status": overall, "checks": checks}
