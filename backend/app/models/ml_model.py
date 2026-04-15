"""ML model registry."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=True, index=True
    )  # None = global shared model

    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(
        String(30), default="ensemble"
    )  # fraud_classifier|anomaly_detector|risk_scorer|ensemble
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="training"
    )  # training|validating|active|retired|failed

    # Performance metrics
    precision: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    recall: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    auc_roc: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    false_positive_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    training_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Artifact storage
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feature_importance: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
