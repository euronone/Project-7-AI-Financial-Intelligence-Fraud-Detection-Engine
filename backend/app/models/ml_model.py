import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ModelType(str, enum.Enum):
    FRAUD_CLASSIFIER = "fraud_classifier"
    ANOMALY_DETECTOR = "anomaly_detector"
    RISK_SCORER = "risk_scorer"
    BEHAVIORAL_PROFILER = "behavioral_profiler"


class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    VALIDATING = "validating"
    ACTIVE = "active"
    RETIRED = "retired"
    FAILED = "failed"


class MLModel(BaseModel):
    __tablename__ = "ml_models"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_name_version"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="ml_model_type", create_constraint=True), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="ml_model_status", create_constraint=True), nullable=False
    )
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    training_dataset_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
