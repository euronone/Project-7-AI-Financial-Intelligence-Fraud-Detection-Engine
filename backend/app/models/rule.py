import enum
import uuid

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RuleCategory(str, enum.Enum):
    VELOCITY = "velocity"
    AMOUNT = "amount"
    GEOGRAPHY = "geography"
    PATTERN = "pattern"
    DEVICE = "device"
    CUSTOM = "custom"


class RuleSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Rule(BaseModel):
    __tablename__ = "rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[RuleCategory] = mapped_column(
        Enum(RuleCategory, name="rule_category", create_constraint=True), nullable=False
    )
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    severity: Mapped[RuleSeverity] = mapped_column(
        Enum(RuleSeverity, name="rule_severity", create_constraint=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    hit_count: Mapped[int] = mapped_column(BigInteger, default=0)
    false_positive_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
