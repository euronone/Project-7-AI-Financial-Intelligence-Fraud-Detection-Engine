"""TenantCredential model — stores encrypted BYOK API keys per institution."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class TenantCredential(Base):
    """
    One row = one named credential belonging to a tenant.

    Example rows for tenant "Acme Bank":
        service="resend",    key_name="resend_api_key",          value_encrypted="gAAA..."
        service="twilio",    key_name="twilio_account_sid",      value_encrypted="gAAA..."
        service="twilio",    key_name="twilio_auth_token",       value_encrypted="gAAA..."
        service="supabase",  key_name="supabase_service_key",    value_encrypted="gAAA..."
    """

    __tablename__ = "tenant_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "service", "key_name", name="uq_tenant_service_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Logical grouping — e.g. "resend", "twilio", "stripe", "openai"
    service: Mapped[str] = mapped_column(String(64), nullable=False)

    # Human-readable key name — e.g. "resend_api_key", "twilio_auth_token"
    key_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Human label shown in the UI — e.g. "Production API Key"
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Fernet-encrypted secret value
    value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # Audit
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
