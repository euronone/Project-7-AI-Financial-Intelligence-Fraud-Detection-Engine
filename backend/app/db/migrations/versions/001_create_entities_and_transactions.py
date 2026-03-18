"""Create entities and transactions tables.

Revision ID: 001
Revises:
Create Date: 2026-03-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enum(name: str, *values: str) -> postgresql.ENUM:
    """Return a postgresql.ENUM that never auto-creates/drops the PG type.

    We manage CREATE/DROP TYPE manually via raw DDL so that:
    - The migration is idempotent (safe to re-run on a DB that already has the type).
    - Alembic's before_create event doesn't fire a duplicate CREATE TYPE.
    """
    return postgresql.ENUM(*values, name=name, create_type=False)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ── Create ENUM types idempotently via raw DDL ────────────────────────────
    enum_ddl = [
        ("entity_type_enum",            "'individual','business','merchant'"),
        ("risk_level_enum",             "'low','medium','high','critical'"),
        ("kyc_status_enum",             "'pending','verified','rejected','expired'"),
        ("transaction_type_enum",       "'payment','transfer','withdrawal','deposit','refund'"),
        ("transaction_channel_enum",    "'online','pos','atm','mobile','wire','ach'"),
        ("transaction_status_enum",     "'pending','completed','failed','reversed','flagged','blocked'"),
        ("transaction_risk_level_enum", "'low','medium','high','critical'"),
    ]
    for type_name, vals in enum_ddl:
        op.execute(
            f"DO $$ BEGIN "
            f"CREATE TYPE {type_name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; "
            f"END $$;"
        )

    # ── entities ──────────────────────────────────────────────────────────────
    op.create_table(
        "entities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("entity_type", _enum("entity_type_enum", "individual", "business", "merchant"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
        sa.Column("risk_level", _enum("risk_level_enum", "low", "medium", "high", "critical"), nullable=False, server_default="low"),
        sa.Column("is_watchlisted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "kyc_status",
            _enum("kyc_status_enum", "pending", "verified", "rejected", "expired"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )

    # ── transactions (range-partitioned by processed_at monthly) ─────────────
    # Base partitioned table — no direct rows; child partitions hold data.
    op.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id                    UUID NOT NULL DEFAULT gen_random_uuid(),
            external_id           VARCHAR(255) NOT NULL,
            source_entity_id      UUID NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
            destination_entity_id UUID REFERENCES entities(id) ON DELETE SET NULL,
            amount                NUMERIC(18, 4) NOT NULL,
            currency              VARCHAR(3) NOT NULL,
            transaction_type      transaction_type_enum NOT NULL,
            channel               transaction_channel_enum NOT NULL,
            status                transaction_status_enum NOT NULL,
            merchant_category_code VARCHAR(4),
            description           TEXT,
            ip_address            INET,
            device_fingerprint    VARCHAR(255),
            geolocation_lat       NUMERIC(10, 7),
            geolocation_lng       NUMERIC(10, 7),
            country_code          VARCHAR(2),
            card_present          BOOLEAN,
            fraud_score           NUMERIC(5, 4),
            risk_level            transaction_risk_level_enum,
            processed_at          TIMESTAMPTZ NOT NULL,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, processed_at)
        ) PARTITION BY RANGE (processed_at);
    """)

    # PostgreSQL requires unique indexes on partitioned tables to include the partition key.
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_external_id ON transactions (external_id, processed_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_source_entity ON transactions (source_entity_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_processed_at ON transactions (processed_at DESC);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_fraud_score ON transactions (fraud_score DESC NULLS LAST);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);")

    # Default partition for rows outside explicit ranges.
    op.execute("CREATE TABLE IF NOT EXISTS transactions_default PARTITION OF transactions DEFAULT;")

    # Monthly partitions for current and next two months.
    op.execute("""
        DO $$ BEGIN
            CREATE TABLE transactions_2026_03
                PARTITION OF transactions FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
        EXCEPTION WHEN duplicate_table THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TABLE transactions_2026_04
                PARTITION OF transactions FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
        EXCEPTION WHEN duplicate_table THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TABLE transactions_2026_05
                PARTITION OF transactions FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
        EXCEPTION WHEN duplicate_table THEN NULL; END $$;
    """)


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS transactions CASCADE;")
    op.execute("DROP TABLE IF EXISTS entities CASCADE;")

    for name in [
        "transaction_risk_level_enum",
        "transaction_status_enum",
        "transaction_channel_enum",
        "transaction_type_enum",
        "kyc_status_enum",
        "risk_level_enum",
        "entity_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {name};")
