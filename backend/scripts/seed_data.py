"""
FinShield AI — Seed Data Generator
====================================
Generates:
  - 100 synthetic customers (Indian locale, 6 risk profiles)
  - 10,000 transactions (90 days, 3% fraud rate, 6 fraud patterns)
  - Writes to SQLite DB + CSV files for ML training

Run:
    cd backend
    python scripts/seed_data.py

Outputs:
    data/samples/customers_100.csv
    data/samples/transactions_10000.csv
    data/samples/fraud_labels.csv
    Inserts into finshield_dev.db
"""

import asyncio
import csv
import math
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone, date

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)

# ── Config ────────────────────────────────────────────────────────────────────
NUM_CUSTOMERS    = 100
NUM_TRANSACTIONS = 10_000

# ── Card types with BIN prefixes ──────────────────────────────────────────────
CARD_TYPES = [
    {"network": "Visa",       "bin_prefix": "4", "weight": 0.40},
    {"network": "Mastercard", "bin_prefix": "5", "weight": 0.35},
    {"network": "RuPay",      "bin_prefix": "6", "weight": 0.20},
    {"network": "Amex",       "bin_prefix": "3", "weight": 0.05},
]

# ── 10 dedicated test customers with easy-to-remember card numbers ─────────────
# Used for manual fraud testing — card numbers are fully visible (not masked)
TEST_CUSTOMERS = [
    {
        "customer_id":   "test-cust-0001-0000-000000000001",
        "seq":           901,
        "full_name":     "Arjun Test Kumar",
        "email":         "test001@finshield.test",
        "phone_number":  "+919100000001",
        "profile_type":  "standard_salaried",
        "risk_score":    0.10,
        "balance_amount": 50000.00,
        "customer_tier": "standard",
        "card_number":   "4111111111111111",   # Visa — normal behavior
        "card_network":  "Visa",
        "card_cvv":      "111",
        "card_expiry":   "12/2030",
        "scenario":      "normal_purchase",
    },
    {
        "customer_id":   "test-cust-0002-0000-000000000002",
        "seq":           902,
        "full_name":     "Priya Test Sharma",
        "email":         "test002@finshield.test",
        "phone_number":  "+919100000002",
        "profile_type":  "high_net_worth",
        "risk_score":    0.05,
        "balance_amount": 500000.00,
        "customer_tier": "vip",
        "card_number":   "5222222222222222",   # Mastercard — high spender
        "card_network":  "Mastercard",
        "card_cvv":      "222",
        "card_expiry":   "12/2030",
        "scenario":      "high_value_normal",
    },
    {
        "customer_id":   "test-cust-0003-0000-000000000003",
        "seq":           903,
        "full_name":     "Rohit Test Verma",
        "email":         "test003@finshield.test",
        "phone_number":  "+919100000003",
        "profile_type":  "student",
        "risk_score":    0.20,
        "balance_amount": 8000.00,
        "customer_tier": "standard",
        "card_number":   "6333333333333333",   # RuPay — student
        "card_network":  "RuPay",
        "card_cvv":      "333",
        "card_expiry":   "12/2030",
        "scenario":      "student_normal",
    },
    {
        "customer_id":   "test-cust-0004-0000-000000000004",
        "seq":           904,
        "full_name":     "Meena Test Iyer",
        "email":         "test004@finshield.test",
        "phone_number":  "+919100000004",
        "profile_type":  "senior_citizen",
        "risk_score":    0.40,
        "balance_amount": 120000.00,
        "customer_tier": "standard",
        "card_number":   "4444444444444444",   # Visa — senior citizen
        "card_network":  "Visa",
        "card_cvv":      "444",
        "card_expiry":   "12/2030",
        "scenario":      "senior_normal",
    },
    {
        "customer_id":   "test-cust-0005-0000-000000000005",
        "seq":           905,
        "full_name":     "Suresh Test Pillai",
        "email":         "test005@finshield.test",
        "phone_number":  "+919100000005",
        "profile_type":  "small_business",
        "risk_score":    0.15,
        "balance_amount": 200000.00,
        "customer_tier": "premium",
        "card_number":   "5555555555554444",   # Mastercard — business (standard test number)
        "card_network":  "Mastercard",
        "card_cvv":      "555",
        "card_expiry":   "12/2030",
        "scenario":      "business_normal",
    },
    {
        "customer_id":   "test-cust-0006-0000-000000000006",
        "seq":           906,
        "full_name":     "Kavita Test Nair",
        "email":         "test006@finshield.test",
        "phone_number":  "+919100000006",
        "profile_type":  "compromised",
        "risk_score":    0.90,
        "balance_amount": 30000.00,
        "customer_tier": "standard",
        "card_number":   "6666666666666666",   # RuPay — COMPROMISED card for fraud testing
        "card_network":  "RuPay",
        "card_cvv":      "666",
        "card_expiry":   "12/2030",
        "scenario":      "compromised_card",
    },
    {
        "customer_id":   "test-cust-0007-0000-000000000007",
        "seq":           907,
        "full_name":     "Vikram Test Menon",
        "email":         "test007@finshield.test",
        "phone_number":  "+919100000007",
        "profile_type":  "high_net_worth",
        "risk_score":    0.08,
        "balance_amount": 1000000.00,
        "customer_tier": "vip",
        "card_number":   "378277777777777",    # Amex (15 digits) — impossible travel test
        "card_network":  "Amex",
        "card_cvv":      "7777",
        "card_expiry":   "12/2030",
        "scenario":      "impossible_travel",
    },
    {
        "customer_id":   "test-cust-0008-0000-000000000008",
        "seq":           908,
        "full_name":     "Deepa Test Krishnan",
        "email":         "test008@finshield.test",
        "phone_number":  "+919100000008",
        "profile_type":  "standard_salaried",
        "risk_score":    0.12,
        "balance_amount": 75000.00,
        "customer_tier": "standard",
        "card_number":   "4888888888888888",   # Visa — velocity fraud test
        "card_network":  "Visa",
        "card_cvv":      "888",
        "card_expiry":   "12/2030",
        "scenario":      "velocity_fraud",
    },
    {
        "customer_id":   "test-cust-0009-0000-000000000009",
        "seq":           909,
        "full_name":     "Amit Test Desai",
        "email":         "test009@finshield.test",
        "phone_number":  "+919100000009",
        "profile_type":  "standard_salaried",
        "risk_score":    0.30,
        "balance_amount": 40000.00,
        "customer_tier": "standard",
        "card_number":   "5999999999999999",   # Mastercard — account takeover test
        "card_network":  "Mastercard",
        "card_cvv":      "999",
        "card_expiry":   "12/2030",
        "scenario":      "account_takeover",
    },
    {
        "customer_id":   "test-cust-0010-0000-000000000010",
        "seq":           910,
        "full_name":     "Neha Test Joshi",
        "email":         "test010@finshield.test",
        "phone_number":  "+919100000010",
        "profile_type":  "standard_salaried",
        "risk_score":    0.18,
        "balance_amount": 60000.00,
        "customer_tier": "standard",
        "card_number":   "4000000000000000",   # Visa — money mule / structuring test
        "card_network":  "Visa",
        "card_cvv":      "000",
        "card_expiry":   "12/2030",
        "scenario":      "money_mule",
    },
]
FRAUD_RATE       = 0.03          # 3% fraud = 300 fraudulent transactions
DAYS_HISTORY     = 90
OUTPUT_DIR       = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")
DB_URL           = "sqlite+aiosqlite:///./finshield_dev.db"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Customer profiles ─────────────────────────────────────────────────────────
CUSTOMER_PROFILES = [
    {"type": "standard_salaried", "count": 40, "avg_monthly":  25_000, "risk": "low",      "fraud_risk": 0.10},
    {"type": "high_net_worth",    "count": 15, "avg_monthly": 200_000, "risk": "low",      "fraud_risk": 0.05},
    {"type": "student",           "count": 15, "avg_monthly":   8_000, "risk": "medium",   "fraud_risk": 0.20},
    {"type": "small_business",    "count": 15, "avg_monthly":  75_000, "risk": "medium",   "fraud_risk": 0.15},
    {"type": "senior_citizen",    "count": 10, "avg_monthly":  15_000, "risk": "high",     "fraud_risk": 0.35},
    {"type": "compromised",       "count":  5, "avg_monthly":  30_000, "risk": "critical", "fraud_risk": 0.90},
]

