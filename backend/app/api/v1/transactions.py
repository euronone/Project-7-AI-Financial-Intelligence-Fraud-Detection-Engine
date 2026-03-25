"""Transaction endpoints — ingest, score, list, detail."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.dependencies import CurrentUser
from app.services.fraud_detection_service import score_transaction
from app.streaming.websocket_manager import ws_manager
import uuid

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a new transaction and trigger real-time fraud scoring."""
    txn = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        customer_id=body.customer_id,
        amount=body.amount,
        currency=body.currency,
        transaction_type=body.transaction_type,
        channel=body.channel,
        merchant_name=body.merchant_name,
        merchant_category_code=body.merchant_category_code,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        country_code=body.country_code,
        city=body.city,
        ip_address=body.ip_address,
        device_fingerprint=body.device_fingerprint,
        device_type=body.device_type,
        transaction_timestamp=body.transaction_timestamp or datetime.now(timezone.utc),
        is_test=body.is_test,
        fraud_category="unscored",
        status="completed",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    # Run fraud scoring inline (fast enough at ~50ms to not need a background queue)
    try:
        tenant_id = current_user.tenant_id

        async def _broadcast(payload: dict):
            await ws_manager.broadcast_to_tenant(tenant_id, payload)

        await score_transaction(txn, db, broadcast_fn=_broadcast)
        await db.refresh(txn)
    except Exception as _score_err:
        import traceback, logging
        logging.getLogger(__name__).error("Fraud scoring failed: %s\n%s", _score_err, traceback.format_exc())

    return txn


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    fraud_category: str | None = Query(None),
    is_flagged: bool | None = Query(None),
    is_test: bool | None = Query(None),
):
    """List transactions with optional filters."""
    query = select(Transaction).where(Transaction.tenant_id == current_user.tenant_id)

    if fraud_category:
        query = query.where(Transaction.fraud_category == fraud_category)
    if is_flagged is not None:
        query = query.where(Transaction.is_flagged == is_flagged)
    if is_test is not None:
        query = query.where(Transaction.is_test == is_test)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Transaction.transaction_timestamp.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return TransactionListResponse(items=list(items), total=total, page=page, per_page=per_page)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get a single transaction by ID."""
    from app.core.exceptions import NotFoundException
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.tenant_id == current_user.tenant_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise NotFoundException("Transaction")
    return txn


@router.post("/test", response_model=TransactionResponse, status_code=201)
async def test_transaction(
    body: TransactionCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Submit a test transaction (is_test=True) through the full fraud pipeline."""
    body.is_test = True
    return await create_transaction(body, background_tasks, current_user, db)
