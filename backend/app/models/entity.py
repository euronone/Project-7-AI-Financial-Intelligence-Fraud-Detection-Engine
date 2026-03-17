import enum

from sqlalchemy import Boolean, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EntityType(str, enum.Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    MERCHANT = "merchant"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Entity(BaseModel):
    __tablename__ = "entities"

    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type", create_constraint=True), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level", create_constraint=True),
        default=RiskLevel.LOW,
    )
    is_watchlisted: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_status: Mapped[KYCStatus] = mapped_column(
        Enum(KYCStatus, name="kyc_status", create_constraint=True),
        default=KYCStatus.PENDING,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
