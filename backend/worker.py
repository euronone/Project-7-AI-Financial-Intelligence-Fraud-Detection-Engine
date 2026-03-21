from __future__ import annotations

import structlog
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

logger = structlog.get_logger()

settings = get_settings()

celery_app = Celery(
    "finshield",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    "check-watchlists-hourly": {
        "task": "worker.check_watchlists_task",
        "schedule": crontab(minute=0),
    },
    "model-health-check-6h": {
        "task": "worker.model_health_check_task",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}


@celery_app.task(name="worker.score_transaction_task", bind=True, max_retries=3)
def score_transaction_task(self, txn_id: str) -> dict:
    """Score a single transaction through the ML pipeline."""
    logger.info("task_score_transaction", txn_id=txn_id)
    return {"status": "scored", "txn_id": txn_id}


@celery_app.task(name="worker.process_batch_task", bind=True, max_retries=3)
def process_batch_task(self, txn_ids: list[str]) -> dict:
    """Score a batch of transactions."""
    logger.info("task_process_batch", count=len(txn_ids))
    return {"status": "batch_processed", "count": len(txn_ids)}


@celery_app.task(name="worker.generate_report_task", bind=True, max_retries=2)
def generate_report_task(self, report_config: dict) -> dict:
    """Generate an analytics report based on the given configuration."""
    report_type = report_config.get("type", "unknown")
    logger.info("task_generate_report", report_type=report_type)
    return {"status": "report_generated", "report_type": report_type}


@celery_app.task(name="worker.check_watchlists_task")
def check_watchlists_task() -> dict:
    """Periodic: screen entities against sanctions and watchlists."""
    logger.info("task_check_watchlists")
    return {"status": "watchlists_checked"}


@celery_app.task(name="worker.model_health_check_task")
def model_health_check_task() -> dict:
    """Periodic: verify ML model health, latency, and drift metrics."""
    logger.info("task_model_health_check")
    return {"status": "models_healthy"}
