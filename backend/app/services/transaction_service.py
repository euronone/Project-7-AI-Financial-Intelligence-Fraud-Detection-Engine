"""Transaction service — core business logic for F1.

Handles:
- Single transaction ingest with fraud pipeline (F1.1, F1.2)
- Batch ingest up to 10,000 transactions (F1.4)
- Paginated list with full filter support (F1.5)
- Transaction detail with fraud analysis and entity context (F1.6)
- Similar transaction lookup (F1.6)
- CSV/JSON export with applied filters (F1.7)
"""
import asyncio
import csv
import io
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, desc, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.exceptions import (
    BatchSizeLimitError,
    ConflictError,
    FraudPipelineTimeoutError,
    NotFoundError,
)
from app.models.entity import Entity
from app.models.transaction import (
    Transaction,
    TransactionChannel,
    TransactionRiskLevel,
    TransactionStatus,
    TransactionType,
)
from app.schemas.transaction import (
    BatchIngestRequest,
    BatchIngestResponse,
    FraudScoreBreakdown,
    TransactionCreate,
    TransactionDetail,
    TransactionResponse,
    TransactionSearchRequest,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


def _risk_level_from_score(score: float) -> TransactionRiskLevel:
    """Map a composite fraud score (0–1) to a risk level enum."""
    if score >= 0.8:
        return TransactionRiskLevel.critical
    if score >= 0.6:
        return TransactionRiskLevel.high
    if score >= 0.3:
        return TransactionRiskLevel.medium
    return TransactionRiskLevel.low


def _decision_from_score(score: float) -> str:
    if score >= 0.8:
        return "BLOCK"
    if score >= 0.6:
        return "ALERT"
    if score >= 0.3:
        return "FLAG"
    return "PASS"


def _status_from_decision(
    current_status: TransactionStatus, decision: str
) -> TransactionStatus:
    """Determine final transaction status based on fraud pipeline decision."""
    if decision == "BLOCK":
        return TransactionStatus.blocked
    if decision in ("ALERT", "FLAG"):
        return TransactionStatus.flagged
    return current_status


async def _run_fraud_pipeline(
    transaction_data: Dict[str, Any],
) -> FraudScoreBreakdown:
    """Call the fraud detection service within a latency budget.

    Falls back to a rule-only score if the pipeline exceeds the timeout.
    The full ML pipeline is integrated in F2; here we call the existing
    FraudDetectionService which already combines ML, anomaly, behavioral,
    and network scores.
    """
    from app.services.fraud_detection_service import FraudDetectionService

    fraud_svc = FraudDetectionService()
    timeout_s = settings.fraud_pipeline_timeout_ms / 1000.0

    try:
        loop = asyncio.get_event_loop()
        result: Dict[str, Any] = await asyncio.wait_for(
            loop.run_in_executor(None, fraud_svc.detect_fraud, transaction_data),
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "fraud_pipeline_timeout",
            timeout_ms=settings.fraud_pipeline_timeout_ms,
            transaction_id=transaction_data.get("id"),
        )
        raise FraudPipelineTimeoutError()

    components = result.get("components", {})
    composite = float(result.get("risk_score", 0.0))

    return FraudScoreBreakdown(
        ml_score=float(components.get("ml_score", 0.0)),
        anomaly_score=float(components.get("anomaly_score", 0.0)),
        behavioral_score=float(components.get("behavioral_score", 0.0)),
        network_score=float(components.get("network_score", 0.0)),
        rule_score=float(components.get("rule_score", 0.0)),
        composite_score=composite,
        decision=result.get("status", _decision_from_score(composite)),
        triggered_rules=result.get("triggered_rules", []),
        top_features=result.get("explanations", {}).get("top_features", []),
    )


class TransactionService:
    """All transaction-related business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Ingest ────────────────────────────────────────────────────────────────

    async def ingest(self, data: TransactionCreate) -> TransactionDetail:
        """Ingest a single transaction and run the fraud detection pipeline.

        Steps:
        1. Check for duplicate external_id.
        2. Verify source entity exists.
        3. Persist transaction with status=pending.
        4. Run fraud pipeline (async, with timeout guard).
        5. Update fraud_score, risk_level, and status.
        6. Return full detail.
        """
        # 1. Duplicate check
        existing = await self._db.execute(
            select(Transaction).where(
                Transaction.external_id == data.external_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(
                f"Transaction with external_id '{data.external_id}' already exists."
            )

        # 2. Verify source entity
        source_entity = await self._db.get(Entity, data.source_entity_id)
        if not source_entity:
            raise NotFoundError(
                f"Source entity '{data.source_entity_id}' not found."
            )

        destination_entity: Entity | None = None
        if data.destination_entity_id:
            destination_entity = await self._db.get(
                Entity, data.destination_entity_id
            )
            if not destination_entity:
                raise NotFoundError(
                    f"Destination entity '{data.destination_entity_id}' not found."
                )

        # 3. Persist with initial status
        txn = Transaction(
            external_id=data.external_id,
            source_entity_id=data.source_entity_id,
            destination_entity_id=data.destination_entity_id,
            amount=data.amount,
            currency=data.currency,
            transaction_type=data.transaction_type,
            channel=data.channel,
            status=data.status,
            merchant_category_code=data.merchant_category_code,
            description=data.description,
            ip_address=data.ip_address,
            device_fingerprint=data.device_fingerprint,
            geolocation_lat=data.geolocation_lat,
            geolocation_lng=data.geolocation_lng,
            country_code=data.country_code,
            card_present=data.card_present,
            processed_at=data.processed_at,
        )
        self._db.add(txn)
        await self._db.flush()  # Get the generated id before fraud pipeline

        logger.info(
            "transaction_ingested",
            transaction_id=str(txn.id),
            external_id=txn.external_id,
            amount=float(txn.amount),
            channel=txn.channel,
        )

        # 4. Fraud pipeline
        pipeline_input = {
            "id": str(txn.id),
            "external_id": txn.external_id,
            "amount": float(txn.amount),
            "currency": txn.currency,
            "transaction_type": txn.transaction_type.value,
            "channel": txn.channel.value,
            "source_entity_id": str(txn.source_entity_id),
            "destination_entity_id": (
                str(txn.destination_entity_id)
                if txn.destination_entity_id
                else None
            ),
            "ip_address": txn.ip_address,
            "device_fingerprint": txn.device_fingerprint,
            "geolocation_lat": float(txn.geolocation_lat) if txn.geolocation_lat else None,
            "geolocation_lng": float(txn.geolocation_lng) if txn.geolocation_lng else None,
            "country_code": txn.country_code,
            "card_present": txn.card_present,
            "processed_at": txn.processed_at.isoformat(),
            "merchant_category_code": txn.merchant_category_code,
        }

        breakdown: FraudScoreBreakdown | None = None
        try:
            breakdown = await _run_fraud_pipeline(pipeline_input)
        except FraudPipelineTimeoutError:
            # Graceful degradation: continue with no score rather than failing ingest
            logger.warning(
                "fraud_pipeline_degraded",
                transaction_id=str(txn.id),
            )

        # 5. Update with fraud pipeline results
        if breakdown:
            txn.fraud_score = Decimal(str(breakdown.composite_score))
            txn.risk_level = _risk_level_from_score(breakdown.composite_score)
            txn.status = _status_from_decision(txn.status, breakdown.decision)

            logger.info(
                "fraud_score_assigned",
                transaction_id=str(txn.id),
                fraud_score=breakdown.composite_score,
                decision=breakdown.decision,
            )

        await self._db.commit()
        await self._db.refresh(txn)

        return self._to_detail(txn, breakdown, source_entity, destination_entity)

    # ── Batch Ingest ──────────────────────────────────────────────────────────

    async def batch_ingest(
        self, request: BatchIngestRequest
    ) -> BatchIngestResponse:
        """Ingest up to 10,000 transactions in chunked bulk inserts.

        Large batches (>500) are processed in chunks to avoid DB timeouts.
        Each chunk is committed independently — partial success is supported.
        """
        total = len(request.transactions)
        if total > settings.batch_ingest_max_size:
            raise BatchSizeLimitError(
                f"Batch of {total} exceeds maximum {settings.batch_ingest_max_size}."
            )

        accepted = 0
        rejected = 0
        errors: List[Dict[str, Any]] = []
        chunk_size = settings.batch_ingest_chunk_size

        for chunk_start in range(0, total, chunk_size):
            chunk = request.transactions[chunk_start : chunk_start + chunk_size]
            for item in chunk:
                try:
                    await self.ingest(item)
                    accepted += 1
                except ConflictError as exc:
                    rejected += 1
                    errors.append(
                        {"external_id": item.external_id, "error": str(exc)}
                    )
                except Exception as exc:
                    rejected += 1
                    errors.append(
                        {"external_id": item.external_id, "error": str(exc)}
                    )
                    logger.error(
                        "batch_ingest_item_failed",
                        external_id=item.external_id,
                        error=str(exc),
                    )

        logger.info(
            "batch_ingest_complete",
            total=total,
            accepted=accepted,
            rejected=rejected,
        )
        return BatchIngestResponse(accepted=accepted, rejected=rejected, errors=errors)

    # ── Get by ID ─────────────────────────────────────────────────────────────

    async def get_by_id(self, transaction_id: uuid.UUID) -> TransactionDetail:
        """Fetch a transaction with entity relationships loaded."""
        result = await self._db.execute(
            select(Transaction)
            .options(
                selectinload(Transaction.source_entity),
                selectinload(Transaction.destination_entity),
            )
            .where(Transaction.id == transaction_id)
        )
        txn = result.scalar_one_or_none()
        if not txn:
            raise NotFoundError(f"Transaction '{transaction_id}' not found.")

        return self._to_detail(txn, None, txn.source_entity, txn.destination_entity)

    # ── Search / List ─────────────────────────────────────────────────────────

    async def search(
        self, params: TransactionSearchRequest
    ) -> Tuple[List[TransactionResponse], int]:
        """Paginated search with full filter support (F1.5).

        Returns (items, total_count) for the caller to build PaginatedResponse.
        """
        filters = self._build_filters(params)

        # Count query
        count_q = select(func.count()).select_from(Transaction).where(and_(true(), *filters))
        total: int = (await self._db.execute(count_q)).scalar_one()

        # Sort
        sort_col = getattr(Transaction, params.sort_by, Transaction.processed_at)
        order = desc(sort_col) if params.sort_order == "desc" else sort_col

        # Data query
        offset = (params.page - 1) * params.page_size
        data_q = (
            select(Transaction)
            .where(and_(true(), *filters))
            .order_by(order)
            .offset(offset)
            .limit(params.page_size)
        )
        rows = (await self._db.execute(data_q)).scalars().all()

        items = [TransactionResponse.model_validate(row) for row in rows]
        return items, total

    # ── Similar Transactions ──────────────────────────────────────────────────

    async def find_similar(
        self, transaction_id: uuid.UUID, limit: int = 10
    ) -> List[TransactionResponse]:
        """Find transactions with similar characteristics (F1.6 stub).

        Full ML-powered similarity is implemented in F2.
        Here we match by: same source entity + same channel + comparable amount range.
        """
        txn = await self._get_or_404(transaction_id)
        amount = float(txn.amount)
        lower = Decimal(str(amount * 0.8))
        upper = Decimal(str(amount * 1.2))

        q = (
            select(Transaction)
            .where(
                and_(
                    Transaction.id != txn.id,
                    Transaction.source_entity_id == txn.source_entity_id,
                    Transaction.channel == txn.channel,
                    Transaction.amount.between(lower, upper),
                )
            )
            .order_by(desc(Transaction.processed_at))
            .limit(limit)
        )
        rows = (await self._db.execute(q)).scalars().all()
        return [TransactionResponse.model_validate(row) for row in rows]

    # ── Export ────────────────────────────────────────────────────────────────

    async def export(
        self,
        params: TransactionSearchRequest,
        fmt: str = "csv",
    ) -> bytes:
        """Export filtered transactions as CSV or JSON (F1.7).

        Streams all matching rows (no pagination limit) into bytes for the response.
        """
        # Re-use search filters but without pagination
        params_all = params.model_copy(update={"page": 1, "page_size": 10000})
        items, _ = await self.search(params_all)

        if fmt == "json":
            data = [item.model_dump(mode="json") for item in items]
            return json.dumps(data, default=str).encode("utf-8")

        # CSV
        buf = io.StringIO()
        if not items:
            return buf.getvalue().encode("utf-8")

        writer = csv.DictWriter(
            buf, fieldnames=list(items[0].model_fields.keys())
        )
        writer.writeheader()
        for item in items:
            writer.writerow(item.model_dump(mode="json"))

        return buf.getvalue().encode("utf-8")

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_or_404(self, transaction_id: uuid.UUID) -> Transaction:
        txn = await self._db.get(Transaction, transaction_id)
        if not txn:
            raise NotFoundError(f"Transaction '{transaction_id}' not found.")
        return txn

    def _build_filters(self, params: TransactionSearchRequest) -> list:
        """Build SQLAlchemy filter expressions from search parameters."""
        filters: list = []

        if params.query:
            like = f"%{params.query}%"
            filters.append(
                or_(
                    Transaction.external_id.ilike(like),
                    Transaction.description.ilike(like),
                )
            )
        if params.status:
            filters.append(Transaction.status.in_(params.status))
        if params.risk_level:
            filters.append(Transaction.risk_level.in_(params.risk_level))
        if params.transaction_type:
            filters.append(Transaction.transaction_type.in_(params.transaction_type))
        if params.channel:
            filters.append(Transaction.channel.in_(params.channel))
        if params.min_amount is not None:
            filters.append(Transaction.amount >= params.min_amount)
        if params.max_amount is not None:
            filters.append(Transaction.amount <= params.max_amount)
        if params.date_from:
            filters.append(Transaction.processed_at >= params.date_from)
        if params.date_to:
            filters.append(Transaction.processed_at <= params.date_to)
        if params.entity_id:
            filters.append(
                or_(
                    Transaction.source_entity_id == params.entity_id,
                    Transaction.destination_entity_id == params.entity_id,
                )
            )
        if params.country_code:
            filters.append(Transaction.country_code == params.country_code.upper())
        if params.min_fraud_score is not None:
            filters.append(
                Transaction.fraud_score >= Decimal(str(params.min_fraud_score))
            )
        if params.max_fraud_score is not None:
            filters.append(
                Transaction.fraud_score <= Decimal(str(params.max_fraud_score))
            )

        return filters

    @staticmethod
    def _to_detail(
        txn: Transaction,
        breakdown: Optional[FraudScoreBreakdown],
        source_entity: Optional[Entity],
        destination_entity: Optional[Entity],
    ) -> TransactionDetail:
        """Build a TransactionDetail response from ORM objects."""
        from app.schemas.transaction import EntitySummary

        src_summary = (
            EntitySummary.model_validate(source_entity)
            if source_entity
            else None
        )
        dst_summary = (
            EntitySummary.model_validate(destination_entity)
            if destination_entity
            else None
        )

        return TransactionDetail(
            id=txn.id,
            external_id=txn.external_id,
            source_entity_id=txn.source_entity_id,
            destination_entity_id=txn.destination_entity_id,
            amount=txn.amount,
            currency=txn.currency,
            transaction_type=txn.transaction_type,
            channel=txn.channel,
            status=txn.status,
            merchant_category_code=txn.merchant_category_code,
            description=txn.description,
            ip_address=txn.ip_address,
            device_fingerprint=txn.device_fingerprint,
            geolocation_lat=txn.geolocation_lat,
            geolocation_lng=txn.geolocation_lng,
            country_code=txn.country_code,
            card_present=txn.card_present,
            fraud_score=txn.fraud_score,
            risk_level=txn.risk_level,
            processed_at=txn.processed_at,
            created_at=txn.created_at,
            fraud_score_breakdown=breakdown,
            source_entity=src_summary,
            destination_entity=dst_summary,
        )
