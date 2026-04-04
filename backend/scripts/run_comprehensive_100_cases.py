#!/usr/bin/env python3
"""
FinShield AI — Comprehensive 100 Test Cases (All Fraud Types & Outcomes)
=========================================================================

Generates 100 test cases deliberately designed to cover:
  ✅ PASS (Legitimate) — 25 cases
  ⚠️  FLAG (Suspicious 0.30–0.60) — 25 cases
  🔴 ALERT (High Risk 0.60–0.80) — 25 cases
  ⛔ BLOCK (Critical >0.80) — 25 cases

All results exported to CSV with complete fraud detection data.

Usage:
  python scripts/run_comprehensive_100_cases.py
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
API_BASE_URL = "http://localhost:8003/api/v1"
SIMULATOR_ENDPOINT = f"{API_BASE_URL}/simulator/predict"
AUTH_ENDPOINT = f"{API_BASE_URL}/auth/login"

TEST_USER_EMAIL = "admin@finshield.local"
TEST_USER_PASSWORD = "Admin123!@#"

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "test_results"
OUTPUT_CSV = OUTPUT_DIR / f"comprehensive_100_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─────────────────────────────────────────────────────────────────────
# PASS Cases (Legitimate) — 25 cases
# ─────────────────────────────────────────────────────────────────────

def create_pass_case(case_num: int) -> dict:
    """Create a legitimate transaction that should PASS."""
    locations = [
        ("Mumbai", 19.0760, 72.8777, "IN"),
        ("Bangalore", 12.9716, 77.5946, "IN"),
        ("Delhi", 28.6139, 77.2090, "IN"),
    ]
    city, lat, lng, country = random.choice(locations)

    return {
        "cardholder_name": f"Legitimate User {case_num}",
        "email": f"user{case_num}@example.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "4111111111111111",
        "card_type": "visa",
        "cvv": "123",
        "expiry_month": 12,
        "expiry_year": 2027,
        "amount": float(random.randint(500, 5000)),  # Low amounts
        "currency": "INR",
        "purchase_type": random.choice(["grocery", "restaurant", "fuel"]),
        "channel": "pos_physical",  # Card present = lower risk
        "merchant_name": random.choice(["D-Mart", "Zomato", "BPCL"]),
        "city": city,
        "country_code": country,
        "location_lat": lat + random.uniform(-0.01, 0.01),
        "location_lng": lng + random.uniform(-0.01, 0.01),
        "device_type": "pos_terminal",
        "is_new_device": False,  # Known device
        "transaction_timestamp": datetime.now(timezone.utc).replace(
            hour=random.randint(10, 20), minute=random.randint(0, 59)
        ).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────
# FLAG Cases (Suspicious 0.30–0.60) — 25 cases
# ─────────────────────────────────────────────────────────────────────

def create_flag_case(case_num: int) -> dict:
    """Create a suspicious transaction that should FLAG."""
    scenarios = [
        # Scenario 1: Foreign transaction + moderate amount
        {
            "city": "London",
            "country_code": "GB",
            "lat": 51.5074,
            "lng": -0.1278,
            "amount": 25000.0,
            "is_new_device": False,
            "hour": 14,
        },
        # Scenario 2: New device + moderate amount
        {
            "city": "Bangalore",
            "country_code": "IN",
            "lat": 12.9716,
            "lng": 77.5946,
            "amount": 20000.0,
            "is_new_device": True,
            "hour": 15,
        },
        # Scenario 3: Unusual hour + moderate amount
        {
            "city": "Mumbai",
            "country_code": "IN",
            "lat": 19.0760,
            "lng": 72.8777,
            "amount": 15000.0,
            "is_new_device": False,
            "hour": 3,
        },
        # Scenario 4: Foreign + new device
        {
            "city": "Singapore",
            "country_code": "SG",
            "lat": 1.3521,
            "lng": 103.8198,
            "amount": 30000.0,
            "is_new_device": True,
            "hour": 16,
        },
    ]

    scenario = random.choice(scenarios)
    return {
        "cardholder_name": f"Suspicious User {case_num}",
        "email": f"susp{case_num}@example.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "5555555555554444",
        "card_type": "mastercard",
        "cvv": "456",
        "expiry_month": 8,
        "expiry_year": 2026,
        "amount": scenario["amount"],
        "currency": "INR",
        "purchase_type": random.choice(["online_shopping", "electronics", "travel"]),
        "channel": random.choice(["online", "mobile"]),
        "merchant_name": random.choice(["Amazon", "Flipkart", "Booking.com"]),
        "city": scenario["city"],
        "country_code": scenario["country_code"],
        "location_lat": scenario["lat"],
        "location_lng": scenario["lng"],
        "device_type": "mobile",
        "is_new_device": scenario["is_new_device"],
        "transaction_timestamp": datetime.now(timezone.utc).replace(
            hour=scenario["hour"], minute=random.randint(0, 59)
        ).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────
# ALERT Cases (High Risk 0.60–0.80) — 25 cases
# ─────────────────────────────────────────────────────────────────────

def create_alert_case(case_num: int) -> dict:
    """Create a high-risk transaction that should ALERT."""
    scenarios = [
        # Account takeover: Foreign + new device + high amount + unusual hour
        {
            "city": "New York",
            "country": "US",
            "lat": 40.7128,
            "lng": -74.0060,
            "amount": 85000.0,
            "is_new_device": True,
            "hour": 2,
            "purchase_type": "electronics",
        },
        # High-value cash withdrawal at night + new device
        {
            "city": "Delhi",
            "country": "IN",
            "lat": 28.6139,
            "lng": 77.2090,
            "amount": 95000.0,
            "is_new_device": True,
            "hour": 3,
            "purchase_type": "atm_withdrawal",
        },
        # Multiple risk factors: High-risk country + new device + high amount
        {
            "city": "Dubai",
            "country": "AE",
            "lat": 25.2048,
            "lng": 55.2708,
            "amount": 120000.0,
            "is_new_device": True,
            "hour": 10,
            "purchase_type": "wire_transfer",
        },
        # Structuring pattern + wire transfer
        {
            "city": "Mumbai",
            "country": "IN",
            "lat": 19.0760,
            "lng": 72.8777,
            "amount": 750000.0,
            "is_new_device": False,
            "hour": 12,
            "purchase_type": "wire_transfer",
        },
    ]

    scenario = random.choice(scenarios)
    return {
        "cardholder_name": f"Alert Case {case_num}",
        "email": f"alert{case_num}@example.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "378282246310005",
        "card_type": "amex",
        "cvv": "7890",
        "expiry_month": 1,
        "expiry_year": 2026,
        "amount": scenario["amount"],
        "currency": "INR",
        "purchase_type": scenario["purchase_type"],
        "channel": random.choice(["online", "atm", "wire"]),
        "merchant_name": random.choice(["International Wire", "ATM", "High-End Electronics"]),
        "city": scenario["city"],
        "country_code": scenario["country"],
        "location_lat": scenario["lat"],
        "location_lng": scenario["lng"],
        "device_type": random.choice(["mobile", "desktop"]),
        "is_new_device": scenario["is_new_device"],
        "transaction_timestamp": datetime.now(timezone.utc).replace(
            hour=scenario["hour"], minute=random.randint(0, 59)
        ).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────
# BLOCK Cases (Critical >0.80) — 25 cases
# ─────────────────────────────────────────────────────────────────────

def create_block_case(case_num: int) -> dict:
    """Create a critical fraud transaction that should BLOCK."""
    scenarios = [
        # Impossible travel: Mumbai → London in 30 min (impossible!)
        {
            "city": "London",
            "country": "GB",
            "lat": 51.5074,
            "lng": -0.1278,
            "amount": 150000.0,
            "is_new_device": True,
            "hour": 2,
            "description": "Impossible Travel",
        },
        # Rapid velocity: Multiple high-value transactions in sequence
        {
            "city": "Singapore",
            "country": "SG",
            "lat": 1.3521,
            "lng": 103.8198,
            "amount": 200000.0,
            "is_new_device": True,
            "hour": 3,
            "description": "Velocity Fraud",
        },
        # High-risk country + massive amount + new device + unusual hour
        {
            "city": "Hong Kong",
            "country": "HK",
            "lat": 22.3193,
            "lng": 114.1694,
            "amount": 500000.0,
            "is_new_device": True,
            "hour": 4,
            "description": "Account Takeover",
        },
        # Structuring (multiple ₹8L+ transactions) + wire + new device
        {
            "city": "Mumbai",
            "country": "IN",
            "lat": 19.0760,
            "lng": 72.8777,
            "amount": 850000.0,
            "is_new_device": True,
            "hour": 5,
            "description": "Structuring",
        },
    ]

    scenario = random.choice(scenarios)
    return {
        "cardholder_name": f"Fraud Case {case_num}",
        "email": f"fraud{case_num}@test.com",
        "mobile_number": f"+91{9000000000 + case_num}",
        "card_number": "6011111111111117",
        "card_type": "rupay",
        "cvv": "789",
        "expiry_month": 3,
        "expiry_year": 2028,
        "amount": scenario["amount"],
        "currency": "INR",
        "purchase_type": random.choice(["wire_transfer", "electronics", "atm_withdrawal"]),
        "channel": random.choice(["online", "wire", "atm"]),
        "merchant_name": "Suspicious Merchant",
        "city": scenario["city"],
        "country_code": scenario["country"],
        "location_lat": scenario["lat"],
        "location_lng": scenario["lng"],
        "device_type": "mobile",
        "is_new_device": scenario["is_new_device"],
        "transaction_timestamp": datetime.now(timezone.utc).replace(
            hour=scenario["hour"], minute=random.randint(0, 59)
        ).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────
# Main execution
# ─────────────────────────────────────────────────────────────────────

async def get_auth_token() -> str:
    """Authenticate and get JWT token."""
    logger.info(f"Authenticating...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUTH_ENDPOINT,
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
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
    case_type: str,
    case_num: int,
    txn_data: dict,
) -> Optional[dict]:
    """Submit a test case."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(SIMULATOR_ENDPOINT, json=txn_data, headers=headers, timeout=30.0)

        if resp.status_code not in (200, 201):
            logger.warning(f"{case_type} #{case_num}: HTTP {resp.status_code}")
            return None

        result = resp.json()
        return {
            "case_type": case_type,
            "case_num": case_num,
            "cardholder_name": txn_data.get("cardholder_name"),
            "card_type": txn_data.get("card_type"),
            "amount": txn_data.get("amount"),
            "currency": txn_data.get("currency"),
            "purchase_type": txn_data.get("purchase_type"),
            "channel": txn_data.get("channel"),
            "merchant_name": txn_data.get("merchant_name"),
            "city": txn_data.get("city"),
            "country_code": txn_data.get("country_code"),
            "device_type": txn_data.get("device_type"),
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

    except Exception as e:
        logger.error(f"{case_type} #{case_num}: {e}")
        return None


async def main():
    """Main entry point."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 100)
    logger.info("FinShield AI — Comprehensive 100 Test Cases (All Fraud Types)")
    logger.info("=" * 100)

    token = await get_auth_token()

    # Generate 100 test cases: 25 per category
    logger.info("\nGenerating 100 diverse test cases...")
    test_cases = []

    # PASS cases
    for i in range(1, 26):
        test_cases.append(("PASS", i, create_pass_case(i)))

    # FLAG cases
    for i in range(26, 51):
        test_cases.append(("FLAG", i, create_flag_case(i)))

    # ALERT cases
    for i in range(51, 76):
        test_cases.append(("ALERT", i, create_alert_case(i)))

    # BLOCK cases
    for i in range(76, 101):
        test_cases.append(("BLOCK", i, create_block_case(i)))

    logger.info(f"✓ Generated 100 test cases\n")

    # Run all cases
    logger.info(f"Submitting {len(test_cases)} test cases to simulator...\n")
    results = []

    async with httpx.AsyncClient() as client:
        for i, (case_type, case_num, txn_data) in enumerate(test_cases):
            result = await run_test_case(client, token, case_type, case_num, txn_data)
            if result:
                results.append(result)
                logger.info(
                    f"{case_type:6s} #{case_num:3d} | "
                    f"₹{txn_data.get('amount'):9,.0f} | "
                    f"Score: {result.get('fraud_score'):5.2f} | "
                    f"{result.get('decision'):6s}"
                )

            if (i + 1) % 25 == 0:
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

        logger.info(f"✓ CSV created with {len(results)} rows\n")

        # Summary
        by_case_type = {}
        for r in results:
            case_type = r.get("case_type")
            by_case_type.setdefault(case_type, []).append(r.get("fraud_score", 0))

        logger.info("SUMMARY BY CASE TYPE:")
        for case_type in ["PASS", "FLAG", "ALERT", "BLOCK"]:
            if case_type in by_case_type:
                scores = by_case_type[case_type]
                avg = sum(scores) / len(scores)
                min_s = min(scores)
                max_s = max(scores)
                logger.info(
                    f"  {case_type:6s}: {len(scores):2d} cases | "
                    f"avg={avg:.3f} | min={min_s:.3f} | max={max_s:.3f}"
                )

        logger.info(f"\nOutput: {OUTPUT_CSV}")
    else:
        logger.error("✗ No results!")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
