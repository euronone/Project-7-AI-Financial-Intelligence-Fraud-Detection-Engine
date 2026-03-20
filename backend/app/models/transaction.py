import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    REFUND = "refund"


class TransactionChannel(str, enum.Enum):
    ONLINE = "online"
    POS = "pos"
    ATM = "atm"
    MOBILE = "mobile"
    WIRE = "wire"
    ACH = "ach"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True
    )
    destination_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type", create_constraint=True), nullable=False
    )
    channel: Mapped[TransactionChannel] = mapped_column(
        Enum(TransactionChannel, name="transaction_channel", create_constraint=True), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status", create_constraint=True), nullable=False
    )
    merchant_category_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geolocation_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    geolocation_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    card_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fraud_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    processed_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
