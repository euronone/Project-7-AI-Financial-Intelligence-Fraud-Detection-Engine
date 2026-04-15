"""Customer model."""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Identity
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Address
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="IN")

    # Account
    account_type: Mapped[str] = mapped_column(
        String(20), default="personal"
    )  # personal|business|merchant
    account_opening_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    account_status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active|inactive|suspended|closed

    # KYC
    kyc_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending|verified|rejected|expired
    kyc_verification_level: Mapped[str] = mapped_column(
        String(20), default="basic"
    )  # basic|enhanced|full

    # Risk
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)
    customer_tier: Mapped[str] = mapped_column(
        String(20), default="standard"
    )  # standard|premium|vip

    # Banking
    balance_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0)
    active_card_count: Mapped[int] = mapped_column(Integer, default=0)
    preferred_card_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Misc
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
