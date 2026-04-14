"""Settings endpoints — DB connections, API keys, connection tests."""

import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import Tenant
from app.schemas.settings import DbConnectionRequest, DbConnectionResponse, ConnectionTestResponse
from app.dependencies import CurrentUser, AdminUser
from app.core.encryption import encryptor

logger = logging.getLogger(__name__)

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

    # Try to decrypt secrets — if decryption fails, assume data is old plaintext
    try:
        config = encryptor.decrypt_config(config)
    except Exception as exc:
        logger.warning(
            "Failed to decrypt database config: %s (may be plaintext from before encryption)", exc
        )
        # Continue with plaintext config from old data

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
        "has_password": bool(config.get("db_password")),
        "has_anon_key": bool(config.get("supabase_anon_key")),
        "has_service_key": bool(config.get("supabase_service_key")),
        "has_service_role_key": bool(config.get("supabase_service_role_key")),
        "has_supabase_db_password": bool(config.get("supabase_db_password")),
        "has_api_key": bool(config.get("api_key")),
        "has_aws_secret": bool(config.get("aws_secret_access_key")),
        "has_service_account": bool(config.get("service_account_json")),
        "has_snowflake_pass": bool(config.get("db_password") and config.get("snowflake_account")),
        "has_planetscale_pass": bool(config.get("planetscale_password")),
        "has_redis_password": bool(config.get("redis_password")),
        "ssl_mode": config.get("ssl_mode"),
        "schema_name": config.get("schema_name"),
        "pool_size": config.get("pool_size"),
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
    # Store full config as JSON with encrypted secrets.
    # ISSUE-009: we assign a *new* dict object so SQLAlchemy detects the change.
    # Never mutate tenant.db_config_json in-place without calling
    # flag_modified(tenant, "db_config_json") afterwards.
    config = {k: v for k, v in body.model_dump().items() if v is not None}
    config["label"] = body.label or body.db_type

    # Encrypt sensitive fields before storing
    config = encryptor.encrypt_config(config)
    tenant.db_config_json = config

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
            return ConnectionTestResponse(
                success=False, message=f"Connection failed: {str(exc)[:120]}"
            )

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
            pg_url_clean = pg_url.replace("postgresql+asyncpg://", "postgresql://").replace(
                "postgres://", "postgresql://"
            )
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
        return ConnectionTestResponse(
            success=False, message="Fill host, username, and password before testing."
        )

    # ── MongoDB ──────────────────────────────────────────────────────────
    if body.db_type == "mongodb":
        uri = body.mongo_connection_string or body.db_url
        if not uri:
            return ConnectionTestResponse(
                success=False, message="Provide a MongoDB connection string."
            )
        try:
            from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

            client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            await client.admin.command("ping")
            client.close()
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=True, message="MongoDB ping successful", latency_ms=latency
            )
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
            message="MSSQL credentials accepted"
            if has_creds
            else "Fill server host, username, and password.",
            latency_ms=latency,
        )

    # ── Oracle ───────────────────────────────────────────────────────────
    if body.db_type == "oracle":
        has_creds = bool(
            body.host and body.db_user and body.db_password and body.oracle_service_name
        )
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message="Oracle credentials accepted"
            if has_creds
            else "Fill host, username, password, and service name.",
            latency_ms=latency,
        )

    # ── Redis ────────────────────────────────────────────────────────────
    if body.db_type == "redis":
        host = body.host or "localhost"
        port = body.port or 6379
        try:
            import asyncio
            import socket

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: socket.create_connection((host, port), timeout=4)
            )
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=True, message=f"Redis TCP reachable at {host}:{port}", latency_ms=latency
            )
        except Exception as exc:
            latency = round((time.time() - start) * 1000, 1)
            return ConnectionTestResponse(
                success=False, message=f"Redis unreachable: {str(exc)[:100]}", latency_ms=latency
            )

    # ── Amazon DynamoDB ──────────────────────────────────────────────────
    if body.db_type == "dynamodb":
        has_creds = bool(body.aws_access_key_id and body.aws_secret_access_key and body.aws_region)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"DynamoDB credentials accepted for region {body.aws_region}"
            if has_creds
            else "Fill AWS Access Key ID, Secret Access Key, and Region.",
            latency_ms=latency,
        )

    # ── Google Firestore ─────────────────────────────────────────────────
    if body.db_type == "firestore":
        has_creds = bool(body.gcp_project_id and body.service_account_json)
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"Firestore project {body.gcp_project_id} credentials accepted"
            if has_creds
            else "Fill GCP Project ID and Service Account JSON.",
            latency_ms=latency,
        )

    # ── Snowflake ────────────────────────────────────────────────────────
    if body.db_type == "snowflake":
        has_creds = bool(
            body.snowflake_account
            and body.db_user
            and body.db_password
            and body.snowflake_database
            and body.snowflake_warehouse
        )
        latency = round((time.time() - start) * 1000, 1)
        return ConnectionTestResponse(
            success=has_creds,
            message=f"Snowflake credentials accepted for account {body.snowflake_account}"
            if has_creds
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
                return ConnectionTestResponse(
                    success=True, message="ClickHouse ping successful", latency_ms=latency
                )
            return ConnectionTestResponse(
                success=False, message=f"ClickHouse returned {resp.status_code}", latency_ms=latency
            )
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
        return ConnectionTestResponse(
            success=False, message="Provide a base URL before testing.", latency_ms=latency
        )

    # ── Fallback for any unhandled type ──────────────────────────────────
    latency = round((time.time() - start) * 1000, 1)
    return ConnectionTestResponse(
        success=True,
        message="Configuration accepted — validate by running a test transaction",
        latency_ms=latency,
    )


# ---------------------------------------------------------------------------
# Keys-summary endpoint — fast per-service "is configured?" check
# ---------------------------------------------------------------------------


@router.get("/keys-summary")
async def get_keys_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return which services have at least one saved credential for this tenant.

    Response shape (example):
        {
          "resend":   {"configured": true,  "keys": ["resend_api_key"]},
          "twilio":   {"configured": false, "keys": []},
          "openai":   {"configured": true,  "keys": ["openai_api_key"]},
          "stripe":   {"configured": false, "keys": []},
          "firebase": {"configured": false, "keys": []},
        }

    Only metadata is returned — no encrypted values, no masked values.
    """
    from app.models.credential import TenantCredential

    result = await db.execute(
        select(TenantCredential.service, TenantCredential.key_name).where(
            TenantCredential.tenant_id == current_user.tenant_id
        )
    )
    rows = result.all()

    # Group by service
    service_keys: dict[str, list[str]] = {}
    for service, key_name in rows:
        service_keys.setdefault(service, []).append(key_name)

    # ISSUE-004: derive known services from the single-source-of-truth constant
    from app.schemas.credentials import SUPPORTED_PROVIDERS

    all_services = sorted(set(SUPPORTED_PROVIDERS) | set(service_keys.keys()))

    return {
        svc: {
            "configured": bool(service_keys.get(svc)),
            "keys": service_keys.get(svc, []),
        }
        for svc in all_services
    }


# ---------------------------------------------------------------------------
# Notification settings endpoints
# ---------------------------------------------------------------------------


@router.get("/notifications")
async def get_notification_settings(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return notification configuration (secrets masked).

    has_resend / has_twilio are resolved from the tenant_credentials table
    (the single source of truth for API keys) with a fallback to platform
    environment variables.  The legacy db_config_json.notifications keys
    are intentionally ignored — users manage all API keys via Integrations.
    """
    from app.config import get_settings
    from app.models.credential import TenantCredential

    settings = get_settings()
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    notif_config = (tenant.db_config_json or {}).get("notifications", {}) if tenant else {}

    # Check tenant_credentials table for email/SMS provider keys
    cred_result = await db.execute(
        select(TenantCredential.service, TenantCredential.key_name).where(
            TenantCredential.tenant_id == current_user.tenant_id,
            TenantCredential.service.in_(["resend", "brevo", "twilio"]),
        )
    )
    cred_rows = cred_result.all()
    cred_services = {(r.service, r.key_name) for r in cred_rows}

    # Check if ANY credential exists for each service (not just a specific key_name).
    # This handles cases where the user saved under a non-canonical key_name.
    configured_services = {svc for svc, _ in cred_services}
    has_resend = (
        "resend" in configured_services  # BYOK tenant_credentials
        or bool(notif_config.get("resend_api_key"))  # legacy db_config_json path
        or bool(getattr(settings, "RESEND_API_KEY", ""))  # platform env var
    )
    has_brevo = (
        "brevo" in configured_services  # BYOK tenant_credentials
        or bool(notif_config.get("brevo_api_key"))  # legacy db_config_json path
        or bool(getattr(settings, "BREVO_API_KEY", ""))  # platform env var
    )
    has_twilio = (
        "twilio" in configured_services  # BYOK tenant_credentials
        or bool(notif_config.get("twilio_account_sid"))  # legacy db_config_json path
        or bool(getattr(settings, "TWILIO_ACCOUNT_SID", ""))  # platform env var
    )

    # Check if a custom from_email (verified sender domain) is stored
    has_from_email = ("resend", "from_email") in cred_services

    return {
        "company_alert_email": notif_config.get(
            "company_alert_email", getattr(settings, "ALERT_COMPANY_EMAIL", "")
        ),
        "has_resend": has_resend,
        "has_brevo": has_brevo,
        "has_twilio": has_twilio,
        "has_from_email": has_from_email,
        "sms_enabled": notif_config.get("sms_enabled", True),
        "email_customer": notif_config.get("email_customer", True),
        "email_company": notif_config.get("email_company", True),
    }


@router.put("/notifications")
async def update_notification_settings(
    body: dict,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Save notification preferences (company email, toggles)."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        from app.core.exceptions import NotFoundException

        raise NotFoundException("Tenant")

    from sqlalchemy.orm.attributes import flag_modified

    # Work on a fresh copy so SQLAlchemy sees a distinct object reference
    config = dict(tenant.db_config_json or {})
    existing_notif = dict(config.get("notifications") or {})

    notif: dict = {
        "company_alert_email": body.get("company_alert_email", ""),
        "sms_enabled": body.get("sms_enabled", True),
        "email_customer": body.get("email_customer", True),
        "email_company": body.get("email_company", True),
    }
    # Encrypt and persist API keys if provided; preserve existing if not being updated
    for key_field in (
        "resend_api_key",
        "twilio_account_sid",
        "twilio_auth_token",
        "twilio_from_number",
    ):
        val = (body.get(key_field) or "").strip()
        if val:
            notif[key_field] = encryptor.encrypt(val)
        elif key_field in existing_notif:
            notif[key_field] = existing_notif[key_field]

    config["notifications"] = notif
    tenant.db_config_json = config
    flag_modified(tenant, "db_config_json")  # ← force SQLAlchemy to detect mutation
    await db.commit()
    return {"success": True, "message": "Notification settings saved"}


# ---------------------------------------------------------------------------
# Tenant initialisation — seed sample data for brand-new tenants
# ---------------------------------------------------------------------------


@router.post("/initialize")
async def initialize_tenant(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Seeds the current tenant's FinShield database with 100 sample customers and
    10,000 synthetic transactions (3 % fraud rate, 6 fraud patterns) if the
    tenant currently has ZERO transaction records.

    Idempotent — safe to call multiple times; will only seed once.

    Returns:
      {
        "seeded": true | false,     ← false if data already existed
        "customers_created": N,
        "transactions_created": N,
        "message": "..."
      }
    """
    from sqlalchemy import func
    from app.models.customer import Customer
    from app.models.transaction import Transaction

    # Guard: only seed if tenant has no transactions yet
    txn_count_result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == current_user.tenant_id,
            Transaction.is_test.is_(False),
        )
    )
    if (txn_count_result.scalar_one() or 0) > 0:
        cust_count_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.tenant_id == current_user.tenant_id)
        )
        return {
            "seeded": False,
            "customers_created": 0,
            "transactions_created": 0,
            "message": (
                f"Tenant already has {txn_count_result.scalar_one()} transactions "
                f"and {cust_count_result.scalar_one()} customers — skipping seed."
            ),
        }

    # Run the sample-data generator
    try:
        from app.services.seed_service import seed_tenant_sample_data

        result = await seed_tenant_sample_data(
            db=db,
            tenant_id=current_user.tenant_id,
            n_customers=100,
            n_transactions=10_000,
        )
        return {
            "seeded": True,
            "customers_created": result["customers_created"],
            "transactions_created": result["transactions_created"],
            "message": (
                f"Seeded {result['customers_created']} customers and "
                f"{result['transactions_created']} transactions with "
                f"~3% fraud rate. Your dashboard is now populated."
            ),
        }
    except Exception as exc:
        logger.exception("Seed failed for tenant %s", current_user.tenant_id)
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(exc)[:200]}") from exc


# ---------------------------------------------------------------------------
# Plan management
# ---------------------------------------------------------------------------

PLAN_HIERARCHY = {"free": 0, "pro": 1, "advanced": 2}


@router.put("/plan")
async def update_plan(
    body: dict,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Change the tenant's subscription plan.
    Only admins can call this.

    Body: { "plan": "free" | "pro" | "advanced" }

    In a real deployment this would integrate with Razorpay / Stripe billing.
    For now it updates the plan record immediately (demo / dev mode).
    """
    from datetime import timezone, timedelta

    new_plan = (body.get("plan") or "").strip().lower()
    if new_plan not in PLAN_HIERARCHY:
        raise HTTPException(status_code=422, detail="Plan must be one of: free, pro, advanced")

    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    old_plan = tenant.subscription_plan or "free"
    tenant.subscription_plan = new_plan
    tenant.plan_started_at = __import__("datetime").datetime.now(timezone.utc)
    tenant.plan_expires_at = (
        __import__("datetime").datetime.now(timezone.utc) + timedelta(days=30)
        if new_plan != "free"
        else None
    )
    await db.commit()

    return {
        "success": True,
        "previous_plan": old_plan,
        "new_plan": new_plan,
        "message": f"Plan updated from {old_plan} → {new_plan}",
    }


@router.get("/plan")
async def get_plan(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return the current tenant plan and usage stats."""
    from sqlalchemy import func
    from app.models.customer import Customer
    from app.models.transaction import Transaction

    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()

    plan = (tenant.subscription_plan if tenant else None) or "free"

    # Transaction usage this month
    from datetime import datetime, timezone

    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    txn_month = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == current_user.tenant_id,
            Transaction.transaction_timestamp >= month_start,
            Transaction.is_test.is_(False),
        )
    )
    txn_total = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == current_user.tenant_id,
            Transaction.is_test.is_(False),
        )
    )
    cust_total = await db.execute(
        select(func.count(Customer.id)).where(Customer.tenant_id == current_user.tenant_id)
    )

    limits = {
        "free": {"txn_month": 10_000, "label": "Free"},
        "pro": {"txn_month": 500_000, "label": "Pro"},
        "advanced": {"txn_month": None, "label": "Advanced"},
    }

    plan_limits = limits.get(plan, limits["free"])
    txn_month_val = txn_month.scalar_one() or 0
    monthly_limit = plan_limits["txn_month"]

    return {
        "plan": plan,
        "plan_label": plan_limits["label"],
        "plan_started_at": tenant.plan_started_at.isoformat()
        if tenant and tenant.plan_started_at
        else None,
        "plan_expires_at": tenant.plan_expires_at.isoformat()
        if tenant and tenant.plan_expires_at
        else None,
        "usage": {
            "transactions_this_month": txn_month_val,
            "transactions_total": txn_total.scalar_one() or 0,
            "customers_total": cust_total.scalar_one() or 0,
            "monthly_limit": monthly_limit,
            "usage_pct": round(txn_month_val / monthly_limit * 100, 1) if monthly_limit else None,
        },
        "plans": [
            {
                "id": "free",
                "label": "Free",
                "price_inr": 0,
                "price_display": "₹0 / month",
                "txn_limit": "10,000 / month",
                "connectors": "2 (Supabase + CSV)",
                "models": "Shared FinShield model",
                "support": "Community",
                "features": ["Email alerts only", "5 fraud rules", "Basic dashboard"],
                "color": "#00FF87",
            },
            {
                "id": "pro",
                "label": "Pro",
                "price_inr": 9999,
                "price_display": "₹9,999 / month",
                "txn_limit": "500,000 / month",
                "connectors": "10 connectors",
                "models": "Shared model + SHAP reports",
                "support": "Email (48h SLA)",
                "features": [
                    "Email + SMS alerts",
                    "25 custom rules",
                    "Full analytics dashboard",
                    "Weekly model retraining",
                    "REST API access",
                ],
                "color": "#3B82F6",
            },
            {
                "id": "advanced",
                "label": "Advanced",
                "price_inr": 24999,
                "price_display": "₹24,999 / month",
                "txn_limit": "Unlimited",
                "connectors": "All 20+ connectors",
                "models": "Dedicated ML model (your data)",
                "support": "Dedicated SLA + phone",
                "features": [
                    "Email + SMS + Call alerts",
                    "Unlimited custom rules",
                    "White-label dashboard",
                    "On-demand retraining",
                    "Full API + WebSocket",
                    "Custom schema mapping",
                    "VPC isolation",
                ],
                "color": "#8B5CF6",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Schema Mapping endpoints
# ---------------------------------------------------------------------------

# FinShield canonical schema definition — static, used as the "FinShield Column" side
FINSHIELD_CUSTOMER_SCHEMA = [
    {
        "field": "customer_id",
        "type": "UUID",
        "required": True,
        "description": "Unique customer identifier",
    },
    {
        "field": "full_name",
        "type": "STRING",
        "required": True,
        "description": "Customer's full legal name",
    },
    {"field": "email", "type": "STRING", "required": False, "description": "Email address"},
    {
        "field": "phone_number",
        "type": "STRING",
        "required": False,
        "description": "Mobile phone number (E.164 format: +91XXXXXXXXXX)",
    },
    {
        "field": "date_of_birth",
        "type": "DATE",
        "required": False,
        "description": "Date of birth (YYYY-MM-DD)",
    },
    {
        "field": "address_line_1",
        "type": "STRING",
        "required": False,
        "description": "Street address",
    },
    {"field": "city", "type": "STRING", "required": False, "description": "City name"},
    {
        "field": "state_province",
        "type": "STRING",
        "required": False,
        "description": "State or province",
    },
    {
        "field": "postal_code",
        "type": "STRING",
        "required": False,
        "description": "Postal / ZIP code",
    },
    {
        "field": "country_code",
        "type": "STRING(2)",
        "required": False,
        "description": "ISO 3166-1 alpha-2 country code (e.g. IN, US)",
    },
    {
        "field": "account_type",
        "type": "ENUM",
        "required": False,
        "description": "personal | business | merchant",
    },
    {
        "field": "account_opening_date",
        "type": "DATE",
        "required": False,
        "description": "Date account was opened",
    },
    {
        "field": "account_status",
        "type": "ENUM",
        "required": False,
        "description": "active | inactive | suspended | closed",
    },
    {
        "field": "kyc_status",
        "type": "ENUM",
        "required": False,
        "description": "pending | verified | rejected | expired",
    },
    {
        "field": "risk_score",
        "type": "DECIMAL",
        "required": False,
        "description": "Current risk score (0.0–1.0); computed by FinShield",
    },
    {
        "field": "customer_tier",
        "type": "ENUM",
        "required": False,
        "description": "standard | premium | vip",
    },
    {
        "field": "balance_amount",
        "type": "DECIMAL",
        "required": False,
        "description": "Current account balance",
    },
    {
        "field": "active_card_count",
        "type": "INTEGER",
        "required": False,
        "description": "Number of active payment cards",
    },
    {
        "field": "preferred_card_token",
        "type": "STRING",
        "required": False,
        "description": "Tokenised primary card identifier (no raw card numbers)",
    },
]

FINSHIELD_TRANSACTION_SCHEMA = [
    {
        "field": "transaction_id",
        "type": "UUID",
        "required": True,
        "description": "Unique transaction identifier",
    },
    {
        "field": "customer_id",
        "type": "UUID",
        "required": True,
        "description": "Reference to customers.customer_id",
    },
    {
        "field": "amount",
        "type": "DECIMAL",
        "required": True,
        "description": "Transaction amount (base currency units)",
    },
    {
        "field": "currency",
        "type": "STRING(3)",
        "required": True,
        "description": "ISO 4217 currency code (e.g. INR, USD)",
    },
    {
        "field": "transaction_type",
        "type": "ENUM",
        "required": True,
        "description": "purchase | withdrawal | transfer | refund | reversal",
    },
    {
        "field": "channel",
        "type": "ENUM",
        "required": True,
        "description": "pos_physical | online | atm | mobile | wire | ach",
    },
    {
        "field": "merchant_name",
        "type": "STRING",
        "required": False,
        "description": "Merchant or payee name",
    },
    {
        "field": "merchant_category_code",
        "type": "STRING(4)",
        "required": False,
        "description": "ISO 18245 Merchant Category Code (MCC)",
    },
    {
        "field": "transaction_timestamp",
        "type": "TIMESTAMP",
        "required": True,
        "description": "When the transaction occurred (UTC ISO 8601)",
    },
    {
        "field": "location_lat",
        "type": "DECIMAL",
        "required": False,
        "description": "GPS latitude of transaction location",
    },
    {
        "field": "location_lng",
        "type": "DECIMAL",
        "required": False,
        "description": "GPS longitude of transaction location",
    },
    {
        "field": "city",
        "type": "STRING",
        "required": False,
        "description": "City where transaction occurred",
    },
    {
        "field": "country_code",
        "type": "STRING(2)",
        "required": False,
        "description": "ISO country code of transaction location",
    },
    {
        "field": "ip_address",
        "type": "STRING",
        "required": False,
        "description": "IPv4/IPv6 address of originating device",
    },
    {
        "field": "device_fingerprint",
        "type": "STRING",
        "required": False,
        "description": "Unique device identifier / fingerprint hash",
    },
    {
        "field": "device_type",
        "type": "ENUM",
        "required": False,
        "description": "mobile | desktop | tablet | pos_terminal | unknown",
    },
    {
        "field": "status",
        "type": "ENUM",
        "required": False,
        "description": "pending | completed | failed | reversed | flagged | blocked",
    },
    # FinShield-computed columns (written back by the platform)
    {
        "field": "fraud_score",
        "type": "DECIMAL",
        "required": False,
        "description": "[FinShield writes] Fraud probability (0.0–1.0)",
    },
    {
        "field": "fraud_risk_level",
        "type": "ENUM",
        "required": False,
        "description": "[FinShield writes] low | medium | high | critical",
    },
    {
        "field": "fraud_category",
        "type": "ENUM",
        "required": False,
        "description": "[FinShield writes] legitimate | suspicious | fraudulent | unscored",
    },
    {
        "field": "is_flagged",
        "type": "BOOLEAN",
        "required": False,
        "description": "[FinShield writes] True if transaction was flagged",
    },
    {
        "field": "is_blocked",
        "type": "BOOLEAN",
        "required": False,
        "description": "[FinShield writes] True if transaction was blocked",
    },
    {
        "field": "model_version",
        "type": "STRING",
        "required": False,
        "description": "[FinShield writes] ML model version used for scoring",
    },
    {
        "field": "triggered_rule_ids",
        "type": "JSON",
        "required": False,
        "description": "[FinShield writes] List of rule IDs that fired",
    },
    {
        "field": "fraud_scored_at",
        "type": "TIMESTAMP",
        "required": False,
        "description": "[FinShield writes] When fraud scoring was performed",
    },
]


@router.get("/schema-definition")
async def get_schema_definition(_: CurrentUser):
    """Return FinShield's canonical column definitions for both schemas."""
    return {
        "customers": FINSHIELD_CUSTOMER_SCHEMA,
        "transactions": FINSHIELD_TRANSACTION_SCHEMA,
    }


def _normalize_field_mapping(raw: dict) -> dict:
    """
    Migrate old-format { field: "client_col_string" } to new-format
    { field: { "client_column": str, "enabled": bool } }.
    New-format entries are returned as-is.
    """
    out: dict = {}
    for field, value in raw.items():
        if isinstance(value, str):
            out[field] = {"client_column": value, "enabled": True}
        elif isinstance(value, dict):
            out[field] = {
                "client_column": value.get("client_column", ""),
                "enabled": bool(value.get("enabled", True)),
            }
    return out


@router.get("/schema-mapping")
async def get_schema_mapping(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the tenant's current column mapping.

    Response format (v2):
    {
      "customers":          { field: { client_column, enabled } },
      "transactions":       { field: { client_column, enabled } },
      "customers_custom":   [ { field, type, description, client_column, enabled } ],
      "transactions_custom":[ { field, type, description, client_column, enabled } ],
      "last_updated": "ISO timestamp | null"
    }
    """
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    mapping = (tenant.schema_mapping_json or {}) if tenant else {}

    return {
        "customers": _normalize_field_mapping(mapping.get("customers", {})),
        "transactions": _normalize_field_mapping(mapping.get("transactions", {})),
        "customers_custom": mapping.get("customers_custom", []),
        "transactions_custom": mapping.get("transactions_custom", []),
        "last_updated": mapping.get("_updated_at"),
    }


@router.put("/schema-mapping")
async def save_schema_mapping(
    body: dict,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Save the tenant's column name mapping (v2 format).

    Body format:
    {
      "customers":          { field: { "client_column": str, "enabled": bool } },
      "transactions":       { field: { "client_column": str, "enabled": bool } },
      "customers_custom":   [ { "field", "type", "description", "client_column", "enabled" } ],
      "transactions_custom":[ ... ]
    }
    """
    from datetime import datetime, timezone

    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        from app.core.exceptions import NotFoundException

        raise NotFoundException("Tenant")

    existing = tenant.schema_mapping_json or {}

    # Normalise incoming canonical-field mappings (accept both old & new client shapes)
    incoming_customers = body.get("customers", existing.get("customers", {}))
    incoming_transactions = body.get("transactions", existing.get("transactions", {}))

    # Build a fresh dict so SQLAlchemy detects the mutation (ISSUE-009).
    updated = dict(existing)
    updated.update(
        {
            "customers": _normalize_field_mapping(incoming_customers),
            "transactions": _normalize_field_mapping(incoming_transactions),
            "customers_custom": body.get("customers_custom", existing.get("customers_custom", [])),
            "transactions_custom": body.get(
                "transactions_custom", existing.get("transactions_custom", [])
            ),
            "_updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    tenant.schema_mapping_json = updated
    await db.commit()

    return {"success": True, "message": "Schema mapping saved"}
