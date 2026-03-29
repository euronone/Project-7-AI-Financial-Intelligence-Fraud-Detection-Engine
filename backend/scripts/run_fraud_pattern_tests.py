#!/usr/bin/env python3
"""
FinShield AI — Test 100+ Fraud Patterns (High-Fraud Scenarios)
================================================================

This script generates test cases designed to trigger HIGH fraud scores
across all fraud pattern categories:
  - Impossible travel (>900 km/hr)
  - Velocity fraud (rapid transactions)
  - Card-not-present high-value
  - Account takeover patterns
  - Structuring/Smurfing
  - High-risk countries
  - New devices + unusual hours + high amounts

Usage:
  python scripts/run_fraud_pattern_tests.py

Output: CSV with fraud detection results, decision points, and triggered rules
"""

import asyncio
import csv
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx

# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8003/api/v1"
SIMULATOR_ENDPOINT = f"{API_BASE_URL}/simulator/predict"
AUTH_ENDPOINT = f"{API_BASE_URL}/auth/login"

TEST_USER_EMAIL = "admin@finshield.local"
TEST_USER_PASSWORD = "Admin123!@#"

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "test_results"
OUTPUT_CSV = OUTPUT_DIR / f"fraud_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─────────────────────────────────────────────────────────────────────
# Fraud pattern generators
# ─────────────────────────────────────────────────────────────────────

def create_impossible_travel_case(case_num: int) -> dict:
    """Mumbai -> London in 15 minutes = impossible travel."""
    base_time = datetime.now(timezone.utc)
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "4111111111111111",
        "card_type": "visa",
        "cvv": "123",
        "expiry_month": 12,
        "expiry_year": 2027,
        "amount": 50000.0,
        "currency": "INR",
        "purchase_type": "electronics",
        "channel": "online",
        "merchant_name": "Amazon UK",
        "city": "London",
        "country_code": "GB",
        "location_lat": 51.5074,
        "location_lng": -0.1278,
        "device_type": "mobile",
        "is_new_device": True,
        "transaction_timestamp": base_time.replace(hour=2, minute=30).isoformat(),
    }


def create_velocity_fraud_case(case_num: int) -> dict:
    """6 rapid transactions in 10 minutes."""
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "5555555555554444",
        "card_type": "mastercard",
        "cvv": "456",
        "expiry_month": 8,
        "expiry_year": 2026,
        "amount": float(random.randint(5000, 15000)),
        "currency": "INR",
        "purchase_type": "online_shopping",
        "channel": "online",
        "merchant_name": random.choice(["Flipkart", "Amazon", "Myntra", "EBay"]),
        "city": "Bangalore",
        "country_code": "IN",
        "location_lat": 12.9716,
        "location_lng": 77.5946,
        "device_type": "desktop",
        "is_new_device": False,
    }


def create_account_takeover_case(case_num: int) -> dict:
    """New device + high value + unusual hour + different country."""
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "378282246310005",
        "card_type": "amex",
        "cvv": "7890",
        "expiry_month": 1,
        "expiry_year": 2026,
        "amount": 125000.0,
        "currency": "INR",
        "purchase_type": "electronics",
        "channel": "online",
        "merchant_name": "BestBuy",
        "city": "New York",
        "country_code": "US",
        "location_lat": 40.7128,
        "location_lng": -74.0060,
        "device_type": "mobile",
        "is_new_device": True,
        "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=45).isoformat(),
    }


def create_structuring_case(case_num: int) -> dict:
    """Amount just below ₹8,00,000 threshold (structuring pattern)."""
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "6011111111111117",
        "card_type": "rupay",
        "cvv": "789",
        "expiry_month": 3,
        "expiry_year": 2028,
        "amount": 750000.0,
        "currency": "INR",
        "purchase_type": "wire_transfer",
        "channel": "wire",
        "merchant_name": "International Wire",
        "city": "Mumbai",
        "country_code": "IN",
        "location_lat": 19.0760,
        "location_lng": 72.8777,
        "device_type": "desktop",
        "is_new_device": False,
    }


def create_cnp_fraud_case(case_num: int) -> dict:
    """High-value card-not-present (online) with new device."""
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "4556737586899855",
        "card_type": "visa",
        "cvv": "123",
        "expiry_month": 6,
        "expiry_year": 2027,
        "amount": 95000.0,
        "currency": "INR",
        "purchase_type": "online_shopping",
        "channel": "online",
        "merchant_name": "Luxury.com",
        "city": "Singapore",
        "country_code": "SG",
        "location_lat": 1.3521,
        "location_lng": 103.8198,
        "device_type": "mobile",
        "is_new_device": True,
    }


def create_cash_withdrawal_fraud(case_num: int) -> dict:
    """Large ATM withdrawal at 3 AM from new device."""
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "5105105105105100",
        "card_type": "mastercard",
        "cvv": "456",
        "expiry_month": 4,
        "expiry_year": 2027,
        "amount": 98000.0,
        "currency": "INR",
        "purchase_type": "atm_withdrawal",
        "channel": "atm",
        "merchant_name": "ATM Withdrawal",
        "city": "Delhi",
        "country_code": "IN",
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "device_type": "pos_terminal",
        "is_new_device": True,
        "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=15).isoformat(),
    }


