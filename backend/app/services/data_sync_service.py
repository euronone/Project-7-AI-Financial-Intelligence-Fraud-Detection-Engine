"""
FinShield AI — External Data Sync Service
==========================================

Connects to a tenant's external database (Supabase, PostgreSQL, MySQL, REST API),
applies their schema mapping (customer column name → FinShield canonical name),
and upserts the records into FinShield's internal Transaction/Customer tables.

Key responsibilities:
  1. Read tenant's db_config_json for connection credentials
  2. Read tenant's schema_mapping_json for column rename rules
  3. Connect to the external source (Supabase REST, asyncpg, aiomysql, or HTTP)
  4. Fetch rows from customer's table names, rename columns via mapping
  5. Upsert into FinShield's internal customers/transactions tables
  6. Write sync status back to tenant.db_config_json["last_sync"]

Auto-refresh config is stored in tenant.db_config_json["data_refresh"] as:
  {
    "mode": "manual" | "on_training_start" | "every_1h" | "every_6h" | "every_24h",
    "tables": ["transactions", "customers"],
    "row_limit": 100000
  }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import Tenant
from app.core.encryption import encryptor

logger = logging.getLogger(__name__)

# ── Canonical column names the ML pipeline depends on ────────────────────────

REQUIRED_TXN_COLUMNS = {
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "transaction_type",
    "channel",
    "transaction_timestamp",
}

# ── Helpers ───────────────────────────────────────────────────────────────────


def _apply_schema_mapping(
    rows: list[dict],
    mapping: dict,  # { finshield_field: { "client_column": str, "enabled": bool } }
    custom_fields: list[dict],  # [ { "field": str, "client_column": str, "enabled": bool } ]
) -> list[dict]:
    """
    Rename columns in each row dict from the client's column names to
    FinShield's canonical field names.

    Also appends any custom field columns that have a client_column mapping.

    Algorithm:
      For each FinShield field in mapping:
        - Find the value in the row using client_column name
        - Store it under the FinShield field name
      For each custom field:
        - Find value using its client_column, keep under its field name
    """
    # Build reverse map: client_column → finshield_field
    rename_map: dict[str, str] = {}
    for finshield_field, cfg in mapping.items():
        client_col = cfg.get("client_column") if isinstance(cfg, dict) else cfg
        if client_col and isinstance(client_col, str) and client_col.strip():
            rename_map[client_col.strip()] = finshield_field

    # Custom field renames
    for cf in custom_fields:
        client_col = cf.get("client_column", "")
        field = cf.get("field", "")
        if client_col and field:
            rename_map[client_col.strip()] = field

    if not rename_map and not rows:
        return rows

    out: list[dict] = []
    for row in rows:
        new_row: dict = {}
        for col, val in row.items():
            target = rename_map.get(col, col)  # keep original name if not in map
            new_row[target] = val
        out.append(new_row)
    return out


def _build_pg_dsn(config: dict) -> str | None:
    """Construct an asyncpg-compatible DSN from the db_config_json dict."""
    if config.get("db_url"):
        return config["db_url"]
    host = config.get("host")
    port = config.get("port", 5432)
    user = config.get("db_user")
    password = config.get("db_password", "")
    db_name = config.get("db_name", "postgres")
    if host and user:
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return None


# ── Connector functions (one per source type) ─────────────────────────────────


async def _fetch_supabase(
    config: dict,
    table_name: str,
    limit: int,
    cutoff_col: str | None = None,
    cutoff_dt: datetime | None = None,
) -> list[dict]:
    """
    Use Supabase PostgREST REST API to fetch rows from an external table.
    Requires: supabase_url + supabase_anon_key (or supabase_service_key).
    """
    import httpx

    base_url = config.get("supabase_url", "").rstrip("/")
    key = config.get("supabase_service_key") or config.get("supabase_anon_key", "")
    if not base_url or not key:
        raise ValueError("Supabase credentials missing: need supabase_url and anon/service key.")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Prefer": "return=representation",
    }
    params: dict = {"limit": str(limit), "order": "id.desc"}
    if cutoff_col and cutoff_dt:
        params[cutoff_col] = f"gte.{cutoff_dt.isoformat()}"

    url = f"{base_url}/rest/v1/{table_name}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params)

    if resp.status_code == 404:
        raise ValueError(f"Table '{table_name}' not found in external Supabase database.")
    if resp.status_code >= 400:
        raise ValueError(f"Supabase returned HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    return data if isinstance(data, list) else []


async def _fetch_postgresql(
    config: dict,
    table_name: str,
    limit: int,
    cutoff_col: str | None = None,
    cutoff_dt: datetime | None = None,
) -> list[dict]:
    """Fetch rows via asyncpg direct connection."""
    try:
        import asyncpg  # type: ignore
    except ImportError:
        raise ValueError("asyncpg not installed. Install it to use PostgreSQL external sync.")

    dsn = _build_pg_dsn(config)
    if not dsn:
        raise ValueError("PostgreSQL credentials incomplete: need host, db_user, and db_name.")

    dsn_clean = dsn.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgres://", "postgresql://"
    )
    conn = await asyncpg.connect(dsn_clean, timeout=10.0)
    try:
        query = f'SELECT * FROM "{table_name}" ORDER BY 1 DESC LIMIT {limit}'
        if cutoff_col and cutoff_dt:
            query = (
                f'SELECT * FROM "{table_name}" WHERE "{cutoff_col}" >= $1 '
                f"ORDER BY 1 DESC LIMIT {limit}"
            )
            rows = await conn.fetch(query, cutoff_dt)
        else:
            rows = await conn.fetch(query)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _fetch_rest_api(
    config: dict,
    table_name: str,
    limit: int,
) -> list[dict]:
    """Fetch rows via generic REST API using endpoint pattern."""
    import httpx

    base_url = (config.get("api_base_url") or config.get("db_url", "")).rstrip("/")
    api_key = config.get("api_key", "")
    auth_header = config.get("api_auth_header", "Authorization")
    if not base_url:
        raise ValueError("REST API base URL missing.")

    headers: dict = {}
    if api_key:
        headers[auth_header] = f"Bearer {api_key}"

    url = f"{base_url}/{table_name}"
    params = {"limit": limit}
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers=headers, params=params)
    if resp.status_code >= 400:
        raise ValueError(f"REST API returned HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if isinstance(data, list):
        return data
    # Many REST APIs wrap in { "data": [...] } or { "results": [...] }
    for key in ("data", "results", "records", "items", table_name):
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


async def _fetch_external_table(
    db_type: str,
    config: dict,
    table_name: str,
    limit: int = 100_000,
    cutoff_col: str | None = None,
    cutoff_dt: datetime | None = None,
) -> list[dict]:
    """Route to the correct connector based on db_type."""
    if db_type == "supabase":
        return await _fetch_supabase(config, table_name, limit, cutoff_col, cutoff_dt)
    elif db_type in ("postgresql", "cockroachdb", "neon"):
        return await _fetch_postgresql(config, table_name, limit, cutoff_col, cutoff_dt)
    elif db_type == "rest_api":
        return await _fetch_rest_api(config, table_name, limit)
    else:
        raise ValueError(
            f"Unsupported external DB type for sync: '{db_type}'. "
            "Supported: supabase, postgresql, cockroachdb, neon, rest_api."
        )


# ── Upsert helpers ────────────────────────────────────────────────────────────


async def _upsert_customers(db_session, tenant_id: str, rows: list[dict]) -> int:
    """
    Insert or update customer records in FinShield's internal customers table.
    Matches on email (unique). If no email mapping, uses external customer_id
    stored in banking_profile JSON.
    """
    from app.models.customer import Customer

    upserted = 0
    for row in rows:
        ext_id = str(row.get("customer_id") or row.get("id") or "")
        email = str(row.get("email") or f"{ext_id}@external.import").lower()

        # Try find by email first, then by banking_profile->external_id
        result = await db_session.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.email == email,
            )
        )
        customer = result.scalar_one_or_none()

        if customer is None:
            customer = Customer(tenant_id=tenant_id)
            db_session.add(customer)

        # Map fields — use .get() with sensible defaults
        customer.email = email
        customer.full_name = str(row.get("full_name") or row.get("name") or "Unknown")
        customer.phone_number = str(row.get("phone_number") or row.get("phone") or "")
        customer.city = str(row.get("city") or "")
        customer.account_type = str(row.get("account_type") or "personal")
        customer.account_status = str(row.get("account_status") or "active")
        customer.kyc_status = str(row.get("kyc_status") or "pending")
        customer.customer_tier = str(row.get("customer_tier") or "standard")
        # Safely parse numeric fields
        try:
            customer.risk_score = float(row.get("risk_score") or 0.1)
        except (TypeError, ValueError):
            customer.risk_score = 0.1
        try:
            customer.balance_amount = float(row.get("balance_amount") or 0)
        except (TypeError, ValueError):
            customer.balance_amount = 0.0

        # Store external ID for traceability
        bp = customer.banking_profile or {}
        bp["external_id"] = ext_id
        customer.banking_profile = bp

        upserted += 1

    await db_session.flush()
    return upserted


async def _upsert_transactions(db_session, tenant_id: str, rows: list[dict]) -> int:
    """
    Insert or update transaction records in FinShield's internal transactions table.
    Matches on the external transaction_id stored in the row (using merchant_id as proxy
    if no explicit transaction_id — deduplication by external_txn_id in JSON notes).
    """
    from app.models.transaction import Transaction

    upserted = 0
    for row in rows:
        ext_id = str(row.get("transaction_id") or row.get("id") or "")
        if not ext_id:
            continue

        # Normalise timestamp
        ts = row.get("transaction_timestamp") or row.get("timestamp") or row.get("created_at")
        if isinstance(ts, str):
            try:
                from dateutil import parser as dtparser

                ts = dtparser.parse(ts)
            except Exception:
                ts = datetime.now(timezone.utc)
        elif ts is None:
            ts = datetime.now(timezone.utc)

        # Parse amount
        try:
            amount = float(str(row.get("amount") or 0).replace(",", ""))
        except (TypeError, ValueError):
            amount = 0.0

        # Try find existing by external id stored in merchant_id field
        # (we reuse merchant_id as an external reference storage)
        result = await db_session.execute(
            select(Transaction).where(
                Transaction.tenant_id == tenant_id,
                Transaction.merchant_id == f"ext:{ext_id}",
            )
        )
        txn = result.scalar_one_or_none()

        if txn is None:
            txn = Transaction(tenant_id=tenant_id)
            db_session.add(txn)

        txn.merchant_id = f"ext:{ext_id}"  # store external reference
        txn.amount = amount
        txn.currency = str(row.get("currency") or "INR").upper()
        txn.transaction_type = str(row.get("transaction_type") or "purchase")
        txn.channel = str(row.get("channel") or "online")
        txn.merchant_name = str(row.get("merchant_name") or "")
        txn.merchant_category_code = str(row.get("merchant_category_code") or "")
        txn.transaction_timestamp = ts
        txn.status = str(row.get("status") or "completed")
        txn.device_type = str(row.get("device_type") or "unknown")
        txn.device_fingerprint = str(row.get("device_fingerprint") or "")
        txn.ip_address = str(row.get("ip_address") or "") or None
        txn.country_code = str(row.get("country_code") or "IN")
        txn.city = str(row.get("city") or "")
        txn.is_test = False

        # Numeric geo fields
        try:
            txn.location_lat = float(row.get("location_lat") or row.get("latitude") or 0) or None
        except (TypeError, ValueError):
            txn.location_lat = None
        try:
            txn.location_lng = float(row.get("location_lng") or row.get("longitude") or 0) or None
        except (TypeError, ValueError):
            txn.location_lng = None

        # Existing fraud fields (import as-is if already scored externally)
        if row.get("fraud_category"):
            txn.fraud_category = str(row["fraud_category"])
        if row.get("fraud_score") is not None:
            try:
                txn.fraud_score = float(row["fraud_score"])
            except (TypeError, ValueError):
                pass

        upserted += 1

    await db_session.flush()
    return upserted


# ── Public service API ────────────────────────────────────────────────────────


class DataSyncService:
    """
    Pulls data from a tenant's external database, applies schema mapping,
    and upserts into FinShield's internal tables.
    """

    @staticmethod
    async def get_refresh_config(tenant_id: str) -> dict:
        """Return the current data refresh configuration for a tenant."""
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if not tenant:
                return {
                    "mode": "manual",
                    "tables": ["transactions", "customers"],
                    "row_limit": 100_000,
                }
            config = tenant.db_config_json or {}
            return config.get(
                "data_refresh",
                {
                    "mode": "manual",
                    "tables": ["transactions", "customers"],
                    "row_limit": 100_000,
                },
            )

    @staticmethod
    async def save_refresh_config(tenant_id: str, refresh_config: dict) -> None:
        """Persist the data refresh schedule to tenant config."""
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if not tenant:
                raise ValueError("Tenant not found")
            cfg = tenant.db_config_json or {}
            cfg["data_refresh"] = refresh_config
            tenant.db_config_json = cfg
            await db.commit()

    @staticmethod
    async def get_sync_status(tenant_id: str) -> dict:
        """Return the last sync status from tenant config."""
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if not tenant:
                return {"synced": False, "message": "Tenant not found"}
            config = tenant.db_config_json or {}
            last_sync = config.get("last_sync", {})
            refresh = config.get("data_refresh", {"mode": "manual"})
            return {
                "last_sync": last_sync,
                "refresh_mode": refresh.get("mode", "manual"),
                "has_external_db": bool(tenant.db_type),
                "db_type": tenant.db_type,
            }

    @staticmethod
    async def preview_external_data(
        tenant_id: str,
        table: str = "transactions",
        limit: int = 10,
    ) -> dict:
        """
        Fetch a small sample from the external DB, apply schema mapping,
        and return both the raw rows and the renamed rows for the user to verify.
        """
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if not tenant:
                raise ValueError("Tenant not found")

            if not tenant.db_type:
                raise ValueError(
                    "No external database configured. "
                    "Go to Settings → Database to add your database credentials."
                )

            config = tenant.db_config_json or {}
            schema = tenant.schema_mapping_json or {}

            # Decrypt sensitive fields (credentials)
            try:
                config = encryptor.decrypt_config(config)
            except Exception as exc:
                logger.warning("Failed to decrypt config: %s (may be plaintext)", exc)
                # Continue with plaintext if decryption fails (old data)

        raw_rows = await _fetch_external_table(
            db_type=tenant.db_type,
            config=config,
            table_name=table,
            limit=limit,
        )

        # Determine mapping for this table
        table_key = "transactions" if table in ("transactions", "txns") else "customers"
        mapping = schema.get(table_key, {})
        custom_fields = schema.get(f"{table_key}_custom", [])

        renamed_rows = _apply_schema_mapping(raw_rows, mapping, custom_fields)

        # Detect unmapped columns (client columns that don't appear in mapping)
        mapped_client_cols = {
            cfg.get("client_column") if isinstance(cfg, dict) else cfg for cfg in mapping.values()
        }
        all_client_cols = set()
        for row in raw_rows[:3]:
            all_client_cols.update(row.keys())
        unmapped = sorted(all_client_cols - mapped_client_cols - {None, ""})

        return {
            "table": table,
            "raw_sample": raw_rows[:limit],
            "mapped_sample": renamed_rows[:limit],
            "unmapped_columns": unmapped,
            "total_fetched": len(raw_rows),
        }

    @staticmethod
    async def run_sync(
        tenant_id: str,
        tables: list[str] | None = None,
        row_limit: int = 100_000,
        incremental: bool = True,
    ) -> dict:
        """
        Full sync from external DB → FinShield internal DB.

        Steps:
          1. Load tenant config (db_type, credentials, schema mapping)
          2. Determine cutoff date for incremental sync
          3. Fetch rows from each requested table in the external DB
          4. Apply schema mapping (rename columns)
          5. Upsert into FinShield's internal customers/transactions tables
          6. Persist sync stats to tenant config
        """
        if tables is None:
            tables = ["transactions", "customers"]

        started_at = datetime.now(timezone.utc)
        stats: dict[str, Any] = {"started_at": started_at.isoformat(), "tables": {}}

        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if not tenant:
                raise ValueError("Tenant not found")
            if not tenant.db_type:
                raise ValueError(
                    "No external database configured. "
                    "Configure your database connection in Settings first."
                )

            db_type = tenant.db_type
            config = tenant.db_config_json or {}
            schema = tenant.schema_mapping_json or {}

            # Decrypt sensitive fields (credentials) before using
            try:
                config = encryptor.decrypt_config(config)
            except Exception as exc:
                logger.warning("Failed to decrypt config: %s (may be plaintext)", exc)
                # Continue with plaintext if decryption fails (old data)

            last_sync_info = config.get("last_sync", {})

        errors: list[str] = []

        for table in tables:
            table_key = "transactions" if table in ("transactions", "txns") else "customers"
            mapping = schema.get(table_key, {})
            custom_fields = schema.get(f"{table_key}_custom", [])

            # Determine cutoff for incremental sync
            cutoff_dt = None
            cutoff_col = None
            if incremental:
                last_ts = last_sync_info.get(f"{table_key}_synced_at")
                if last_ts:
                    try:
                        cutoff_dt = datetime.fromisoformat(last_ts) - timedelta(minutes=5)
                        # Find the client-side timestamp column name
                        ts_mapping = mapping.get("transaction_timestamp") or mapping.get(
                            "created_at", {}
                        )
                        cutoff_col = (
                            ts_mapping.get("client_column")
                            if isinstance(ts_mapping, dict)
                            else ts_mapping
                        ) or "created_at"
                    except Exception:
                        cutoff_dt = None

            try:
                raw_rows = await _fetch_external_table(
                    db_type=db_type,
                    config=config,
                    table_name=table,
                    limit=row_limit,
                    cutoff_col=cutoff_col,
                    cutoff_dt=cutoff_dt,
                )
                logger.info(
                    "[DataSync] tenant=%s table=%s fetched=%d cutoff=%s",
                    tenant_id,
                    table,
                    len(raw_rows),
                    cutoff_dt,
                )
            except Exception as exc:
                err = f"Fetch failed for '{table}': {exc}"
                logger.error("[DataSync] %s", err)
                errors.append(err)
                stats["tables"][table] = {"error": err, "fetched": 0, "upserted": 0}
                continue

            renamed_rows = _apply_schema_mapping(raw_rows, mapping, custom_fields)

            upserted = 0
            try:
                async with AsyncSessionLocal() as db:
                    if table_key == "customers":
                        upserted = await _upsert_customers(db, tenant_id, renamed_rows)
                    else:
                        upserted = await _upsert_transactions(db, tenant_id, renamed_rows)
                    await db.commit()
            except Exception as exc:
                err = f"Upsert failed for '{table}': {exc}"
                logger.error("[DataSync] %s", err)
                errors.append(err)
                stats["tables"][table] = {"error": err, "fetched": len(raw_rows), "upserted": 0}
                continue

            stats["tables"][table] = {
                "fetched": len(raw_rows),
                "upserted": upserted,
                "incremental": incremental,
                "cutoff_applied": cutoff_dt.isoformat() if cutoff_dt else None,
            }

        completed_at = datetime.now(timezone.utc)
        duration_s = round((completed_at - started_at).total_seconds(), 1)

        # Persist sync status
        last_sync_out: dict = {
            "synced_at": completed_at.isoformat(),
            "duration_seconds": duration_s,
            "errors": errors,
        }
        for table in tables:
            table_key = "transactions" if table in ("transactions", "txns") else "customers"
            if table_key not in [e for e in errors if table_key in e]:
                last_sync_out[f"{table_key}_synced_at"] = completed_at.isoformat()
            tbl_stats = stats["tables"].get(table, {})
            last_sync_out[f"{table_key}_count"] = tbl_stats.get("upserted", 0)

        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = res.scalar_one_or_none()
            if tenant:
                cfg = tenant.db_config_json or {}
                cfg["last_sync"] = last_sync_out
                tenant.db_config_json = cfg
                await db.commit()

        stats.update(
            {
                "completed_at": completed_at.isoformat(),
                "duration_seconds": duration_s,
                "errors": errors,
                "success": len(errors) == 0,
            }
        )
        return stats
