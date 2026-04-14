"""
Seed service — generates realistic synthetic customers and transactions
for a brand-new tenant so their dashboard is populated immediately.

Called by POST /settings/initialize (idempotent — only runs when the
tenant has zero transaction records).
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static name / city data (Indian locale, no external deps)
# ---------------------------------------------------------------------------

_FIRST_NAMES = [
    "Aarav",
    "Arjun",
    "Rohan",
    "Vikram",
    "Kiran",
    "Suresh",
    "Rahul",
    "Amit",
    "Deepak",
    "Rajesh",
    "Sanjay",
    "Manish",
    "Nikhil",
    "Vishal",
    "Kartik",
    "Priya",
    "Divya",
    "Ananya",
    "Sneha",
    "Pooja",
    "Kavya",
    "Meera",
    "Ritu",
    "Shreya",
    "Nisha",
    "Lakshmi",
    "Geeta",
    "Sunita",
    "Rekha",
    "Anjali",
    "Mohammed",
    "Arun",
    "Sunil",
    "Prakash",
    "Ravi",
    "Gopal",
    "Mohan",
    "Venkat",
    "Srikanth",
    "Ramesh",
    "Ganesh",
    "Mahesh",
    "Dinesh",
    "Harish",
    "Naveen",
    "Sridhar",
    "Balaji",
    "Vijay",
    "Anil",
    "Ashok",
    "Pankaj",
    "Yogesh",
    "Rakesh",
    "Sudhir",
    "Ajay",
    "Vijayalakshmi",
    "Chandra",
    "Pallavi",
    "Archana",
    "Usha",
    "Radha",
    "Saritha",
    "Vidya",
    "Smitha",
]

_LAST_NAMES = [
    "Sharma",
    "Gupta",
    "Singh",
    "Kumar",
    "Verma",
    "Patel",
    "Shah",
    "Mehta",
    "Joshi",
    "Rao",
    "Reddy",
    "Nair",
    "Iyer",
    "Pillai",
    "Menon",
    "Agarwal",
    "Srivastava",
    "Mishra",
    "Tiwari",
    "Pandey",
    "Yadav",
    "Chauhan",
    "Jain",
    "Bose",
    "Das",
    "Mukherjee",
    "Chatterjee",
    "Banerjee",
    "Ghosh",
    "Sen",
    "Kapoor",
    "Malhotra",
    "Khanna",
    "Chopra",
    "Arora",
    "Sethi",
    "Bajaj",
    "Desai",
    "Chaudhary",
    "Saxena",
    "Soni",
    "Bhatt",
    "Naik",
    "Kulkarni",
    "Deshpande",
    "Joshi",
    "More",
    "Patil",
    "Shinde",
    "Pawar",
]

_CITIES = [
    ("Mumbai", "Maharashtra", "400001", 19.076, 72.878),
    ("Delhi", "Delhi", "110001", 28.613, 77.209),
    ("Bangalore", "Karnataka", "560001", 12.972, 77.594),
    ("Hyderabad", "Telangana", "500001", 17.385, 78.487),
    ("Chennai", "Tamil Nadu", "600001", 13.083, 80.270),
    ("Kolkata", "West Bengal", "700001", 22.573, 88.364),
    ("Pune", "Maharashtra", "411001", 18.520, 73.857),
    ("Ahmedabad", "Gujarat", "380001", 23.022, 72.571),
    ("Jaipur", "Rajasthan", "302001", 26.913, 75.787),
    ("Lucknow", "Uttar Pradesh", "226001", 26.847, 80.947),
    ("Surat", "Gujarat", "395001", 21.170, 72.831),
    ("Kochi", "Kerala", "682001", 9.939, 76.270),
    ("Chandigarh", "Punjab", "160001", 30.734, 76.779),
    ("Nagpur", "Maharashtra", "440001", 21.146, 79.089),
    ("Indore", "Madhya Pradesh", "452001", 22.719, 75.857),
]

_MERCHANTS = [
    ("Swiggy", "5812", "online", "food"),
    ("Zomato", "5812", "online", "food"),
    ("Amazon", "5999", "online", "shopping"),
    ("Flipkart", "5999", "online", "shopping"),
    ("Myntra", "5691", "online", "shopping"),
    ("Reliance Fresh", "5411", "pos_physical", "grocery"),
    ("BigBazaar", "5411", "pos_physical", "grocery"),
    ("Dmart", "5411", "pos_physical", "grocery"),
    ("HPCL Pump", "5541", "pos_physical", "fuel"),
    ("BPCL Pump", "5541", "pos_physical", "fuel"),
    ("PVR Cinemas", "7832", "pos_physical", "entertainment"),
    ("BookMyShow", "7832", "online", "entertainment"),
    ("MakeMyTrip", "4722", "online", "travel"),
    ("Irctc", "4112", "online", "travel"),
    ("Apollo Pharmacy", "5912", "pos_physical", "healthcare"),
    ("Practo", "8099", "online", "healthcare"),
    ("Starbucks", "5812", "pos_physical", "food"),
    ("McDonalds", "5812", "pos_physical", "food"),
    ("Urban Company", "7389", "online", "services"),
    ("ATM Withdrawal", "6011", "atm", "atm"),
]


# ---------------------------------------------------------------------------
# Customer profile types
# ---------------------------------------------------------------------------

_PROFILES = [
    # (type_name, count, avg_balance, avg_spend, risk_base, tier, kyc)
    ("standard_salaried", 40, 145_000, 25_000, 0.08, "standard", "verified"),
    ("high_net_worth", 15, 850_000, 200_000, 0.05, "vip", "verified"),
    ("student", 15, 12_000, 8_000, 0.15, "standard", "basic"),
    ("small_business", 15, 320_000, 75_000, 0.12, "premium", "verified"),
    ("senior_citizen", 10, 90_000, 15_000, 0.20, "standard", "verified"),
    ("compromised", 5, 55_000, 30_000, 0.75, "standard", "verified"),
]

# ---------------------------------------------------------------------------
# Fraud patterns (used for injecting fraudulent transactions)
# ---------------------------------------------------------------------------

_FRAUD_PATTERNS = [
    "card_not_present_fraud",  # 80
    "account_takeover",  # 60
    "impossible_travel",  # 50
    "velocity_fraud",  # 40
    "identity_theft",  # 40
    "money_mule",  # 30
]

_FRAUD_PATTERN_WEIGHTS = [80, 60, 50, 40, 40, 30]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def seed_tenant_sample_data(
    *,
    db: AsyncSession,
    tenant_id: str,
    n_customers: int = 100,
    n_transactions: int = 10_000,
    fraud_rate: float = 0.03,
    rng_seed: int = 42,
) -> dict:
    """
    Generate *n_customers* sample customers and *n_transactions* synthetic
    transactions for *tenant_id* and bulk-insert them.

    Returns ``{"customers_created": N, "transactions_created": N}``.
    """
    from app.models.customer import Customer
    from app.models.transaction import Transaction

    rng = random.Random(rng_seed)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=90)

    # ── 1. Build customers ───────────────────────────────────────────────────
    customers: list[Customer] = []
    cust_city_map: dict[str, tuple] = {}  # customer_id → city tuple

    for profile_type, count, avg_bal, _avg_spend, risk_base, tier, kyc in _PROFILES:
        actual = round(count * (n_customers / 100))
        for _ in range(actual):
            cid = str(uuid.uuid4())
            first = rng.choice(_FIRST_NAMES)
            last = rng.choice(_LAST_NAMES)
            city_row = rng.choice(_CITIES)
            city, state, postal, _lat, _lng = city_row

            bal = rng.gauss(avg_bal, avg_bal * 0.3)
            bal = max(500.0, bal)

            dob_year = rng.randint(1960, 2004)
            open_days_ago = rng.randint(30, 3000)

            c = Customer(
                id=cid,
                tenant_id=tenant_id,
                full_name=f"{first} {last}",
                email=f"{first.lower()}.{last.lower()}{rng.randint(1, 999)}@example.com",
                phone_number=f"+91{rng.randint(7000000000, 9999999999)}",
                date_of_birth=date(dob_year, rng.randint(1, 12), rng.randint(1, 28)),
                city=city,
                state_province=state,
                postal_code=postal,
                country_code="IN",
                account_type="personal" if tier != "vip" else "business",
                account_opening_date=date.today() - timedelta(days=open_days_ago),
                account_status="active",
                kyc_status=kyc,
                kyc_verification_level="enhanced" if tier == "vip" else "basic",
                risk_score=round(min(1.0, max(0.0, rng.gauss(risk_base, 0.05))), 4),
                customer_tier=tier,
                balance_amount=round(bal, 2),
                active_card_count=rng.randint(1, 3),
                preferred_card_token=f"tok_{uuid.uuid4().hex[:12].upper()}",
            )
            customers.append(c)
            cust_city_map[cid] = city_row

    # Pad to exactly n_customers if rounding left us short
    while len(customers) < n_customers:
        cid = str(uuid.uuid4())
        city_row = rng.choice(_CITIES)
        city, state, postal, _lat, _lng = city_row
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        c = Customer(
            id=cid,
            tenant_id=tenant_id,
            full_name=f"{first} {last}",
            email=f"{first.lower()}.{last.lower()}{rng.randint(1,999)}@example.com",
            phone_number=f"+91{rng.randint(7000000000, 9999999999)}",
            city=city,
            state_province=state,
            postal_code=postal,
            country_code="IN",
            account_type="personal",
            account_opening_date=date.today() - timedelta(days=rng.randint(60, 1000)),
            account_status="active",
            kyc_status="verified",
            kyc_verification_level="basic",
            risk_score=round(rng.uniform(0.05, 0.25), 4),
            customer_tier="standard",
            balance_amount=round(rng.uniform(5_000, 100_000), 2),
            active_card_count=1,
            preferred_card_token=f"tok_{uuid.uuid4().hex[:12].upper()}",
        )
        customers.append(c)
        cust_city_map[cid] = city_row

    db.add_all(customers)
    await db.flush()  # obtain PKs before FK-referencing transactions

    # ── 2. Build transactions ────────────────────────────────────────────────
    n_fraud = round(n_transactions * fraud_rate)
    n_legit = n_transactions - n_fraud

    transactions: list[Transaction] = []
    customer_ids = [c.id for c in customers]

    # ── 2a. Legitimate transactions ──────────────────────────────────────────
    for _ in range(n_legit):
        cid = rng.choice(customer_ids)
        city_row = cust_city_map[cid]
        _, _, _, lat, lng = city_row
        merchant = rng.choice(_MERCHANTS)
        m_name, mcc, channel, _cat = merchant

        ts = window_start + timedelta(
            seconds=rng.randint(0, int((now - window_start).total_seconds()))
        )

        # Use customer's home city coordinates with minor jitter
        jitter = 0.05
        txn_lat = lat + rng.uniform(-jitter, jitter)
        txn_lng = lng + rng.uniform(-jitter, jitter)

        amount = _realistic_amount(rng, channel, mcc)
        score = round(rng.uniform(0.0, 0.28), 4)

        t = Transaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=cid,
            merchant_name=m_name,
            merchant_category_code=mcc,
            amount=amount,
            currency="INR",
            transaction_type="withdrawal" if channel == "atm" else "purchase",
            channel=channel,
            location_lat=round(txn_lat, 6),
            location_lng=round(txn_lng, 6),
            country_code="IN",
            device_fingerprint=f"df_{uuid.uuid4().hex[:10]}",
            device_type=rng.choice(["mobile", "desktop", "mobile", "pos_terminal"]),
            status="completed",
            fraud_score=score,
            fraud_risk_level="low" if score < 0.3 else "medium",
            fraud_category="legitimate",
            is_flagged=False,
            is_blocked=False,
            is_test=False,
            model_version="seed_v1",
            triggered_rule_ids=[],
            transaction_timestamp=ts,
            created_at=ts,
        )
        transactions.append(t)

    # ── 2b. Fraudulent transactions ──────────────────────────────────────────
    fraud_targets = [c.id for c in customers if c.risk_score and c.risk_score > 0.3]
    if not fraud_targets:
        fraud_targets = customer_ids  # fallback

    for _ in range(n_fraud):
        pattern = rng.choices(_FRAUD_PATTERNS, weights=_FRAUD_PATTERN_WEIGHTS, k=1)[0]
        cid = rng.choice(fraud_targets)
        city_row = cust_city_map.get(cid, rng.choice(_CITIES))
        _, _, _, lat, lng = city_row

        ts = window_start + timedelta(
            seconds=rng.randint(0, int((now - window_start).total_seconds()))
        )

        merchant = rng.choice(_MERCHANTS)
        m_name, mcc, channel, _cat = merchant
        amount = _fraud_amount(rng, pattern)
        score = round(rng.uniform(0.65, 0.99), 4)

        # Geographic anomaly for impossible travel / cross-border patterns
        if pattern in ("impossible_travel", "account_takeover"):
            # Put transaction 1,500–3,000 km away
            txn_lat = lat + rng.uniform(8, 15) * rng.choice([-1, 1])
            txn_lng = lng + rng.uniform(8, 15) * rng.choice([-1, 1])
        else:
            txn_lat = lat + rng.uniform(-1, 1)
            txn_lng = lng + rng.uniform(-1, 1)

        is_blocked = score >= 0.80

        t = Transaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=cid,
            merchant_name=m_name,
            merchant_category_code=mcc,
            amount=amount,
            currency="INR",
            transaction_type="purchase",
            channel=channel,
            location_lat=round(txn_lat, 6),
            location_lng=round(txn_lng, 6),
            country_code="IN"
            if pattern not in ("impossible_travel",)
            else rng.choice(["US", "GB", "SG", "AE"]),
            device_fingerprint=f"df_fraud_{uuid.uuid4().hex[:8]}",
            device_type="mobile",
            status="blocked" if is_blocked else "flagged",
            fraud_score=score,
            fraud_risk_level="critical" if score >= 0.8 else "high",
            fraud_category="fraudulent",
            is_flagged=True,
            is_blocked=is_blocked,
            is_test=False,
            model_version="seed_v1",
            triggered_rule_ids=[pattern],
            transaction_timestamp=ts,
            created_at=ts,
        )
        transactions.append(t)

    # Shuffle so fraud is not all at the end
    rng.shuffle(transactions)

    db.add_all(transactions)
    await db.commit()

    logger.info(
        "Seeded tenant %s: %d customers, %d transactions (%d fraud)",
        tenant_id,
        len(customers),
        len(transactions),
        n_fraud,
    )
    return {
        "customers_created": len(customers),
        "transactions_created": len(transactions),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _realistic_amount(rng: random.Random, channel: str, mcc: str) -> float:
    """Return a realistic transaction amount for a legitimate transaction."""
    if channel == "atm":
        return float(rng.choice([2000, 3000, 5000, 10000]))
    if mcc == "5541":  # fuel
        return round(rng.uniform(800, 3000), 2)
    if mcc in ("4722", "4112"):  # travel
        return round(rng.uniform(3000, 25000), 2)
    if mcc == "5999":  # shopping
        return round(rng.uniform(500, 8000), 2)
    if mcc == "5411":  # grocery
        return round(rng.uniform(400, 4000), 2)
    # Default
    return round(rng.uniform(200, 3000), 2)


def _fraud_amount(rng: random.Random, pattern: str) -> float:
    """Return a suspicious amount matching the fraud pattern."""
    if pattern == "velocity_fraud":
        return round(rng.uniform(2000, 9500), 2)
    if pattern == "money_mule":
        return round(rng.choice([9_00_000, 7_50_000, 5_00_000]) + rng.uniform(-5000, 5000), 2)
    if pattern in ("impossible_travel", "account_takeover"):
        return round(rng.uniform(15_000, 80_000), 2)
    if pattern == "identity_theft":
        return round(rng.uniform(30_000, 1_00_000), 2)
    # card_not_present_fraud
    return round(rng.uniform(5_000, 50_000), 2)
