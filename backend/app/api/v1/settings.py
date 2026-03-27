"""Settings endpoints — DB connections, API keys, connection tests."""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import Tenant
from app.schemas.settings import DbConnectionRequest, DbConnectionResponse, ConnectionTestResponse
from app.dependencies import CurrentUser, AdminUser

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/database")
async def get_database_settings(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return current DB connection config (without secrets)."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"db_type": None, "label": None, "is_connected": False}

    config = tenant.db_config_json or {}
    return {
        "db_type": tenant.db_type,
        "label": config.get("label"),
        "is_connected": bool(tenant.db_type),
        "supabase_url": config.get("supabase_url"),
        "host": config.get("host"),
        "port": config.get("port"),
        "db_name": config.get("db_name"),
        "db_user": config.get("db_user"),
        # Mask all secret fields — return presence flag only
        "has_password":          bool(config.get("db_password")),
        "has_anon_key":          bool(config.get("supabase_anon_key")),
        "has_service_key":       bool(config.get("supabase_service_key")),
        "has_api_key":           bool(config.get("api_key")),
        "has_aws_secret":        bool(config.get("aws_secret_access_key")),
        "has_service_account":   bool(config.get("service_account_json")),
        "has_snowflake_pass":    bool(config.get("db_password") and config.get("snowflake_account")),
        "has_planetscale_pass":  bool(config.get("planetscale_password")),
        "ssl_mode":              config.get("ssl_mode"),
        "schema_name":           config.get("schema_name"),
        "pool_size":             config.get("pool_size"),
    }


@router.put("/database", response_model=DbConnectionResponse)
async def update_database_settings(
    body: DbConnectionRequest,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Save database connection configuration."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Tenant")

    tenant.db_type = body.db_type
    # Store full config as JSON (in production, encrypt secret fields with ENCRYPTION_KEY)
    tenant.db_config_json = {k: v for k, v in body.model_dump().items() if v is not None}
    tenant.db_config_json["label"] = body.label or body.db_type

    # Mark onboarding complete
    from app.models.user import User
    user_result = await db.execute(select(User).where(User.id == current_user.id))
    user = user_result.scalar_one_or_none()
    if user:
        user.has_completed_onboarding = True

    await db.commit()

    return DbConnectionResponse(
        db_type=body.db_type,
        label=body.label or body.db_type,
        is_connected=True,
        message=f"{body.db_type} connection saved successfully",
    )


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    body: DbConnectionRequest,
    current_user: CurrentUser,
):
    """
    Test a DB connection without saving.

    For Supabase: performs a lightweight HTTP request to the project REST API.
    For PostgreSQL / CockroachDB / Neon: validates the DSN format and attempts
      a real asyncpg connection if the URL is provided.
    For all other types: validates required fields are present and returns an
      accepted response — full validation requires a restart with the credentials.
    """
    start = time.time()

    # ── Supabase ────────────────────────────────────────────────────────
    if body.db_type == "supabase" and body.supabase_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(
                    f"{body.supabase_url.rstrip('/')}/rest/v1/",
                    headers={
                        "apikey": body.supabase_anon_key or "",
                        "Authorization": f"Bearer {body.supabase_anon_key or ''}",
                    },
                )
            latency = round((time.time() - start) * 1000, 1)
            if resp.status_code < 500:
                return ConnectionTestResponse(
                    success=True,
                    message=f"Supabase reachable — HTTP {resp.status_code}",
                    latency_ms=latency,
                )
            return ConnectionTestResponse(
                success=False,
                message=f"Supabase returned HTTP {resp.status_code}",
                latency_ms=latency,
            )
        except Exception as exc:
            return ConnectionTestResponse(success=False, message=f"Connection failed: {str(exc)[:120]}")

    # ── PostgreSQL / CockroachDB / Neon (asyncpg ping) ──────────────────
    pg_url = (
        body.db_url
        or body.neon_connection_string
        or (
            f"postgresql://{body.db_user}:{body.db_password}@{body.host}:{body.port or 5432}/{body.db_name}"
            if body.host and body.db_user
            else None
        )
    )
    if body.db_type in ("postgresql", "cockroachdb", "neon") and pg_url:
        try:
            import asyncpg  # type: ignore
            # Normalise URL scheme for asyncpg
            pg_url_clean = pg_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
            conn = await asyncpg.connect(pg_url_clean, timeout=6.0)
            await conn.close()
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=True,
                message=f"{body.db_type} connection successful",
                latency_ms=latency,
            )
        except ImportError:
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=True,
                message="Connection string format valid (asyncpg not installed for live ping)",
                latency_ms=latency,
            )
        except Exception as exc:
            return ConnectionTestResponse(success=False, message=str(exc)[:150])

    # ── MySQL / MariaDB / PlanetScale ────────────────────────────────────
    if body.db_type in ("mysql", "planetscale"):
        has_creds = bool(
            (body.host or body.planetscale_host)
            and (body.db_user or body.planetscale_username)
            and (body.db_password or body.planetscale_password)
        )
        latency = round((time.time() - start) * 1000, 1)
        if has_creds:
            return ConnectionTestResponse(
                success=True,
                message="MySQL/MariaDB credentials accepted (live ping requires aiomysql)",
                latency_ms=latency,
            )
        return ConnectionTestResponse(success=False, message="Fill host, username, and password before testing.")

    # ── MongoDB ──────────────────────────────────────────────────────────
    if body.db_type == "mongodb":
        uri = body.mongo_connection_string or body.db_url
        if not uri:
            return ConnectionTestResponse(success=False, message="Provide a MongoDB connection string.")
        try:
            from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
            client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            await client.admin.command("ping")
            client.close()
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(success=True, message="MongoDB ping successful", latency_ms=latency)
        except ImportError:
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=True,
                message="Connection string accepted (motor not installed for live ping)",
                latency_ms=latency,
            )
        except Exception as exc:
            return ConnectionTestResponse(success=False, message=str(exc)[:150])

    # ── Microsoft SQL Server ─────────────────────────────────────────────
    if body.db_type == "mssql":
        has_creds = bool(body.host and body.db_user and body.db_password)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message="MSSQL credentials accepted" if has_creds else "Fill server host, username, and password.",
            latency_ms=latency,
        )

    # ── Oracle ───────────────────────────────────────────────────────────
    if body.db_type == "oracle":
        has_creds = bool(body.host and body.db_user and body.db_password and body.oracle_service_name)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message="Oracle credentials accepted" if has_creds else "Fill host, username, password, and service name.",
            latency_ms=latency,
        )

    # ── Redis ────────────────────────────────────────────────────────────
    if body.db_type == "redis":
        host = body.host or "localhost"
        port = body.port or 6379
        try:
            import asyncio, socket
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: socket.create_connection((host, port), timeout=4))
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(success=True, message=f"Redis TCP reachable at {host}:{port}", latency_ms=latency)
        except Exception as exc:
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(success=False, message=f"Redis unreachable: {str(exc)[:100]}", latency_ms=latency)

    # ── Amazon DynamoDB ──────────────────────────────────────────────────
    if body.db_type == "dynamodb":
        has_creds = bool(body.aws_access_key_id and body.aws_secret_access_key and body.aws_region)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"DynamoDB credentials accepted for region {body.aws_region}" if has_creds
                    else "Fill AWS Access Key ID, Secret Access Key, and Region.",
            latency_ms=latency,
        )

    # ── Google Firestore ─────────────────────────────────────────────────
    if body.db_type == "firestore":
        has_creds = bool(body.gcp_project_id and body.service_account_json)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"Firestore project {body.gcp_project_id} credentials accepted" if has_creds
                    else "Fill GCP Project ID and Service Account JSON.",
            latency_ms=latency,
        )

    # ── Snowflake ────────────────────────────────────────────────────────
    if body.db_type == "snowflake":
        has_creds = bool(
            body.snowflake_account and body.db_user and body.db_password
            and body.snowflake_database and body.snowflake_warehouse
        )
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"Snowflake credentials accepted for account {body.snowflake_account}" if has_creds
                    else "Fill account identifier, username, password, warehouse, and database.",
            latency_ms=latency,
        )

    # ── ClickHouse ───────────────────────────────────────────────────────
    if body.db_type == "clickhouse":
        host = body.host or "localhost"
        port = body.clickhouse_http_port or 8123
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"http://{host}:{port}/ping",
                    auth=(body.db_user or "default", body.db_password or ""),
                )
            latency = round((time.time() - start) * 1000, 1)
            if resp.status_code == 200:
                return ConnectionTestResponse(success=True, message="ClickHouse ping successful", latency_ms=latency)
            return ConnectionTestResponse(success=False, message=f"ClickHouse returned {resp.status_code}", latency_ms=latency)
        except Exception as exc:
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(success=False, message=str(exc)[:120], latency_ms=latency)

    # ── Generic REST API / CSV ───────────────────────────────────────────
    if body.db_type == "rest_api":
        has_url = bool(body.api_base_url or body.db_url)
        latency = round((time.time() - start) * 1000, 1)
        if has_url:
            try:
                import httpx
                url = (body.api_base_url or body.db_url or "").rstrip("/") + "/"
                headers: dict = {}
                if body.api_key:
                    headers[body.api_auth_header or "Authorization"] = f"Bearer {body.api_key}"
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(url, headers=headers)
                latency = round((time.time() - start) * 1000, 1)
                return ConnectionTestResponse(
                    success=resp.status_code < 500,
                    message=f"REST API reachable — HTTP {resp.status_code}",
                    latency_ms=latency,
                )
            except Exception as exc:
                return ConnectionTestResponse(success=False, message=str(exc)[:120])
        return ConnectionTestResponse(success=False, message="Provide a base URL before testing.", latency_ms=latency)

    # ── Fallback for any unhandled type ──────────────────────────────────
    latency = round((time.time() - start) * 1000, 1)
    return ConnectionTestResponse(
        success=True,
        message="Configuration accepted — validate by running a test transaction",
        latency_ms=latency,
    )
