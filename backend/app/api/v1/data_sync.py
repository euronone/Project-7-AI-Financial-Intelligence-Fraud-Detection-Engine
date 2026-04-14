"""
Data Sync API — External database synchronization endpoints.

Routes (all under /api/v1/data-sync/):
  POST /trigger             — manually start a full or incremental sync
  GET  /status              — last sync stats + refresh schedule
  POST /preview             — sample rows from external DB with mapping applied
  GET  /schedule            — get current auto-refresh schedule
  PUT  /schedule            — update auto-refresh schedule

The sync pulls data from the tenant's external DB (configured in Settings →
Database), applies their schema mapping (Settings → Schema Mapping), and
upserts into FinShield's internal tables so ML training has fresh data.
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser, AdminUser
from app.services.data_sync_service import DataSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-sync", tags=["Data Sync"])


# ── Request / Response schemas ─────────────────────────────────────────────────


class TriggerSyncRequest(BaseModel):
    tables: list[Literal["transactions", "customers"]] = Field(
        default=["transactions", "customers"],
        description="Which tables to sync from the external database.",
    )
    incremental: bool = Field(
        default=True,
        description=(
            "True = only fetch rows newer than the last sync (faster). "
            "False = full re-sync from the external DB (slower, use for first run)."
        ),
    )
    row_limit: int = Field(
        default=100_000,
        ge=1,
        le=500_000,
        description="Maximum rows to fetch per table per sync run.",
    )


class PreviewRequest(BaseModel):
    table: Literal["transactions", "customers"] = Field(
        default="transactions",
        description="Which table to preview from the external database.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of sample rows to return.",
    )


class RefreshScheduleRequest(BaseModel):
    mode: Literal["manual", "on_training_start", "every_1h", "every_6h", "every_24h"] = Field(
        description=(
            "Auto-refresh mode:\n"
            "  manual            — sync only when POST /trigger is called\n"
            "  on_training_start — auto-sync immediately before each training job\n"
            "  every_1h          — sync every 1 hour (requires background worker)\n"
            "  every_6h          — sync every 6 hours\n"
            "  every_24h         — sync every 24 hours"
        )
    )
    tables: list[Literal["transactions", "customers"]] = Field(
        default=["transactions", "customers"],
        description="Tables to include in the scheduled sync.",
    )
    row_limit: int = Field(
        default=100_000,
        ge=1,
        le=500_000,
        description="Maximum rows to pull per table per auto-refresh run.",
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post("/trigger", status_code=202)
async def trigger_sync(
    body: TriggerSyncRequest,
    current_user: CurrentUser,
):
    """
    Manually trigger a data sync from the tenant's external database.

    - Connects to the configured external DB (Supabase / PostgreSQL / REST API)
    - Applies the tenant's column-name mapping from Settings → Schema Mapping
    - Upserts fetched records into FinShield's internal customers / transactions tables
    - Stores sync result (counts, duration, errors) in tenant config

    Returns 202 and runs synchronously (waits for completion).
    For large datasets (>50K rows) consider calling this before sleeping / polling status.
    """
    try:
        stats = await DataSyncService.run_sync(
            tenant_id=current_user.tenant_id,
            tables=body.tables,
            row_limit=body.row_limit,
            incremental=body.incremental,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Data sync failed for tenant %s", current_user.tenant_id)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(exc)[:200]}") from exc

    return {
        "message": "Sync completed" if stats.get("success") else "Sync completed with errors",
        "success": stats.get("success", False),
        "tables": stats.get("tables", {}),
        "duration_seconds": stats.get("duration_seconds"),
        "errors": stats.get("errors", []),
    }


@router.get("/status")
async def get_sync_status(current_user: CurrentUser):
    """
    Return the last sync result and auto-refresh schedule.

    Response:
    {
      "last_sync": {
        "synced_at": "ISO timestamp",
        "duration_seconds": 4.2,
        "transactions_count": 8423,
        "customers_count": 312,
        "errors": []
      },
      "refresh_mode": "on_training_start",
      "has_external_db": true,
      "db_type": "supabase"
    }
    """
    return await DataSyncService.get_sync_status(current_user.tenant_id)


@router.post("/preview")
async def preview_external_data(
    body: PreviewRequest,
    current_user: CurrentUser,
):
    """
    Fetch a small sample from the external DB and show raw vs mapped columns side-by-side.

    Use this to verify your schema mapping is correct before running a full sync.

    Response includes:
      - raw_sample:     rows as they appear in the external DB (with client column names)
      - mapped_sample:  same rows after applying your schema mapping (FinShield column names)
      - unmapped_columns: client columns not covered by any mapping entry (potential gaps)
    """
    try:
        result = await DataSyncService.preview_external_data(
            tenant_id=current_user.tenant_id,
            table=body.table,
            limit=body.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Preview failed for tenant %s", current_user.tenant_id)
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(exc)[:200]}") from exc

    return result


@router.get("/schedule")
async def get_refresh_schedule(current_user: CurrentUser):
    """Return the current auto-refresh schedule configuration."""
    config = await DataSyncService.get_refresh_config(current_user.tenant_id)
    return {
        "mode": config.get("mode", "manual"),
        "tables": config.get("tables", ["transactions", "customers"]),
        "row_limit": config.get("row_limit", 100_000),
        "description": {
            "manual": "Sync only runs when you call POST /data-sync/trigger",
            "on_training_start": "Sync runs automatically before each ML training job",
            "every_1h": "Sync runs every hour (requires background scheduler)",
            "every_6h": "Sync runs every 6 hours",
            "every_24h": "Sync runs every 24 hours",
        }.get(config.get("mode", "manual"), ""),
    }


@router.put("/schedule")
async def update_refresh_schedule(
    body: RefreshScheduleRequest,
    current_user: AdminUser,
):
    """
    Update the auto-refresh schedule.

    Only admins can change the refresh schedule.
    The schedule is applied on the next training job or background tick.

    Modes:
      manual            — no automatic sync (default)
      on_training_start — sync immediately before each ML training job starts
      every_1h/6h/24h   — periodic sync (background worker must be running)
    """
    refresh_config = {
        "mode": body.mode,
        "tables": body.tables,
        "row_limit": body.row_limit,
    }
    try:
        await DataSyncService.save_refresh_config(current_user.tenant_id, refresh_config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": f"Auto-refresh schedule set to '{body.mode}'.",
        "config": refresh_config,
    }
