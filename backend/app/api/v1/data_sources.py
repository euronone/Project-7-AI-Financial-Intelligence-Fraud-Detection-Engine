"""
Data Sources endpoints.

Provides:
  GET /api/v1/data-sources              – connected sources, status, record counts
  GET /api/v1/data-sources/schema       – table schema with column name, type, sample values
  GET /api/v1/data-sources/field-map    – transaction table key fields with descriptions
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert
from app.models.rule import FraudRule

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


# ---------------------------------------------------------------------------
# 1. Overview: connected sources + record counts
# ---------------------------------------------------------------------------


@router.get("")
async def get_data_sources(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the list of connected data sources with:
    - type (SQLite / PostgreSQL / Supabase)
    - status (live / unreachable)
    - table names + record counts
    - last updated timestamp (most recent row in transactions)
    """
    from app.config import get_settings

    settings = get_settings()

    # Detect DB type from connection URL
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        db_type = "SQLite"
        db_label = "SQLite (local dev)"
        connector_icon = "database"
    elif "supabase" in db_url or (settings.SUPABASE_URL and "supabase" in settings.SUPABASE_URL):
        db_type = "Supabase (PostgreSQL)"
        db_label = "Supabase Cloud"
        connector_icon = "cloud"
    else:
        db_type = "PostgreSQL"
        db_label = "PostgreSQL"
        connector_icon = "database"

    # Test DB connectivity
    db_status = "unreachable"
    db_latency_ms = None
    try:
        import time

        t0 = time.time()
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - t0) * 1000, 1)
        db_status = "live"
    except Exception:
        pass

    tid = current_user.tenant_id

    # Record counts per table (scoped to tenant where possible)
    cust_res = await db.execute(select(func.count(Customer.id)).where(Customer.tenant_id == tid))
    txn_res = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.tenant_id == tid,
            Transaction.is_test == False,  # noqa: E712
        )
    )
    alert_res = await db.execute(
        select(func.count(FraudAlert.id)).where(FraudAlert.tenant_id == tid)
    )
    rule_res = await db.execute(select(func.count(FraudRule.id)))

    customer_count = cust_res.scalar_one() or 0
    txn_count = txn_res.scalar_one() or 0
    alert_count = alert_res.scalar_one() or 0
    rule_count = rule_res.scalar_one() or 0

    # Last updated: most recent transaction timestamp
    last_txn_res = await db.execute(
        select(func.max(Transaction.transaction_timestamp)).where(Transaction.tenant_id == tid)
    )
    last_updated = last_txn_res.scalar_one()
    last_updated_str = last_updated.isoformat() if last_updated else None

    tables = [
        {
            "table_name": "customers",
            "description": "Customer profiles — identity, KYC, risk scores",
            "record_count": customer_count,
            "primary_key": "id (UUID)",
            "tenant_scoped": True,
            "last_updated": last_updated_str,
        },
        {
            "table_name": "transactions",
            "description": "Financial transactions with FinShield fraud columns",
            "record_count": txn_count,
            "primary_key": "id (UUID)",
            "tenant_scoped": True,
            "last_updated": last_updated_str,
        },
        {
            "table_name": "fraud_alerts",
            "description": "Fraud detection alerts with severity and resolution status",
            "record_count": alert_count,
            "primary_key": "id (UUID)",
            "tenant_scoped": True,
            "last_updated": None,
        },
        {
            "table_name": "fraud_rules",
            "description": "Active fraud detection rules (built-in + custom)",
            "record_count": rule_count,
            "primary_key": "id (UUID)",
            "tenant_scoped": False,
            "last_updated": None,
        },
    ]

    total_records = customer_count + txn_count + alert_count + rule_count

    # Supabase secondary source (if configured)
    sources = [
        {
            "source_id": "primary_db",
            "name": db_label,
            "type": "Database",
            "connector_type": db_type,
            "connector_icon": connector_icon,
            "status": db_status,
            "latency_ms": db_latency_ms,
            "tables": tables,
            "total_records": total_records,
            "last_synced": last_updated_str or datetime.now(timezone.utc).isoformat(),
            "active_users": customer_count,
        },
    ]

    if settings.SUPABASE_URL and "sqlite" not in db_url:
        # Already covered by primary — mark as same source
        pass
    elif settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        sources.append(
            {
                "source_id": "supabase_connector",
                "name": "Supabase Cloud",
                "type": "API",
                "connector_type": "Supabase REST",
                "connector_icon": "cloud",
                "status": "configured",
                "latency_ms": None,
                "tables": [],
                "total_records": 0,
                "last_synced": None,
                "active_users": 0,
            }
        )

    return {
        "sources": sources,
        "total_sources": len(sources),
        "total_records": total_records,
        "database_type": db_type,
        "connection_status": db_status,
    }


# ---------------------------------------------------------------------------
# 2. Schema introspection
# ---------------------------------------------------------------------------


