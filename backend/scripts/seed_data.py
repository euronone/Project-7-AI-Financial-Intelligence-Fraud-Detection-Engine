"""Seed script — populates the database with realistic test data.

Generates:
  - 10 users  (2 admin, 4 analyst, 2 investigator, 2 viewer)
  - 100 entities (70 individuals, 20 businesses, 10 merchants)
  - 500 transactions spanning the last 90 days (~5 % fraud)
  - Default admin credentials: admin@finshield.local / Admin123!@#

Run from the backend/ directory:
    poetry run python scripts/seed_data.py
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── minimal inline settings so the script is self-contained ──────────────────
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://finshield:localdev123@localhost:5432/finshield",
)

# ── data helpers ─────────────────────────────────────────────────────────────

ENTITY_TYPES   = ["individual", "business", "merchant"]
RISK_LEVELS    = ["low", "medium", "high", "critical"]
KYC_STATUSES   = ["pending", "verified", "rejected", "expired"]
TX_TYPES       = ["payment", "transfer", "withdrawal", "deposit", "refund"]
TX_CHANNELS    = ["online", "pos", "atm", "mobile", "wire", "ach"]
TX_STATUSES    = ["pending", "completed", "failed", "reversed", "flagged", "blocked"]
COUNTRIES      = ["US", "GB", "DE", "FR", "CA", "AU", "SG", "JP", "BR", "IN", "RU", "NG"]
FIRST_NAMES    = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank",
                  "Iris", "Jack", "Karen", "Leo", "Mia", "Nate", "Olivia", "Paul"]
LAST_NAMES     = ["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson",
                  "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris"]
BIZ_NAMES      = ["Acme Corp", "GlobalTrade Ltd", "FastPay Inc", "NexGen Solutions",
                  "BlueSky Financial", "Apex Ventures", "Summit Logistics", "TechFlow GmbH"]
MERCHANT_NAMES = ["QuickShop", "PayEasy", "SwiftMart", "EasyStore", "FlexPay",
                  "ShopNow", "MegaMall", "TechZone"]

USER_ROLES = [
    ("admin@finshield.local",       "Admin",   "User",    "admin"),
    ("admin2@finshield.local",      "Admin",   "Two",     "admin"),
    ("analyst1@finshield.local",    "Anna",    "Analyst", "analyst"),
    ("analyst2@finshield.local",    "Ben",     "Analyst", "analyst"),
    ("analyst3@finshield.local",    "Clara",   "Analyst", "analyst"),
    ("analyst4@finshield.local",    "Dan",     "Analyst", "analyst"),
    ("investigator1@finshield.local","Ivan",   "Probe",   "investigator"),
    ("investigator2@finshield.local","Irene",  "Hunt",    "investigator"),
    ("viewer1@finshield.local",     "Victor",  "View",    "viewer"),
    ("viewer2@finshield.local",     "Vera",    "Look",    "viewer"),
]

# Bcrypt hash of "Admin123!@#"  (cost factor 12) — pre-computed to avoid bcrypt dep at seed time
DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGwiazAHe0N2JKFJhXsWXKIGe3i"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _rand_amount() -> float:
    """Most transactions are small; a few are large (mimics real distributions)."""
    if random.random() < 0.7:
        return round(random.uniform(5, 500), 2)
    elif random.random() < 0.9:
        return round(random.uniform(500, 5_000), 2)
    else:
        return round(random.uniform(5_000, 100_000), 2)


def _fraud_score(amount: float, country: str, channel: str) -> float:
    """Heuristic fraud score so seed data isn't all zeros."""
    score = random.uniform(0.0, 0.3)
    if amount > 10_000:
        score += random.uniform(0.1, 0.3)
    if country in ("RU", "NG"):
        score += random.uniform(0.1, 0.25)
    if channel == "wire":
        score += random.uniform(0.05, 0.15)
    return round(min(score, 1.0), 4)


def _risk_level(score: float) -> str:
    if score < 0.3:
        return "low"
    if score < 0.6:
        return "medium"
    if score < 0.8:
        return "high"
    return "critical"


def _tx_status(score: float, base_status: str) -> str:
    if score >= 0.8:
        return "blocked"
    if score >= 0.5:
        return "flagged"
    return base_status


# ── seed functions ────────────────────────────────────────────────────────────