# ── Fraud patterns ────────────────────────────────────────────────────────────
FRAUD_PATTERNS = {
    "card_not_present":  80,
    "account_takeover":  60,
    "impossible_travel": 50,
    "velocity_fraud":    40,
    "identity_theft":    40,
    "money_mule":        30,
}

# ── Transaction categories ────────────────────────────────────────────────────
TXN_CATEGORIES = [
    {"cat": "grocery",          "mcc": "5411", "weight": 0.25, "avg":   2_500, "channels": ["pos_physical", "online"]},
    {"cat": "restaurant",       "mcc": "5812", "weight": 0.15, "avg":     800, "channels": ["pos_physical"]},
    {"cat": "online_shopping",  "mcc": "5999", "weight": 0.20, "avg":   3_500, "channels": ["online"]},
    {"cat": "fuel",             "mcc": "5541", "weight": 0.10, "avg":   1_500, "channels": ["pos_physical"]},
    {"cat": "entertainment",    "mcc": "7832", "weight": 0.08, "avg":   1_200, "channels": ["online", "pos_physical"]},
    {"cat": "travel",           "mcc": "4111", "weight": 0.07, "avg":  15_000, "channels": ["online"]},
    {"cat": "healthcare",       "mcc": "8099", "weight": 0.05, "avg":   2_000, "channels": ["pos_physical"]},
    {"cat": "atm_withdrawal",   "mcc": "6011", "weight": 0.10, "avg":   5_000, "channels": ["atm"]},
]

# ── Indian cities with lat/lng ─────────────────────────────────────────────────
INDIAN_CITIES = [
    ("Mumbai",     19.0760,  72.8777),
    ("Delhi",      28.6139,  77.2090),
    ("Bengaluru",  12.9716,  77.5946),
    ("Hyderabad",  17.3850,  78.4867),
    ("Chennai",    13.0827,  80.2707),
    ("Kolkata",    22.5726,  88.3639),
    ("Pune",       18.5204,  73.8567),
    ("Ahmedabad",  23.0225,  72.5714),
    ("Jaipur",     26.9124,  75.7873),
    ("Surat",      21.1702,  72.8311),
    ("Lucknow",    26.8467,  80.9462),
    ("Chandigarh", 30.7333,  76.7794),
    ("Bhopal",     23.2599,  77.4126),
    ("Nagpur",     21.1458,  79.0882),
]

