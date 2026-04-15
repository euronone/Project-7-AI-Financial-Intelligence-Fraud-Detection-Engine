"""User and Tenant (Institution) models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Tenant(Base):
    """Represents a financial institution (bank, fintech, insurance, etc.)."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[str] = mapped_column(
        String(30), default="bank"
    )  # bank|fintech|insurance|payment_processor|neobank
    subscription_plan: Mapped[str] = mapped_column(String(20), default="free")  # free|pro|advanced
    plan_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Encrypted DB credentials (stored after onboarding)
    db_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # supabase|postgresql|mysql|mongodb|rest_api
    db_url_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    db_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Schema mapping — client's column names → FinShield's canonical names
    # Stored as {"customers": {"customer_id": "cust_ref", ...}, "transactions": {...}}
    schema_mapping_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ML model settings
    model_strategy: Mapped[str] = mapped_column(
        String(20), default="shared_global"
    )  # shared_global|dedicated|hybrid
    active_model_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")


class User(Base):
    """Platform user (admin, analyst, viewer) belonging to a tenant."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="analyst")  # admin|analyst|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supabase_uid: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    has_completed_onboarding: Mapped[bool] = mapped_column(Boolean, default=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Admin-forced reset flag
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
