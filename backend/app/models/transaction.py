"""Transaction model — core entity for fraud scoring."""

import ast
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, JSON, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class SafeJSON(TypeDecorator):
    """
    JSON column that gracefully handles values stored as Python repr
    (e.g. "['rule1']") rather than valid JSON (e.g. '["rule1"]').

    Uses Text as impl so SQLAlchemy passes raw strings to process_result_value
    without first attempting json.loads() — which would raise on Python repr.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Serialize to JSON string on write."""
        if value is None:
            return None
        if isinstance(value, str):
            return value  # already serialized
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Deserialize on read; fall back to ast.literal_eval for Python repr."""
        if value is None:
            return None
        if isinstance(value, (list, dict)):
            return value  # already deserialized (some drivers do this)
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            try:
                return ast.literal_eval(value)  # handles "['rule1']" repr format
            except Exception:
                return []  # last resort — return empty list rather than crash


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=True, index=True
    )

    # Payment details
    card_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant_category_code: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # Amount
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    # Type & channel
    transaction_type: Mapped[str] = mapped_column(
        String(20), default="purchase"
    )  # purchase|withdrawal|transfer|refund|reversal
    channel: Mapped[str] = mapped_column(
        String(20), default="online"
    )  # pos_physical|online|atm|mobile|wire|ach

    # Location & device
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # mobile|desktop|tablet|pos_terminal

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )  # pending|completed|failed|reversed|flagged|blocked

    # ── FinShield Fraud Detection Fields ────────────────────────────────────
    fraud_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, index=True)
    fraud_risk_level: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # low|medium|high|critical
    fraud_category: Mapped[str] = mapped_column(
        String(20), default="unscored", index=True
    )  # legitimate|suspicious|fraudulent|unscored
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    triggered_rule_ids: Mapped[list | None] = mapped_column(SafeJSON, default=list)
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fraud_scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    alerts: Mapped[list["FraudAlert"]] = relationship("FraudAlert", back_populates="transaction")


# Avoid circular import
from app.models.fraud_alert import FraudAlert  # noqa: E402