def create_high_risk_country_case(case_num: int) -> dict:
    """Transaction from sanctioned/high-risk country."""
    risk_countries = [
        ("Iran", 32.4279, 53.6880, "IR"),
        ("North Korea", 40.3399, 127.5101, "KP"),
        ("Syria", 34.8021, 38.9968, "SY"),
    ]
    city, lat, lng, country = random.choice(risk_countries)
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "4111111111111111",
        "card_type": "visa",
        "cvv": "123",
        "expiry_month": 12,
        "expiry_year": 2027,
        "amount": 50000.0,
        "currency": "INR",
        "purchase_type": "electronics",
        "channel": "online",
        "merchant_name": "Local Merchant",
        "city": city,
        "country_code": country,
        "location_lat": lat,
        "location_lng": lng,
        "device_type": "mobile",
        "is_new_device": False,
    }


# ─────────────────────────────────────────────────────────────────────
# Test case generators (patterns)
# ─────────────────────────────────────────────────────────────────────

FRAUD_GENERATORS = [
    ("Impossible Travel", create_impossible_travel_case),
    ("Velocity Fraud", create_velocity_fraud_case),
    ("Account Takeover", create_account_takeover_case),
    ("Structuring Pattern", create_structuring_case),
    ("CNP High-Value", create_cnp_fraud_case),
    ("Cash Withdrawal", create_cash_withdrawal_fraud),
    ("High-Risk Country", create_high_risk_country_case),
]


# ─────────────────────────────────────────────────────────────────────
# Main execution
# ─────────────────────────────────────────────────────────────────────

async def get_auth_token() -> str:
    """Authenticate and get JWT token."""
    logger.info(f"Authenticating with {TEST_USER_EMAIL}...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUTH_ENDPOINT,
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            },
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Auth failed: {resp.text}")
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in response")
    logger.info(f"✓ Authenticated")
    return token


async def run_test_case(
    client: httpx.AsyncClient,
    token: str,
    pattern_name: str,
    case_num: int,
    txn_data: dict,
) -> Optional[dict]:
    """Submit a test case."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            SIMULATOR_ENDPOINT,
            json=txn_data,
            headers=headers,
            timeout=30.0,
        )
        if resp.status_code not in (200, 201):
            logger.warning(f"{pattern_name} #{case_num}: HTTP {resp.status_code}")
            return None

        result = resp.json()
        flattened = {
            "pattern": pattern_name,
            "case_num": case_num,
            "cardholder": txn_data.get("cardholder_name"),
            "card_type": txn_data.get("card_type"),
            "amount": txn_data.get("amount"),
            "purchase_type": txn_data.get("purchase_type"),
            "city": txn_data.get("city"),
            "country_code": txn_data.get("country_code"),
            "is_new_device": txn_data.get("is_new_device"),
            "transaction_id": result.get("transaction_id"),
            "fraud_score": result.get("risk_score"),
            "fraud_score_pct": result.get("risk_score_pct"),
            "fraud_category": result.get("fraud_category"),
            "risk_level": result.get("risk_level"),
            "decision": result.get("decision"),
            "prediction": result.get("prediction"),
            "triggered_rules": json.dumps(result.get("triggered_rules", [])),
            "processing_ms": result.get("processing_ms"),
        }
        logger.info(
            f"{pattern_name:20s} #{case_num:2d} | Score: {result.get('risk_score'):5.2f} | "
            f"{result.get('decision'):6s} | {result.get('risk_level'):10s}"
        )
        return flattened

    except Exception as e:
        logger.error(f"{pattern_name} #{case_num}: {e}")
        return None


async def main():
    """Main entry point."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 100)
    logger.info("FinShield AI — Fraud Pattern Detection Tests")
    logger.info("=" * 100)

    token = await get_auth_token()

    # Generate test cases: 10+ per pattern
    logger.info(f"\nGenerating fraud pattern test cases...")
    test_cases = []
    case_id = 1

    for pattern_name, generator in FRAUD_GENERATORS:
        for i in range(15):  # 15 per pattern
            txn_data = generator(case_id)
            test_cases.append((pattern_name, case_id, txn_data))
            case_id += 1

    logger.info(f"✓ Generated {len(test_cases)} test cases across {len(FRAUD_GENERATORS)} patterns\n")

    # Run all cases
    logger.info(f"Submitting test cases to simulator...\n")
    results = []

    async with httpx.AsyncClient() as client:
        for i, (pattern_name, case_num, txn_data) in enumerate(test_cases):
            result = await run_test_case(client, token, pattern_name, case_num, txn_data)
            if result:
                results.append(result)

            if (i + 1) % 20 == 0:
                await asyncio.sleep(1)

    # Write CSV
    logger.info(f"\n{'=' * 100}")
    logger.info(f"Writing {len(results)} results to: {OUTPUT_CSV}")

    if results:
        fieldnames = results[0].keys()
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"✓ CSV created with {len(results)} rows")

        # Summary
        by_pattern = {}
        for r in results:
            pattern = r.get("pattern")
            by_pattern.setdefault(pattern, []).append(r.get("fraud_score", 0))

        logger.info(f"\nFRAUD PATTERN SUMMARY:")
        for pattern, scores in sorted(by_pattern.items()):
            avg = sum(scores) / len(scores)
            max_score = max(scores)
            logger.info(f"  {pattern:20s}: avg={avg:.3f}, max={max_score:.3f}, n={len(scores)}")

        logger.info(f"\nOutput: {OUTPUT_CSV}")
    else:
        logger.error("✗ No results!")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
