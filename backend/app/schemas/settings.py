"""Settings schemas — production-ready database connection definitions."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


# 15 supported database / integration types
DbType = Literal[
    "supabase",
    "postgresql",
    "mysql",
    "mongodb",
    "mssql",
    "oracle",
    "redis",
    "dynamodb",
    "firestore",
    "snowflake",
    "cockroachdb",
    "neon",
    "planetscale",
    "clickhouse",
    "rest_api",
]


class DbConnectionRequest(BaseModel):
    """
    Universal database connection request.

    Fields are a union of all database types — only the fields
    relevant to the selected db_type need to be populated.
    """

    db_type: DbType

    # ── Display ──────────────────────────────────────────────────────────
    label: Optional[str] = None  # Human-readable connection name

    # ── Direct connection fields (PostgreSQL, MySQL, MSSQL, Oracle, etc.) ─
    host: Optional[str] = None  # Hostname / IP
    port: Optional[int] = Field(None, ge=1, le=65535)  # TCP port
    db_name: Optional[str] = None  # Database / schema name
    db_user: Optional[str] = None  # Username
    db_password: Optional[str] = None  # Password (encrypted at rest)
    schema_name: Optional[str] = None  # PostgreSQL / Oracle schema
    ssl_mode: Optional[str] = None  # disable | require | verify-ca | verify-full
    db_url: Optional[str] = None  # Full DSN (alternative to host/port)

    # ── Connection pool ──────────────────────────────────────────────────
    pool_size: Optional[int] = Field(None, ge=1, le=100)
    max_overflow: Optional[int] = Field(None, ge=0, le=200)
    connection_timeout: Optional[int] = Field(None, ge=1, le=300)  # seconds

    # ── Supabase ─────────────────────────────────────────────────────────
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None  # SUPABASE_SERVICE_KEY
    supabase_service_role_key: Optional[str] = (
        None  # SUPABASE_SERVICE_ROLE_KEY (same JWT, alternate env-var name)
    )
    supabase_db_password: Optional[str] = None  # SUPABASE_DB_PASSWORD (Postgres DB password)

    # ── Oracle specific ──────────────────────────────────────────────────
    oracle_service_name: Optional[str] = None  # Oracle service name or SID
    oracle_wallet_location: Optional[str] = None  # mTLS wallet path

    # ── MongoDB ──────────────────────────────────────────────────────────
    mongo_connection_string: Optional[str] = None  # Full MongoDB URI
    auth_source: Optional[str] = None  # MongoDB authentication database

    # ── Redis ────────────────────────────────────────────────────────────
    redis_password: Optional[str] = None
    redis_db_index: Optional[int] = Field(None, ge=0, le=15)
    redis_use_tls: Optional[bool] = None

    # ── Amazon DynamoDB ──────────────────────────────────────────────────
    aws_region: Optional[str] = None  # e.g. ap-south-1
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None  # For assumed-role auth
    dynamodb_table_prefix: Optional[str] = None  # Table name prefix

    # ── Google Firestore ─────────────────────────────────────────────────
    gcp_project_id: Optional[str] = None
    firestore_collection_prefix: Optional[str] = None
    service_account_json: Optional[str] = None  # Base64-encoded JSON key

    # ── Snowflake ────────────────────────────────────────────────────────
    snowflake_account: Optional[str] = None  # <account>.<region>
    snowflake_warehouse: Optional[str] = None  # Compute warehouse name
    snowflake_database: Optional[str] = None
    snowflake_schema: Optional[str] = None
    snowflake_role: Optional[str] = None  # e.g. SYSADMIN, ANALYST

    # ── PlanetScale ──────────────────────────────────────────────────────
    planetscale_host: Optional[str] = None  # aws.connect.psdb.cloud
    planetscale_username: Optional[str] = None
    planetscale_password: Optional[str] = None  # Database password token

    # ── ClickHouse ───────────────────────────────────────────────────────
    clickhouse_http_port: Optional[int] = None  # Default: 8123 (HTTP), 9000 (native)
    clickhouse_native_port: Optional[int] = None
    clickhouse_cluster: Optional[str] = None  # Cluster name for distributed queries

    # ── Neon (serverless PostgreSQL) ─────────────────────────────────────
    neon_connection_string: Optional[str] = None  # postgresql://user:pw@ep-xxx.neon.tech/db

    # ── Generic REST API / CSV ───────────────────────────────────────────
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    api_auth_header: Optional[str] = None  # e.g. X-API-Key, Authorization


class DbConnectionResponse(BaseModel):
    db_type: str
    label: Optional[str]
    is_connected: bool
    message: str


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[float] = None