async def seed_users(session: AsyncSession) -> None:
    print("  seeding users …")
    for email, first, last, role in USER_ROLES:
        uid = str(uuid.uuid4())
        await session.execute(text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active)
            VALUES (:id, :email, :pw, :first, :last, :role, true)
            ON CONFLICT (email) DO NOTHING
        """), {"id": uid, "email": email, "pw": DUMMY_HASH,
               "first": first, "last": last, "role": role})
    await session.commit()
    print(f"    OK {len(USER_ROLES)} users")


async def seed_entities(session: AsyncSession) -> int:
    print("  seeding entities …")
    count = 0
    for i in range(70):           # individuals
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        score = round(random.uniform(0.0, 0.6), 4)
        await session.execute(text("""
            INSERT INTO entities (id, external_id, entity_type, name, email, country_code,
                                  risk_score, risk_level, kyc_status)
            VALUES (:id, :ext, 'individual', :name, :email, :cc, :score, :rl, :kyc)
            ON CONFLICT (external_id) DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "ext": f"IND-{i+1:04d}", "name": name,
            "email": f"user{i+1}@example.com", "cc": random.choice(COUNTRIES),
            "score": score, "rl": _risk_level(score), "kyc": random.choice(KYC_STATUSES),
        })
        count += 1
    for i in range(20):           # businesses
        score = round(random.uniform(0.0, 0.4), 4)
        await session.execute(text("""
            INSERT INTO entities (id, external_id, entity_type, name, country_code,
                                  risk_score, risk_level, kyc_status)
            VALUES (:id, :ext, 'business', :name, :cc, :score, :rl, :kyc)
            ON CONFLICT (external_id) DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "ext": f"BIZ-{i+1:04d}",
            "name": random.choice(BIZ_NAMES) + f" {i+1}",
            "cc": random.choice(COUNTRIES), "score": score,
            "rl": _risk_level(score), "kyc": random.choice(KYC_STATUSES),
        })
        count += 1
    for i in range(10):           # merchants
        score = round(random.uniform(0.0, 0.3), 4)
        await session.execute(text("""
            INSERT INTO entities (id, external_id, entity_type, name, country_code,
                                  risk_score, risk_level, kyc_status)
            VALUES (:id, :ext, 'merchant', :name, :cc, :score, :rl, :kyc)
            ON CONFLICT (external_id) DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "ext": f"MER-{i+1:04d}",
            "name": random.choice(MERCHANT_NAMES) + f" {i+1}",
            "cc": random.choice(COUNTRIES), "score": score,
            "rl": _risk_level(score), "kyc": "verified",
        })
        count += 1
    await session.commit()
    print(f"    OK {count} entities")
    return count


async def seed_transactions(session: AsyncSession, entity_ids: list[str]) -> None:
    print("  seeding transactions …")
    count = 0
    now = _now()
    for i in range(500):
        src = random.choice(entity_ids)
        dst = random.choice(entity_ids)
        while dst == src:
            dst = random.choice(entity_ids)
        amount   = _rand_amount()
        currency = random.choice(["USD", "EUR", "GBP", "JPY", "CAD"])
        channel  = random.choice(TX_CHANNELS)
        country  = random.choice(COUNTRIES)
        score    = _fraud_score(amount, country, channel)
        rl       = _risk_level(score)
        base_st  = random.choice(["completed", "completed", "completed", "pending", "failed"])
        status   = _tx_status(score, base_st)
        days_ago = random.randint(0, 89)
        proc_at  = now - timedelta(days=days_ago, hours=random.randint(0, 23),
                                   minutes=random.randint(0, 59))

        await session.execute(text("""
            INSERT INTO transactions (
                id, external_id, source_entity_id, destination_entity_id,
                amount, currency, transaction_type, channel, status,
                country_code, fraud_score, risk_level, processed_at
            ) VALUES (
                :id, :ext, :src, :dst,
                :amount, :currency, :ttype, :channel, :status,
                :cc, :score, :rl, :proc_at
            )
        """), {
            "id": str(uuid.uuid4()), "ext": f"TXN-{i+1:06d}",
            "src": src, "dst": dst,
            "amount": amount, "currency": currency,
            "ttype": random.choice(TX_TYPES), "channel": channel,
            "status": status, "cc": country,
            "score": score, "rl": rl, "proc_at": proc_at,
        })
        count += 1
        if count % 100 == 0:
            await session.commit()
            print(f"    … {count}/500")

    await session.commit()
    print(f"    OK {count} transactions")


async def main() -> None:
    print("FinShield AI — seed data\n")
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        # Check whether users table exists (migrations must run first)
        result = await session.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'entities')"
        ))
        if not result.scalar():
            print("ERROR: Run 'alembic upgrade head' before seeding.")
            return

        # Seed users (requires users table — skip gracefully if not yet created)
        try:
            await seed_users(session)
        except Exception as e:
            print(f"  [SKIP] users table not found, skipping ({e.__class__.__name__})")
            await session.rollback()

        # Seed entities
        await seed_entities(session)

        # Collect entity IDs for FK references
        rows = await session.execute(text("SELECT id FROM entities"))
        entity_ids = [str(r[0]) for r in rows.fetchall()]

        # Seed transactions
        await seed_transactions(session, entity_ids)

    await engine.dispose()
    print("\nSeeding complete!")
    print("  Admin login: admin@finshield.local / Admin123!@#")


if __name__ == "__main__":
    asyncio.run(main())
