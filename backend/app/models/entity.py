"""Entity ORM model — represents individuals, businesses, and merchants."""
import uuid
from decimal import Decimal

import enum

from sqlalchemy import Boolean, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EntityType(str, enum.Enum):
    individual = "individual"
    business = "business"
    merchant = "merchant"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class KYCStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    expired = "expired"


class Entity(Base):
    """Participant in a transaction — individual, business, or merchant."""

    __tablename__ = "entities"

    external_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type_enum"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="0.0000"
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum"),
        nullable=False,
        server_default="low",
    )
    is_watchlisted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    kyc_status: Mapped[KYCStatus] = mapped_column(
        Enum(KYCStatus, name="kyc_status_enum"),
        nullable=False,
        server_default="pending",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    # Relationships
    source_transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction",
        foreign_keys="Transaction.source_entity_id",
        back_populates="source_entity",
        lazy="noload",
    )
    destination_transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction",
        foreign_keys="Transaction.destination_entity_id",
        back_populates="destination_entity",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Entity id={self.id} type={self.entity_type} name={self.name!r}>"