@router.get("/schema")
async def get_schema(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns column-level schema for key tables, including:
    - column name
    - data type
    - nullable
    - sample values (first 3 non-null values from the DB)
    """
    tid = current_user.tenant_id

    schema: list[dict] = []

    # ── Customers ──────────────────────────────────────────────────────────
    sample_custs = await db.execute(select(Customer).where(Customer.tenant_id == tid).limit(3))
    cust_rows = sample_custs.scalars().all()

    cust_columns = [
        {
            "name": "id",
            "type": "UUID (PK)",
            "nullable": False,
            "description": "Unique customer identifier",
        },
        {
            "name": "full_name",
            "type": "VARCHAR(255)",
            "nullable": False,
            "description": "Customer full name",
        },
        {"name": "email", "type": "VARCHAR(255)", "nullable": True, "description": "Contact email"},
        {
            "name": "phone_number",
            "type": "VARCHAR(30)",
            "nullable": True,
            "description": "Mobile number",
        },
        {
            "name": "city",
            "type": "VARCHAR(100)",
            "nullable": True,
            "description": "City of residence",
        },
        {
            "name": "account_type",
            "type": "VARCHAR(20)",
            "nullable": False,
            "description": "personal | business | merchant",
        },
        {
            "name": "kyc_status",
            "type": "VARCHAR(20)",
            "nullable": False,
            "description": "pending | verified | rejected",
        },
        {
            "name": "risk_score",
            "type": "DECIMAL(5,4)",
            "nullable": False,
            "description": "Fraud risk 0.0–1.0",
        },
        {
            "name": "customer_tier",
            "type": "VARCHAR(20)",
            "nullable": False,
            "description": "standard | premium | vip",
        },
        {
            "name": "balance_amount",
            "type": "DECIMAL(18,2)",
            "nullable": False,
            "description": "Current account balance (INR)",
        },
        {
            "name": "active_card_count",
            "type": "INTEGER",
            "nullable": False,
            "description": "Number of active cards",
        },
    ]

    for col in cust_columns:
        col["sample_values"] = [
            _safe_get(c, col["name"]) for c in cust_rows if _safe_get(c, col["name"]) is not None
        ][:3]

    schema.append({"table": "customers", "columns": cust_columns})

    # ── Transactions ───────────────────────────────────────────────────────
    sample_txns = await db.execute(
        select(Transaction)
        .where(
            Transaction.tenant_id == tid,
            Transaction.is_test == False,  # noqa: E712
        )
        .limit(3)
    )
    txn_rows = sample_txns.scalars().all()

    txn_columns = [
        {
            "name": "id",
            "type": "UUID (PK)",
            "nullable": False,
            "description": "Unique transaction ID",
        },
        {
            "name": "customer_id",
            "type": "UUID (FK)",
            "nullable": False,
            "description": "References customers.id",
        },
        {
            "name": "amount",
            "type": "DECIMAL(18,2)",
            "nullable": False,
            "description": "Transaction amount (INR)",
        },
        {
            "name": "currency",
            "type": "VARCHAR(3)",
            "nullable": False,
            "description": "ISO 4217 currency code",
        },
        {
            "name": "channel",
            "type": "VARCHAR(20)",
            "nullable": False,
            "description": "pos_physical | online | atm | mobile",
        },
        {
            "name": "merchant_name",
            "type": "VARCHAR(255)",
            "nullable": True,
            "description": "Merchant or payee name",
        },
        {
            "name": "city",
            "type": "VARCHAR(100)",
            "nullable": True,
            "description": "Transaction city",
        },
        {
            "name": "country_code",
            "type": "VARCHAR(2)",
            "nullable": True,
            "description": "ISO 3166-1 country code",
        },
        {
            "name": "location_lat",
            "type": "DECIMAL(10,8)",
            "nullable": True,
            "description": "Transaction latitude",
        },
        {
            "name": "location_lng",
            "type": "DECIMAL(10,8)",
            "nullable": True,
            "description": "Transaction longitude",
        },
        {
            "name": "device_type",
            "type": "VARCHAR(20)",
            "nullable": True,
            "description": "mobile | desktop | tablet | pos_terminal",
        },
        {
            "name": "device_fingerprint",
            "type": "VARCHAR(255)",
            "nullable": True,
            "description": "Device fingerprint hash",
        },
        {
            "name": "ip_address",
            "type": "VARCHAR(45)",
            "nullable": True,
            "description": "Client IP address",
        },
        {
            "name": "transaction_timestamp",
            "type": "TIMESTAMPTZ",
            "nullable": False,
            "description": "When the transaction occurred",
        },
        {
            "name": "status",
            "type": "VARCHAR(20)",
            "nullable": False,
            "description": "completed | blocked | flagged",
        },
        # FinShield fraud columns
        {
            "name": "fraud_score",
            "type": "DECIMAL(5,4)",
            "nullable": True,
            "description": "ML fraud probability 0.0–1.0",
        },
        {
            "name": "fraud_category",
            "type": "VARCHAR(20)",
            "nullable": True,
            "description": "legitimate | suspicious | fraudulent | unscored",
        },
        {
            "name": "fraud_risk_level",
            "type": "VARCHAR(10)",
            "nullable": True,
            "description": "low | medium | high | critical",
        },
        {
            "name": "is_flagged",
            "type": "BOOLEAN",
            "nullable": False,
            "description": "True if flagged for review",
        },
        {
            "name": "is_blocked",
            "type": "BOOLEAN",
            "nullable": False,
            "description": "True if transaction was blocked",
        },
        {
            "name": "triggered_rule_ids",
            "type": "JSON",
            "nullable": True,
            "description": "List of rule names triggered",
        },
        {
            "name": "model_version",
            "type": "VARCHAR(50)",
            "nullable": True,
            "description": "ML model version used",
        },
        {
            "name": "fraud_scored_at",
            "type": "TIMESTAMPTZ",
            "nullable": True,
            "description": "When fraud scoring completed",
        },
    ]

    for col in txn_columns:
        col["sample_values"] = [
            _safe_get(t, col["name"]) for t in txn_rows if _safe_get(t, col["name"]) is not None
        ][:3]

    schema.append({"table": "transactions", "columns": txn_columns})

    return {"schema": schema}


# ---------------------------------------------------------------------------
# 3. Transaction field map (for the UI's "field details" panel)
# ---------------------------------------------------------------------------


@router.get("/field-map")
async def get_field_map(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns key transaction fields with type, description and example.
    Also returns live counts of unique values to show data richness.
    """
    tid = current_user.tenant_id

    # Unique values in key enum columns
    channels_res = await db.execute(
        select(Transaction.channel, func.count(Transaction.id).label("cnt"))
        .where(Transaction.tenant_id == tid, Transaction.is_test == False)  # noqa: E712
        .group_by(Transaction.channel)
    )
    channels = [{"value": r.channel, "count": r.cnt} for r in channels_res.all()]

    device_res = await db.execute(
        select(Transaction.device_type, func.count(Transaction.id).label("cnt"))
        .where(Transaction.tenant_id == tid, Transaction.is_test == False)  # noqa: E712
        .group_by(Transaction.device_type)
    )
    devices = [{"value": r.device_type, "count": r.cnt} for r in device_res.all()]

    category_res = await db.execute(
        select(Transaction.fraud_category, func.count(Transaction.id).label("cnt"))
        .where(Transaction.tenant_id == tid, Transaction.is_test == False)  # noqa: E712
        .group_by(Transaction.fraud_category)
    )
    categories = [{"value": r.fraud_category, "count": r.cnt} for r in category_res.all()]

    # Amount stats
    amt_res = await db.execute(
        select(
            func.min(Transaction.amount).label("min"),
            func.max(Transaction.amount).label("max"),
            func.avg(Transaction.amount).label("avg"),
        ).where(Transaction.tenant_id == tid, Transaction.is_test == False)  # noqa: E712
    )
    amt_row = amt_res.first()
    amount_stats = (
        {
            "min": float(amt_row.min or 0),
            "max": float(amt_row.max or 0),
            "avg": round(float(amt_row.avg or 0), 2),
        }
        if amt_row
        else {}
    )

    return {
        "key_fields": [
            {
                "field": "amount",
                "type": "DECIMAL",
                "description": "Transaction amount in INR",
                "fraud_relevance": "High — large/unusual amounts trigger fraud rules",
                "stats": amount_stats,
            },
            {
                "field": "channel",
                "type": "ENUM",
                "description": "Transaction channel",
                "fraud_relevance": "Medium — online & ATM channels have higher fraud rates",
                "enum_distribution": channels,
            },
            {
                "field": "location_lat / location_lng",
                "type": "DECIMAL",
                "description": "Geographic coordinates of the transaction",
                "fraud_relevance": "Critical — impossible travel detection uses this field",
                "enum_distribution": [],
            },
            {
                "field": "device_type",
                "type": "ENUM",
                "description": "Device used for the transaction",
                "fraud_relevance": "Medium — new/unknown devices raise fraud score",
                "enum_distribution": devices,
            },
            {
                "field": "transaction_timestamp",
                "type": "TIMESTAMPTZ",
                "description": "When the transaction occurred",
                "fraud_relevance": "Medium — night-time (1–5 AM) transactions are flagged",
                "enum_distribution": [],
            },
            {
                "field": "fraud_category",
                "type": "ENUM",
                "description": "FinShield fraud label written back to each transaction",
                "fraud_relevance": "Output — result of ML scoring pipeline",
                "enum_distribution": categories,
            },
        ]
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _safe_get(obj: Any, attr: str) -> Any:
    val = getattr(obj, attr, None)
    if val is None:
        return None
    # Convert to JSON-safe types
    if hasattr(val, "isoformat"):
        return val.isoformat()
    try:
        import decimal

        if isinstance(val, decimal.Decimal):
            return float(val)
    except Exception:
        pass
    return str(val) if not isinstance(val, (int, float, bool, str)) else val
