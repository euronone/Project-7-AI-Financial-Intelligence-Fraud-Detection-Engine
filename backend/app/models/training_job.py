"""Training Job model — tracks custom ML model training runs."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class TrainingJob(Base):
    """
    Persists a single ML training run initiated by a tenant.

    Status lifecycle:
        queued → running → optimizing → evaluating → completed
                                                    → failed
    """

    __tablename__ = "training_jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # ── User-chosen configuration ────────────────────────────────────────────
    selected_algorithms: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # ["xgboost", "random_forest", "isolation_forest", ...]

    data_window_days: Mapped[int] = mapped_column(Integer, default=90)
    # 30 | 60 | 90 | 180 | 365 | 0 = all-time

    auto_optimize: Mapped[bool] = mapped_column(Boolean, default=True)
    # Whether to run hyperparameter tuning after initial training

    use_custom_columns: Mapped[bool] = mapped_column(Boolean, default=True)
    # Whether to respect enabled/disabled flags from schema mapping

    parent_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Set when this is a "re-optimize" run spawned from a completed job

    # ── Runtime progress (updated by background coroutine) ────────────────────
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued | running | optimizing | evaluating | completed | failed | cancelled

    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    # 0–100

    current_stage: Mapped[str] = mapped_column(String(120), default="Queued")
    # Human-readable label for the live progress display

    log_lines: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    # [{"ts": "ISO", "msg": "..."}, ...]

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Results (populated on completion) ────────────────────────────────────
    result_model_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # FK to ml_models.id — set after promote

    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # { algo_id: { precision, recall, f1_score, auc_roc, ... }, "ensemble": {...} }

    best_algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    optimization_rounds: Mapped[int] = mapped_column(Integer, default=0)
    training_samples: Mapped[int] = mapped_column(Integer, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── Uploaded pickle (optional) ────────────────────────────────────────────
    uploaded_model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_model_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