FOREIGN_CITIES = [
    ("Dubai",     25.2048,  55.2708),
    ("Singapore", 1.3521,  103.8198),
    ("London",    51.5074,  -0.1278),
    ("New York",  40.7128, -74.0060),
    ("Bangkok",   13.7563, 100.5018),
]

MERCHANTS = [
    "Amazon India", "Flipkart", "Swiggy", "Zomato", "BigBasket",
    "Reliance Fresh", "DMart", "Myntra", "Nykaa", "Paytm Mall",
    "MakeMyTrip", "IRCTC", "OLA", "Uber", "BookMyShow",
    "Apollo Pharmacy", "Medplus", "HPCL Petrol", "BPCL Pump",
    "McDonald's India", "KFC India", "Starbucks", "Pizza Hut",
    "Decathlon", "Croma", "Vijay Sales", "Apple Store India",
    "ATM Withdrawal", "NEFT Transfer", "UPI Payment",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def pick_city(foreign: bool = False):
    pool = FOREIGN_CITIES if foreign else INDIAN_CITIES
    return random.choice(pool)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def rand_amount(avg: float, spread: float = 0.6) -> float:
    lo = avg * (1 - spread)
    hi = avg * (1 + spread)
    return round(max(1, random.uniform(lo, hi)), 2)


def pick_category():
    weights = [c["weight"] for c in TXN_CATEGORIES]
    return random.choices(TXN_CATEGORIES, weights=weights, k=1)[0]


def build_test_customers() -> tuple[list[dict], list[dict]]:
    """Build 10 test customers with easy unmasked card numbers."""
    customers = []
    cards = []
    city, lat, lng = ("Mumbai", 19.0760, 72.8777)

    for t in TEST_CUSTOMERS:
        card_id  = f"test-card-{t['seq']}-0000-00000000{t['seq']:04d}"
        last4    = t["card_number"][-4:]
        # Full unmasked number — formatted with dashes for readability
        n = t["card_number"]
        if t["card_network"] == "Amex":
            card_display = f"{n[:4]}-{n[4:10]}-{n[10:]}"
        else:
            card_display = f"{n[:4]}-{n[4:8]}-{n[8:12]}-{n[12:]}"

        card_status = "compromised" if t["profile_type"] == "compromised" else "active"

        cards.append({
            "card_id":       card_id,
            "customer_id":   t["customer_id"],
            "card_network":  t["card_network"],
            "card_last4":    last4,
            "card_masked":   card_display,   # UNMASKED for test cards
            "card_number":   t["card_number"],
            "card_cvv":      t["card_cvv"],
            "card_expiry":   t["card_expiry"],
            "card_token":    f"tok_test_{t['seq']:03d}_{last4}",
            "card_status":   card_status,
            "is_primary":    True,
            "is_test_card":  True,
        })

        customers.append({
            "customer_id":          t["customer_id"],
            "seq":                  t["seq"],
            "full_name":            t["full_name"],
            "email":                t["email"],
            "phone_number":         t["phone_number"],
            "date_of_birth":        "1990-01-01",
            "city":                 city,
            "city_lat":             lat,
            "city_lng":             lng,
            "state_province":       "Maharashtra",
            "postal_code":          "400001",
            "country_code":         "IN",
            "account_type":         "business" if t["profile_type"] == "small_business" else "personal",
            "account_opening_date": "2020-01-01",
            "account_status":       "active",
            "kyc_status":           "verified",
            "kyc_level":            "enhanced" if t["profile_type"] == "high_net_worth" else "basic",
            "risk_score":           t["risk_score"],
            "customer_tier":        t["customer_tier"],
            "balance_amount":       t["balance_amount"],
            "active_card_count":    1,
            # ── Embedded primary card fields (full visible number for test cards) ─
            "card_number":          card_display,       # full unmasked for test customers
            "card_last4":           last4,
            "card_network":         t["card_network"],
            "card_cvv":             t["card_cvv"],
            "card_expiry":          t["card_expiry"],
            "card_status":          card_status,
            "card_token":           f"tok_test_{t['seq']:03d}_{last4}",
            "is_test_customer":     True,
            "test_scenario":        t["scenario"],
            "profile_type":         t["profile_type"],
            "fraud_risk":           0.90 if t["profile_type"] == "compromised" else 0.10,
            "_card_ids":            [card_id],
            "_cards":               [cards[-1]],
        })

    return customers, cards


def generate_cards_for_customer(customer_id: str, count: int, profile_type: str) -> list[dict]:
    """Generate 1–4 cards for a customer with realistic attributes."""
    cards = []
    # High net worth always gets an Amex as primary
    if profile_type == "high_net_worth":
        card_pool = [{"network": "Amex", "bin_prefix": "3"}] + \
                    random.choices(CARD_TYPES[:-1], weights=[0.5, 0.35, 0.15], k=count - 1)
    else:
        card_pool = random.choices(CARD_TYPES, weights=[c["weight"] for c in CARD_TYPES], k=count)

    for idx, ctype in enumerate(card_pool):
        last4     = f"{random.randint(1000, 9999)}"
        card_id   = str(uuid.uuid4())
        # Generate a realistic masked card number: XXXX-XXXX-XXXX-{last4}
        masked    = f"XXXX-XXXX-XXXX-{last4}"
        # Expiry: 1–5 years from now
        exp_year  = 2026 + random.randint(1, 5)
        exp_month = random.randint(1, 12)
        # Compromised profile: one card is blocked
        if profile_type == "compromised" and idx == 0:
            status = "compromised"
        else:
            status = "active"
        # CVV: 4 digits for Amex, 3 digits for others
        cvv_digits = 4 if ctype["network"] == "Amex" else 3
        cvv = f"{random.randint(10**(cvv_digits-1), 10**cvv_digits - 1)}"

        cards.append({
            "card_id":       card_id,
            "customer_id":   customer_id,
            "card_network":  ctype["network"],
            "card_last4":    last4,
            "card_masked":   masked,
            "card_token":    f"tok_{uuid.uuid4().hex[:16]}",
            "card_cvv":      cvv,
            "card_expiry":   f"{exp_month:02d}/{exp_year}",
            "card_status":   status,
            "is_primary":    idx == 0,
        })
    return cards


def pick_timestamp(base: datetime, day_offset_range: tuple) -> datetime:
    day = random.randint(*day_offset_range)
    hour = random.choices(range(24), weights=[
        1,1,1,1,2,3,5,8,9,10,10,9,8,9,10,10,9,8,7,6,5,4,3,2
    ], k=1)[0]
    minute = random.randint(0, 59)
    return base + timedelta(days=day, hours=hour, minutes=minute)


# ── Phase 1: Generate customers ───────────────────────────────────────────────

def generate_customers() -> tuple[list[dict], list[dict]]:
    customers = []
    all_cards = []
    cid = 0
    for profile in CUSTOMER_PROFILES:
        for _ in range(profile["count"]):
            cid += 1
            gender  = random.choice(["M", "F"])
            name    = fake.name_male() if gender == "M" else fake.name_female()
            city, lat, lng = pick_city()
            opening = date(
                random.randint(2015, 2023),
                random.randint(1, 12),
                random.randint(1, 28),
            )
            balance     = round(random.uniform(
                profile["avg_monthly"] * 0.5,
                profile["avg_monthly"] * 6
            ), 2)
            customer_id = str(uuid.uuid4())
            card_count  = random.randint(1, 4)
            cards       = generate_cards_for_customer(customer_id, card_count, profile["type"])
            primary     = cards[0]
            all_cards.extend(cards)

            customers.append({
                "customer_id":          customer_id,
                "seq":                  cid,
                "full_name":            name,
                "email":                f"cust{cid:03d}@{fake.domain_name()}",
                "phone_number":         f"+91{random.randint(7000000000, 9999999999)}",
                "date_of_birth":        str(date(random.randint(1960, 2002), random.randint(1,12), random.randint(1,28))),
                "city":                 city,
                "city_lat":             lat,
                "city_lng":             lng,
                "state_province":       fake.state(),
                "postal_code":          fake.postcode(),
                "country_code":         "IN",
                "account_type":         "business" if profile["type"] == "small_business" else "personal",
                "account_opening_date": str(opening),
                "account_status":       "active",
                "kyc_status":           "verified",
                "kyc_level":            "enhanced" if profile["type"] == "high_net_worth" else "basic",
                "risk_score":           round(random.uniform(0.0, 0.3) if profile["risk"] == "low"
                                        else random.uniform(0.3, 0.6) if profile["risk"] == "medium"
                                        else random.uniform(0.6, 0.95), 4),
                "customer_tier":        "vip" if profile["type"] == "high_net_worth"
                                        else "premium" if profile["type"] == "small_business"
                                        else "standard",
                "balance_amount":       balance,
                "active_card_count":    card_count,
                # ── Embedded primary card fields ───────────────────────────────
                "card_number":          primary["card_masked"],   # XXXX-XXXX-XXXX-{last4}
                "card_last4":           primary["card_last4"],
                "card_network":         primary["card_network"],
                "card_cvv":             primary["card_cvv"],
                "card_expiry":          primary["card_expiry"],
                "card_status":          primary["card_status"],
                "card_token":           primary["card_token"],
                "is_test_customer":     False,
                "test_scenario":        "",
                "profile_type":         profile["type"],
                "fraud_risk":           profile["fraud_risk"],
                # Internal only — not written to CSV
                "_card_ids":            [c["card_id"] for c in cards],
                "_cards":               cards,
            })
    random.shuffle(customers)
    return customers, all_cards


# ── Phase 2: Generate transactions ───────────────────────────────────────────

def generate_transactions(customers: list[dict], all_cards: list[dict]) -> tuple[list[dict], list[dict]]:
    base_date = datetime.now(timezone.utc) - timedelta(days=DAYS_HISTORY)
    transactions = []
    labels       = []

    # Pre-assign fraud transactions
    fraud_total = int(NUM_TRANSACTIONS * FRAUD_RATE)
    fraud_pool  = []
    for pattern, count in FRAUD_PATTERNS.items():
        fraud_pool.extend([pattern] * count)
    random.shuffle(fraud_pool)

    # Build a set of (txn_index, fraud_pattern) for fraud injection
    fraud_indices = set(random.sample(range(NUM_TRANSACTIONS), fraud_total))
    fraud_iter    = iter(fraud_pool)

    # Build card lookup: customer_id -> list of card_ids
    customer_cards: dict[str, list[str]] = {}
    for card in all_cards:
        customer_cards.setdefault(card["customer_id"], []).append(card["card_id"])

    # Maintain last txn per customer for velocity/travel checks
    customer_last: dict[str, dict] = {}

    for i in range(NUM_TRANSACTIONS):
        cust   = random.choice(customers)
        cat    = pick_category()
        ts     = pick_timestamp(base_date, (0, DAYS_HISTORY - 1))
        city, lat, lng = pick_city()
        amount = rand_amount(cat["avg"], 0.6)
        channel = random.choice(cat["channels"])
        merchant = random.choice(MERCHANTS)

        is_fraud   = i in fraud_indices
        pattern    = next(fraud_iter) if is_fraud else None
        fraud_risk = "legitimate"

        # ── Inject fraud patterns ─────────────────────────────────────────────
        if is_fraud:
            fraud_risk = "fraudulent"
            last = customer_last.get(cust["customer_id"])

            if pattern == "impossible_travel" and last:
                # Force a city very far from last txn, within 30 min
                for candidate in INDIAN_CITIES + FOREIGN_CITIES:
                    c_city, c_lat, c_lng = candidate
                    if haversine_km(last["lat"], last["lng"], c_lat, c_lng) > 900:
                        city, lat, lng = c_city, c_lat, c_lng
                        ts = last["ts"] + timedelta(minutes=random.randint(5, 25))
                        break

            elif pattern == "velocity_fraud":
                # Many small txns in a short window
                amount = rand_amount(500, 0.3)
                ts     = (last["ts"] + timedelta(minutes=random.randint(1, 8))) if last else ts

            elif pattern == "card_not_present":
                channel = "online"
                amount  = rand_amount(cat["avg"] * 3, 0.4)

            elif pattern == "account_takeover":
                ts      = ts.replace(hour=random.randint(1, 4))  # 1–4 AM
                amount  = rand_amount(cat["avg"] * 4, 0.3)
                city, lat, lng = pick_city(foreign=random.random() < 0.4)

            elif pattern == "identity_theft":
                amount  = rand_amount(cust["balance_amount"] * random.uniform(0.3, 0.7), 0.2)
                channel = "online"

            elif pattern == "money_mule":
                amount  = round(random.choice([9_50_000, 4_90_000, 7_50_000, 8_00_000]) * random.uniform(0.9, 1.1), 2)

        # Clamp timestamp to valid range
        ts = max(base_date, min(ts, datetime.now(timezone.utc)))

        txn_id = str(uuid.uuid4())
        txn = {
            "transaction_id":     txn_id,
            "customer_id":        cust["customer_id"],
            "card_last4":         cust.get("card_last4", "0000"),
            "card_network":       cust.get("card_network", "Visa"),
            "amount":             amount,
            "currency":           "INR",
            "transaction_type":   "purchase" if channel != "atm" else "withdrawal",
            "channel":            channel,
            "merchant_name":      merchant,
            "merchant_category_code": cat["mcc"],
            "location_lat":       lat,
            "location_lng":       lng,
            "city":               city,
            "country_code":       "IN" if city in [c[0] for c in INDIAN_CITIES] else "XX",
            "ip_address":         fake.ipv4(),
            "device_fingerprint": f"df_{uuid.uuid4().hex[:12]}",
            "device_type":        random.choice(["mobile", "desktop", "tablet", "mobile", "pos_terminal"]),
            "status":             "blocked" if is_fraud and pattern in ("impossible_travel", "account_takeover") else "completed",
            "fraud_score":        round(random.uniform(0.65, 0.99), 4) if is_fraud else round(random.uniform(0.01, 0.28), 4),
            "fraud_risk_level":   "critical" if is_fraud and pattern in ("impossible_travel","account_takeover","money_mule")
                                  else "high" if is_fraud
                                  else random.choice(["low", "low", "low", "medium"]),
            "fraud_category":     fraud_risk,
            "is_flagged":         is_fraud,
            "is_blocked":         is_fraud and pattern in ("impossible_travel", "account_takeover", "money_mule"),
            "is_test":            False,
            "model_version":      "ensemble_v1",
            "triggered_rule_ids": [pattern] if is_fraud else [],
            "fraud_scored_at":    ts.isoformat(),
            "transaction_timestamp": ts.isoformat(),
            "fraud_pattern":      pattern or "none",
        }
        transactions.append(txn)

        # Track last txn per customer
        customer_last[cust["customer_id"]] = {
            "ts": ts, "lat": lat, "lng": lng, "amount": amount
        }

        label = {
            "transaction_id": txn_id,
            "customer_id":    cust["customer_id"],
            "is_fraud":       1 if is_fraud else 0,
            "fraud_pattern":  pattern or "none",
            "fraud_category": fraud_risk,
            "fraud_score":    txn["fraud_score"],
        }
        labels.append(label)

    # Sort by timestamp
    transactions.sort(key=lambda t: t["transaction_timestamp"])
    return transactions, labels


# ── Phase 3: Write CSVs ───────────────────────────────────────────────────────

def write_csv(rows: list[dict], filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows -> {path}")


# ── Phase 4: Insert into SQLite DB ───────────────────────────────────────────

async def insert_to_db(customers: list[dict], transactions: list[dict], tenant_id: str):
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Insert customers
        for c in customers:
            await session.execute(text("""
                INSERT OR IGNORE INTO customers
                  (id, tenant_id, full_name, email, phone_number,
                   city, state_province, postal_code, country_code,
                   account_type, account_status, kyc_status, kyc_verification_level,
                   risk_score, customer_tier, balance_amount, active_card_count,
                   preferred_card_token, created_at, updated_at)
                VALUES
                  (:id, :tenant_id, :full_name, :email, :phone_number,
                   :city, :state, :postal, :country,
                   :account_type, 'active', :kyc, :kyc_level,
                   :risk, :tier, :balance, :cards,
                   :token, :now, :now)
            """), {
                "id":           c["customer_id"],
                "tenant_id":    tenant_id,
                "full_name":    c["full_name"],
                "email":        c["email"],
                "phone_number": c["phone_number"],
                "city":         c["city"],
                "state":        c["state_province"],
                "postal":       c["postal_code"],
                "country":      c["country_code"],
                "account_type": c["account_type"],
                "kyc":          c["kyc_status"],
                "kyc_level":    c["kyc_level"],
                "risk":         c["risk_score"],
                "tier":         c["customer_tier"],
                "balance":      c["balance_amount"],
                "cards":        c["active_card_count"],
                "token":        c.get("card_token", ""),
                "now":          datetime.now(timezone.utc).isoformat(),
            })

        await session.commit()
        print(f"  Inserted {len(customers)} customers into DB")

        # Insert transactions in batches of 500
        batch_size = 500
        inserted = 0
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i+batch_size]
            for t in batch:
                await session.execute(text("""
                    INSERT OR IGNORE INTO transactions
                      (id, tenant_id, customer_id, merchant_name, merchant_category_code,
                       amount, currency, transaction_type, channel,
                       location_lat, location_lng, city, country_code,
                       ip_address, device_fingerprint, device_type, status,
                       fraud_score, fraud_risk_level, fraud_category,
                       is_flagged, is_blocked, is_test, model_version,
                       triggered_rule_ids, fraud_scored_at,
                       transaction_timestamp, created_at)
                    VALUES
                      (:id, :tenant_id, :customer_id, :merchant, :mcc,
                       :amount, :currency, :txn_type, :channel,
                       :lat, :lng, :city, :country,
                       :ip, :device_fp, :device_type, :status,
                       :fraud_score, :fraud_risk, :fraud_cat,
                       :is_flagged, :is_blocked, 0, :model_version,
                       :rules, :scored_at,
                       :ts, :now)
                """), {
                    "id":           t["transaction_id"],
                    "tenant_id":    tenant_id,
                    "customer_id":  t["customer_id"],
                    "merchant":     t["merchant_name"],
                    "mcc":          t["merchant_category_code"],
                    "amount":       t["amount"],
                    "currency":     t["currency"],
                    "txn_type":     t["transaction_type"],
                    "channel":      t["channel"],
                    "lat":          t["location_lat"],
                    "lng":          t["location_lng"],
                    "city":         t["city"],
                    "country":      t["country_code"],
                    "ip":           t["ip_address"],
                    "device_fp":    t["device_fingerprint"],
                    "device_type":  t["device_type"],
                    "status":       t["status"],
                    "fraud_score":  t["fraud_score"],
                    "fraud_risk":   t["fraud_risk_level"],
                    "fraud_cat":    t["fraud_category"],
                    "is_flagged":   1 if t["is_flagged"] else 0,
                    "is_blocked":   1 if t["is_blocked"] else 0,
                    "model_version": t["model_version"],
                    "rules":        str(t["triggered_rule_ids"]),
                    "scored_at":    t["fraud_scored_at"],
                    "ts":           t["transaction_timestamp"],
                    "now":          datetime.now(timezone.utc).isoformat(),
                })
            await session.commit()
            inserted += len(batch)
            print(f"  Inserted transactions: {inserted:,}/{len(transactions):,}", end="\r")

        print(f"\n  Inserted {len(transactions):,} transactions into DB")

    await engine.dispose()


# ── Phase 4b: Generate & insert payment methods ───────────────────────────────

UPI_PROVIDERS_SEED = [
    ("gpay",    "@okicici"),
    ("phonepe", "@ybl"),
    ("paytm",   "@paytm"),
    ("sbi",     "@oksbi"),
    ("axis",    "@axisbank"),
    ("hdfc",    "@hdfcbank"),
    ("airtel",  "@airtel"),
]

CARD_BANKS_SEED = [
    "HDFC Bank", "SBI", "ICICI Bank", "Axis Bank", "Kotak Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank",
    "IndusInd Bank", "Yes Bank",
]


def generate_payment_methods_for_customer(customer_id: str, profile_type: str, phone_number: str) -> list[dict]:
    """Return 1-3 payment methods (UPI + credit/debit) for a customer."""
    methods = []
    # Derive phone last-10 digits for UPI VPA
    digits = "".join(c for c in phone_number if c.isdigit())[-10:]

    # 80% chance of having UPI
    if random.random() < 0.80:
        provider, suffix = random.choice(UPI_PROVIDERS_SEED)
        vpa = f"{digits}{suffix}"
        methods.append({
            "id":           str(uuid.uuid4()),
            "customer_id":  customer_id,
            "payment_type": "upi",
            "upi_vpa":      vpa,
            "upi_provider": provider,
            "card_last4":   None,
            "card_network": None,
            "card_expiry_month": None,
            "card_expiry_year":  None,
            "card_bank_name":    None,
            "is_primary":   len(methods) == 0,
        })

    # 70% chance of a credit card
    if random.random() < 0.70:
        net   = random.choices(["visa", "mastercard", "rupay", "amex"], weights=[0.40,0.35,0.20,0.05])[0]
        last4 = str(random.randint(1000, 9999))
        exp_m = random.randint(1, 12)
        exp_y = 2026 + random.randint(1, 5)
        methods.append({
            "id":           str(uuid.uuid4()),
            "customer_id":  customer_id,
            "payment_type": "credit_card",
            "upi_vpa":      None,
            "upi_provider": None,
            "card_last4":   last4,
            "card_network": net,
            "card_expiry_month": exp_m,
            "card_expiry_year":  exp_y,
            "card_bank_name":    random.choice(CARD_BANKS_SEED),
            "is_primary":   len(methods) == 0,
        })

    # 60% chance of a debit card
    if random.random() < 0.60:
        net   = random.choices(["visa", "mastercard", "rupay"], weights=[0.35, 0.30, 0.35])[0]
        last4 = str(random.randint(1000, 9999))
        exp_m = random.randint(1, 12)
        exp_y = 2025 + random.randint(1, 4)
        methods.append({
            "id":           str(uuid.uuid4()),
            "customer_id":  customer_id,
            "payment_type": "debit_card",
            "upi_vpa":      None,
            "upi_provider": None,
            "card_last4":   last4,
            "card_network": net,
            "card_expiry_month": exp_m,
            "card_expiry_year":  exp_y,
            "card_bank_name":    random.choice(CARD_BANKS_SEED),
            "is_primary":   len(methods) == 0,
        })

    # Ensure at least one method exists
    if not methods:
        digits_fallback = digits if digits else "9876543210"
        methods.append({
            "id":           str(uuid.uuid4()),
            "customer_id":  customer_id,
            "payment_type": "upi",
            "upi_vpa":      f"{digits_fallback}@oksbi",
            "upi_provider": "sbi",
            "card_last4":   None, "card_network": None,
            "card_expiry_month": None, "card_expiry_year": None,
            "card_bank_name": None,
            "is_primary":   True,
        })

    return methods


async def insert_payment_methods(customers: list[dict], tenant_id: str):
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Ensure table exists (it's created by SQLAlchemy metadata on startup,
        # but seed script runs standalone so we create it explicitly here)
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS customer_payment_methods (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                upi_vpa TEXT,
                upi_provider TEXT,
                card_last4 TEXT,
                card_network TEXT,
                card_expiry_month INTEGER,
                card_expiry_year INTEGER,
                card_bank_name TEXT,
                is_primary INTEGER DEFAULT 0,
                created_at TEXT
            )
        """))

        total_pm = 0
        for c in customers:
            methods = generate_payment_methods_for_customer(
                c["customer_id"], c["profile_type"], c.get("phone_number", "")
            )
            for m in methods:
                await session.execute(text("""
                    INSERT OR IGNORE INTO customer_payment_methods
                      (id, customer_id, tenant_id, payment_type,
                       upi_vpa, upi_provider,
                       card_last4, card_network, card_expiry_month, card_expiry_year,
                       card_bank_name, is_primary, created_at)
                    VALUES
                      (:id, :cid, :tid, :ptype,
                       :upi_vpa, :upi_prov,
                       :c_last4, :c_net, :c_exp_m, :c_exp_y,
                       :c_bank, :primary, :now)
                """), {
                    "id":       m["id"],
                    "cid":      m["customer_id"],
                    "tid":      tenant_id,
                    "ptype":    m["payment_type"],
                    "upi_vpa":  m["upi_vpa"],
                    "upi_prov": m["upi_provider"],
                    "c_last4":  m["card_last4"],
                    "c_net":    m["card_network"],
                    "c_exp_m":  m["card_expiry_month"],
                    "c_exp_y":  m["card_expiry_year"],
                    "c_bank":   m["card_bank_name"],
                    "primary":  1 if m["is_primary"] else 0,
                    "now":      datetime.now(timezone.utc).isoformat(),
                })
                total_pm += 1
        await session.commit()
        print(f"  Inserted {total_pm} payment methods into DB")

    await engine.dispose()


# ── Phase 5: Create fraud alerts for flagged transactions ─────────────────────

async def insert_fraud_alerts(transactions: list[dict], tenant_id: str):
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    fraud_txns = [t for t in transactions if t["is_flagged"]]
    async with session_factory() as session:
        for t in fraud_txns:
            severity = (
                "critical" if t["fraud_risk_level"] == "critical"
                else "high" if t["fraud_risk_level"] == "high"
                else "medium"
            )
            await session.execute(text("""
                INSERT OR IGNORE INTO fraud_alerts
                  (id, tenant_id, transaction_id, customer_id,
                   alert_type, severity, status,
                   is_confirmed, created_at)
                VALUES
                  (:id, :tenant_id, :txn_id, :cust_id,
                   'ml_model', :severity, :status,
                   :confirmed, :now)
            """), {
                "id":        str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "txn_id":    t["transaction_id"],
                "cust_id":   t["customer_id"],
                "severity":  severity,
                "status":    "open",
                "confirmed": 1 if t["is_blocked"] else 0,
                "now":       t["transaction_timestamp"],
            })
        await session.commit()
        print(f"  Inserted {len(fraud_txns)} fraud alerts into DB")

    await engine.dispose()


# ── Phase 6: Get active tenant from DB ───────────────────────────────────────

async def get_or_create_demo_tenant() -> str:
    """Return the first tenant ID found in DB, or a fixed demo ID."""
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(text("SELECT id FROM tenants LIMIT 1"))
        row = result.fetchone()

    await engine.dispose()

    if row:
        return row[0]

    # No tenant yet — return demo ID (will be used as tenant_id in seed data)
    return "demo-tenant-seed-0000-000000000001"


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n" + "="*60)
    print("  FinShield AI — Seed Data Generator")
    print("="*60)

    # Step 1: Get tenant ID
    tenant_id = await get_or_create_demo_tenant()
    print(f"\n[1/5] Tenant ID: {tenant_id}")

    # Step 2: Generate customers + cards
    print(f"\n[2/5] Generating {NUM_CUSTOMERS} customers + 10 test customers + cards...")
    customers, all_cards = generate_customers()

    fraud_dist = {p["type"]: p["count"] for p in CUSTOMER_PROFILES}
    for ptype, count in fraud_dist.items():
        print(f"       {ptype:<20} {count:>3} customers")

    # Add 10 test customers with easy unmasked card numbers
    test_customers, test_cards = build_test_customers()
    customers  = customers + test_customers
    all_cards  = all_cards + test_cards
    print("       + 10 test customers    10 customers (easy card numbers)")
    print(f"       Total cards generated: {len(all_cards)}")

    # Step 3: Generate transactions
    print(f"\n[3/5] Generating {NUM_TRANSACTIONS:,} transactions (3% fraud)...")
    transactions, labels = generate_transactions(customers, all_cards)

    fraud_count = sum(1 for t in transactions if t["is_flagged"])
    legit_count = NUM_TRANSACTIONS - fraud_count
    print(f"       Legitimate: {legit_count:,}  |  Fraudulent: {fraud_count:,}  |  Rate: {fraud_count/NUM_TRANSACTIONS*100:.1f}%")

    pattern_counts: dict = {}
    for t in transactions:
        p = t["fraud_pattern"]
        pattern_counts[p] = pattern_counts.get(p, 0) + 1

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        if pattern != "none":
            print(f"       {pattern:<22} {count:>3} cases")

    # Step 4: Write CSVs
    print(f"\n[4/5] Writing CSV files to {OUTPUT_DIR}/...")

    # Customer CSV — card fields embedded in columns 2-9
    CUST_COLS_ORDER = [
        "customer_id",
        # ── Card details (embedded, cols 2-9) ──────────────────────────────────
        "card_number",          # full for test customers, XXXX-XXXX-XXXX-{last4} for others
        "card_last4",
        "card_network",
        "card_cvv",
        "card_expiry",
        "card_status",
        "card_token",
        "active_card_count",
        # ── Personal info ──────────────────────────────────────────────────────
        "full_name", "email", "phone_number", "date_of_birth",
        "city", "state_province", "postal_code", "country_code",
        # ── Account ────────────────────────────────────────────────────────────
        "account_type", "account_opening_date", "account_status",
        "kyc_status", "kyc_level", "risk_score", "customer_tier",
        "balance_amount", "profile_type", "is_test_customer", "test_scenario",
    ]
    customer_csv = [{k: c.get(k, "") for k in CUST_COLS_ORDER} for c in customers]
    write_csv(customer_csv, "customers_100.csv")

    # Transactions CSV — include card_last4 and card_network for self-contained rows
    TXN_COLS_ORDER = [
        "transaction_id", "customer_id", "card_last4", "card_network",
        "amount", "currency", "transaction_type", "channel",
        "merchant_name", "merchant_category_code",
        "location_lat", "location_lng", "city", "country_code",
        "ip_address", "device_fingerprint", "device_type",
        "status", "fraud_score", "fraud_risk_level", "fraud_category",
        "is_flagged", "is_blocked", "is_test", "model_version",
        "triggered_rule_ids", "fraud_scored_at", "transaction_timestamp",
    ]
    transactions_csv = [{k: t.get(k, "") for k in TXN_COLS_ORDER} for t in transactions]
    write_csv(transactions_csv, "transactions_10000.csv")
    write_csv(labels, "fraud_labels.csv")

    # Also keep cards reference CSV (optional, for debugging)
    CARD_COLS = ["card_id", "customer_id", "card_network", "card_last4",
                 "card_masked", "card_number", "card_cvv", "card_expiry",
                 "card_token", "card_status", "is_primary", "is_test_card"]
    cards_csv = [{k: c.get(k, "") for k in CARD_COLS} for c in all_cards]
    write_csv(cards_csv, "cards_100.csv")

    # Step 5: Insert into DB
    print(f"\n[5/5] Inserting into SQLite DB ({DB_URL})...")
    await insert_to_db(customers, transactions, tenant_id)
    await insert_fraud_alerts(transactions, tenant_id)
    await insert_payment_methods(customers, tenant_id)

    # Summary
    print("\n" + "="*60)
    print("  SEED COMPLETE")
    print("="*60)
    print(f"  Customers:        {NUM_CUSTOMERS}")
    print(f"  Cards:            {len(all_cards)} (avg {len(all_cards)//NUM_CUSTOMERS} per customer)")
    print(f"  Transactions:     {NUM_TRANSACTIONS:,}")
    print(f"  Fraud cases:      {fraud_count} ({fraud_count/NUM_TRANSACTIONS*100:.1f}%)")
    print(f"  Fraud alerts:     {fraud_count}")
    print(f"  CSV dir:          {OUTPUT_DIR}")
    print("    customers_100.csv  (card embedded in cols 2-9)")
    print("    transactions_10000.csv  (card_last4 + card_network embedded)")
    print("    cards_100.csv      (reference only)")
    print("  DB:               finshield_dev.db")
    print("\n  Next: run python scripts/upload_to_supabase.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
