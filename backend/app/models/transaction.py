"""Transaction ORM model.

Table is partitioned by processed_at (monthly) in production.
Indexes cover the most common query patterns: entity, time, fraud score, status.
"""
import uuid
import enum
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.models.base import Base


class TransactionType(str, enum.Enum):
    payment = "payment"
    transfer = "transfer"
    withdrawal = "withdrawal"
    deposit = "deposit"
    refund = "refund"


class TransactionChannel(str, enum.Enum):
    online = "online"
    pos = "pos"
    atm = "atm"
    mobile = "mobile"
    wire = "wire"
    ach = "ach"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    reversed = "reversed"
    flagged = "flagged"
    blocked = "blocked"


class TransactionRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Transaction(Base):
    """Financial transaction record — the central entity of the fraud pipeline."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_source_entity", "source_entity_id"),
        Index("idx_transactions_processed_at", "processed_at"),
        Index("idx_transactions_fraud_score", "fraud_score"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_external_id", "external_id"),
        # NOTE: Range partitioning by processed_at (monthly) is applied via
        # the Alembic migration using raw DDL — SQLAlchemy ORM does not
        # manage partitions natively.
    )

    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destination_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum"), nullable=False
    )
    channel: Mapped[TransactionChannel] = mapped_column(
        Enum(TransactionChannel, name="transaction_channel_enum"), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status_enum"), nullable=False
    )
    merchant_category_code: Mapped[str | None] = mapped_column(
        String(4), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    geolocation_lat: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    geolocation_lng: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    card_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fraud_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    risk_level: Mapped[TransactionRiskLevel | None] = mapped_column(
        Enum(TransactionRiskLevel, name="transaction_risk_level_enum"),
        nullable=True,
    )
    processed_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    source_entity: Mapped["Entity"] = relationship(  # noqa: F821
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="source_transactions",
        lazy="noload",
    )
    destination_entity: Mapped["Entity | None"] = relationship(  # noqa: F821
        "Entity",
        foreign_keys=[destination_entity_id],
        back_populates="destination_transactions",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} external_id={self.external_id!r} "
            f"amount={self.amount} status={self.status}>"
        )
