"""Transaction endpoints — ingest, score, list, detail, OTP pre-block, CSV upload."""

import csv
import io
import random
import string
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.dependencies import CurrentUser, AnalystUser
from app.services.fraud_detection_service import score_transaction
from app.streaming.websocket_manager import ws_manager
from app.config import get_settings
import uuid

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# In-memory OTP store (keyed by transaction_id → {"otp": "123456", "expires": timestamp})
# For production: use Redis with TTL.
# ---------------------------------------------------------------------------
_OTP_STORE: dict[str, dict] = {}

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ---------------------------------------------------------------------------
# NOTE: Static-path routes (/test, /upload) MUST be declared before the
# parameterised route (/{transaction_id}) so FastAPI matches them first.
# ---------------------------------------------------------------------------


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
        import traceback
        import logging

        logging.getLogger(__name__).error(
            "Fraud scoring failed: %s\n%s", _score_err, traceback.format_exc()
        )

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


# ---------------------------------------------------------------------------
# Static-path routes before /{transaction_id} to avoid shadowing
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# POST /transactions/{id}/request-otp
# Blocks the transaction and sends an OTP to the customer (pre-settlement guard)
# ---------------------------------------------------------------------------


@router.post("/{transaction_id}/request-otp")
async def request_otp(
    transaction_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Block a flagged/suspicious transaction pending OTP verification.
    - Marks transaction status as 'blocked'
    - Generates a 6-digit OTP
    - Sends via SMS if Twilio configured; returns OTP in dev mode
    """
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

    # Block transaction pending verification
    txn.status = "blocked"
    txn.is_blocked = True
    await db.commit()

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    from datetime import timedelta

    _OTP_STORE[transaction_id] = {
        "otp": otp,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    # Resolve customer phone number from the Customer table
    customer_phone: str | None = None
    if txn.customer_id:
        from app.models.customer import Customer

        cust_result = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
        cust = cust_result.scalar_one_or_none()
        if cust:
            customer_phone = cust.phone_number

    # Try to send OTP via Twilio
    sms_sent = False
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and customer_phone:
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"FinShield OTP: {otp} — Use this to verify your ₹{float(txn.amount):,.0f} transaction. Valid 10 min.",
                from_=settings.TWILIO_FROM_NUMBER,
                to=customer_phone,
            )
            sms_sent = True
        except Exception as exc:
            logger.warning("Twilio SMS failed: %s", exc)

    response: dict = {
        "message": "Transaction blocked pending OTP verification",
        "transaction_id": transaction_id,
        "otp_sent": sms_sent,
        "expires_in_minutes": 10,
    }
    if settings.is_development and not sms_sent:
        response["dev_otp"] = otp
        response["dev_note"] = "Configure TWILIO_ACCOUNT_SID in .env to send real SMS"

    return response


# ---------------------------------------------------------------------------
# POST /transactions/{id}/verify-otp
# ---------------------------------------------------------------------------


@router.post("/{transaction_id}/verify-otp")
async def verify_otp(
    transaction_id: str,
    otp: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP and unblock the transaction if correct.
    Returns blocked status if OTP is wrong or expired.
    """
    from app.core.exceptions import NotFoundException, UnauthorizedException

    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.tenant_id == current_user.tenant_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise NotFoundException("Transaction")

    entry = _OTP_STORE.get(transaction_id)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP found. Request a new one.")

    if datetime.now(timezone.utc) > entry["expires"]:
        del _OTP_STORE[transaction_id]
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    if entry["otp"] != otp.strip():
        raise UnauthorizedException("Incorrect OTP")

    # Unblock — change status back to completed
    txn.status = "completed"
    txn.is_blocked = False
    await db.commit()
    del _OTP_STORE[transaction_id]

    return {"message": "OTP verified. Transaction approved.", "transaction_id": transaction_id}


# ---------------------------------------------------------------------------
# POST /transactions/upload — CSV batch ingestion
# ---------------------------------------------------------------------------


@router.post("/upload", status_code=201)
async def upload_transactions_csv(
    background_tasks: BackgroundTasks,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """
    Batch ingest transactions from a CSV file.

    Required CSV columns (unified schema):
      user_id (→ customer_id), transaction_id, amount, timestamp,
      location (city or lat,lng), device_id (→ device_fingerprint),
      merchant_id, merchant_name, channel, currency

    Optional columns: transaction_type, country_code, ip_address

    Returns: {ingested: N, skipped: N, errors: [...]}
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV has no headers")

    # Normalize column names (lowercase, strip spaces)
    fieldnames_norm = {f.strip().lower().replace(" ", "_"): f for f in reader.fieldnames}

    def get_col(row: dict, *keys: str, default="") -> str:
        """Try multiple column name variants."""
        for k in keys:
            if k in fieldnames_norm:
                v = row.get(fieldnames_norm[k], "").strip()
                if v:
                    return v
        return default

    ingested = 0
    skipped = 0
    errors: list[str] = []
    batch_txns: list[Transaction] = []

    for i, row in enumerate(reader, start=2):  # row 1 = headers
        try:
            amount_raw = get_col(row, "amount")
            if not amount_raw:
                skipped += 1
                continue

            amount = float(amount_raw.replace(",", "").replace("₹", "").strip())
            ts_raw = get_col(row, "timestamp", "transaction_timestamp", "date", "txn_date")
            try:
                ts = (
                    datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    if ts_raw
                    else datetime.now(timezone.utc)
                )
            except ValueError:
                ts = datetime.now(timezone.utc)

            # Parse location: "lat,lng" or just a city name
            location_str = get_col(row, "location", "location_lat", "city")
            lat, lng, city = None, None, None
            if "," in location_str:
                parts = location_str.split(",", 1)
                try:
                    lat, lng = float(parts[0].strip()), float(parts[1].strip())
                except ValueError:
                    city = location_str
            else:
                city = location_str or None

            txn = Transaction(
                id=get_col(row, "transaction_id", "txn_id", "id") or str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                customer_id=get_col(row, "user_id", "customer_id", "cust_id") or None,
                amount=amount,
                currency=get_col(row, "currency") or "INR",
                transaction_type=get_col(row, "transaction_type", "type") or "purchase",
                channel=get_col(row, "channel") or "online",
                merchant_id=get_col(row, "merchant_id") or None,
                merchant_name=get_col(row, "merchant_name", "merchant") or None,
                device_fingerprint=get_col(row, "device_id", "device_fingerprint") or None,
                location_lat=lat,
                location_lng=lng,
                city=city,
                country_code=get_col(row, "country_code", "country") or "IN",
                ip_address=get_col(row, "ip_address", "ip") or None,
                transaction_timestamp=ts,
                fraud_category="unscored",
                status="completed",
                is_test=False,
            )
            batch_txns.append(txn)
            ingested += 1

        except Exception as exc:
            errors.append(f"Row {i}: {exc}")
            skipped += 1

    # Bulk insert
    if batch_txns:
        for txn in batch_txns:
            db.add(txn)
        await db.commit()

        # Score all ingested transactions in background
        async def _score_all():
            for txn in batch_txns:
                try:
                    await score_transaction(txn, db)
                except Exception as exc:
                    logger.warning("Batch scoring failed for txn %s: %s", txn.id, exc)

        background_tasks.add_task(_score_all)

    return {
        "message": f"Processed {ingested + skipped} rows",
        "ingested": ingested,
        "skipped": skipped,
        "errors": errors[:20],  # cap error list to 20 items
    }
