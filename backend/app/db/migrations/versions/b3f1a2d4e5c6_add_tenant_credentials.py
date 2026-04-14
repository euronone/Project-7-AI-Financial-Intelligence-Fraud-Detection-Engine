"""add_tenant_credentials

Revision ID: b3f1a2d4e5c6
Revises: 99747162cf82
Create Date: 2026-04-11 10:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "b3f1a2d4e5c6"
down_revision: Union[str, None] = "99747162cf82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_credentials",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("service", sa.String(length=64), nullable=False),
        sa.Column("key_name", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("value_encrypted", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "service", "key_name", name="uq_tenant_service_key"),
    )
    op.create_index("ix_tenant_credentials_tenant_id", "tenant_credentials", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_tenant_credentials_tenant_id", table_name="tenant_credentials")
    op.drop_table("tenant_credentials")
