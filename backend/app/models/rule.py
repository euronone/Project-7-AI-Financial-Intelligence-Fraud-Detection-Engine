"""Fraud detection rules model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class FraudRule(Base):
    __tablename__ = "fraud_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=True, index=True
    )  # None = global rule

    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_category: Mapped[str] = mapped_column(
        String(20), default="velocity"
    )  # velocity|amount|geographic|device|pattern|behavioral
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Rule DSL stored as JSON (mirrors YAML config)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    threshold: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Action
    action: Mapped[str] = mapped_column(String(20), default="flag")  # flag|block|alert|log
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high|critical
    notify_channels: Mapped[list | None] = mapped_column(
        JSON, default=list
    )  # ["email","sms","push"]

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)

    # Performance metrics
    false_positive_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    hit_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    total_triggers: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
