#!/usr/bin/env python3
"""
FinShield AI — Run 100 Random Test Cases Through ML Pipeline
=============================================================

This script:
1. Generates 100 random test transactions with varied fraud patterns
2. Submits each to the Fraud Simulator API (/simulator/predict)
3. Collects fraud scores, decisions, triggered rules, and ML flags
4. Exports comprehensive CSV with all data points and ML predictions

Usage:
  python scripts/run_100_test_cases.py

Requirements:
  - Backend must be running on http://localhost:8003
  - Valid JWT token in environment or hardcoded (for testing)
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

# Test credentials (must exist in DB — created by seed_data.py)
TEST_USER_EMAIL = "admin@finshield.local"
TEST_USER_PASSWORD = "Admin123!@#"

# Output CSV path
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "test_results"
OUTPUT_CSV = OUTPUT_DIR / f"test_cases_100_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ─────────────────────────────────────────────────────────────────────
# Test data generation
# ─────────────────────────────────────────────────────────────────────

PURCHASE_TYPES = [
    "grocery", "restaurant", "online_shopping", "fuel", "travel",
    "atm_withdrawal", "electronics", "healthcare", "wire_transfer", "crypto"
]

CHANNELS = ["online", "pos_physical", "atm", "mobile", "wire"]

CARD_TYPES = ["visa", "mastercard", "rupay", "amex"]

DEVICE_TYPES = ["mobile", "desktop", "tablet", "pos_terminal"]

CITIES = [
    ("Mumbai", 19.0760, 72.8777, "IN"),
    ("Delhi", 28.6139, 77.2090, "IN"),
    ("Bangalore", 12.9716, 77.5946, "IN"),
    ("London", 51.5074, -0.1278, "GB"),
    ("New York", 40.7128, -74.0060, "US"),
    ("Singapore", 1.3521, 103.8198, "SG"),
    ("Hong Kong", 22.3193, 114.1694, "HK"),
]

MERCHANTS = [
    "D-Mart", "Zomato", "Amazon India", "BPCL Petrol Pump", "MakeMyTrip",
    "Croma", "Apollo Pharmacy", "Flipkart", "Myntra", "Swiggy"
]


def generate_random_transaction() -> dict:
    """Generate a random test transaction."""
    city, lat, lng, country_code = random.choice(CITIES)
    purchase_type = random.choice(PURCHASE_TYPES)

    # Amount varies by transaction type
    if purchase_type == "atm_withdrawal":
        amount = random.choice([5000, 10000, 20000, 50000, 75000, 99000])
    elif purchase_type in ("electronics", "travel", "wire_transfer"):
        amount = random.randint(15000, 150000)
    elif purchase_type == "online_shopping":
        amount = random.randint(500, 30000)
    else:
        amount = random.randint(100, 5000)

    # Determine card type based on purchase
    card_type = random.choice(CARD_TYPES)

    # Generate realistic card number (doesn't validate, just looks real)
    if card_type == "visa":
        card_num = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
    elif card_type == "mastercard":
        card_num = "5" + str(random.randint(1, 5)) + "".join([str(random.randint(0, 9)) for _ in range(14)])
    elif card_type == "amex":
        card_num = "3" + str(random.choice([4, 7])) + "".join([str(random.randint(0, 9)) for _ in range(13)])
    else:  # rupay
        card_num = "6" + "".join([str(random.randint(0, 9)) for _ in range(15)])

    # Device fingerprint
    device_type = random.choice(DEVICE_TYPES)
    is_new_device = random.random() < 0.3  # 30% new device

    # Optional: timestamp override (some fraud patterns happen at specific times)
    txn_time = datetime.now(timezone.utc)
    if random.random() < 0.15:  # 15% unusual hours
        txn_time = txn_time.replace(hour=random.choice([1, 2, 3, 4, 5]))

    return {
        "cardholder_name": f"Test User {random.randint(1000, 9999)}",
        "email": f"user{random.randint(100000, 999999)}@example.com",
        "mobile_number": f"+91{random.randint(6000000000, 9999999999)}",
        "card_number": card_num,
        "card_type": card_type,
        "cvv": str(random.randint(100, 999)) if card_type != "amex" else str(random.randint(1000, 9999)),
        "expiry_month": random.randint(1, 12),
        "expiry_year": random.randint(2025, 2029),
        "amount": float(amount),
        "currency": "INR",
        "purchase_type": purchase_type,
        "channel": random.choice(CHANNELS) if purchase_type != "atm_withdrawal" else "atm",
        "merchant_name": random.choice(MERCHANTS),
        "city": city,
        "country_code": country_code,
        "location_lat": lat + random.uniform(-0.1, 0.1),
        "location_lng": lng + random.uniform(-0.1, 0.1),
        "ip_address": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        "device_type": device_type,
        "is_new_device": is_new_device,
        "transaction_timestamp": txn_time.isoformat(),
    }


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

    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("No access_token in response")

    logger.info(f"✓ Authenticated, token: {token[:20]}...")
    return token


async def run_test_case(
    client: httpx.AsyncClient,
    token: str,
    index: int,
    txn_data: dict,
) -> Optional[dict]:
    """Submit a single test case to the simulator."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            SIMULATOR_ENDPOINT,
            json=txn_data,
            headers=headers,
            timeout=30.0,
        )

        if resp.status_code not in (200, 201):
            logger.warning(f"Case {index + 1}: HTTP {resp.status_code} — {resp.text[:200]}")
            return None

        result = resp.json()

        # Flatten the response for CSV
        flattened = {
            # Input data
            "case_num": index + 1,
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

            # ML Results
            "transaction_id": result.get("transaction_id"),
            "fraud_score": result.get("risk_score"),
            "fraud_score_pct": result.get("risk_score_pct"),
            "fraud_category": result.get("fraud_category"),
            "risk_level": result.get("risk_level"),
            "decision": result.get("decision"),
            "prediction": result.get("prediction"),
            "model_version": result.get("model_version"),
            "processing_ms": result.get("processing_ms"),

            # Rules triggered (as JSON string)
            "triggered_rules": json.dumps(result.get("triggered_rules", [])),

            # Top SHAP features (if available)
            "shap_top_features": _extract_shap_summary(result.get("shap_explanation")),

            # Summary
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Case {index + 1:3d} ✓ {txn_data['purchase_type']:15s} | "
            f"₹{txn_data['amount']:8,.0f} | Score: {result.get('risk_score'):.2f} | "
            f"{result.get('decision'):6s} | Rules: {len(result.get('triggered_rules', []))} triggered"
        )

        return flattened

    except Exception as e:
        logger.error(f"Case {index + 1}: {e}")
        return None


def _extract_shap_summary(shap_data: Optional[dict]) -> str:
    """Extract top SHAP features into a readable string."""
    if not shap_data:
        return ""

    features = shap_data.get("features", [])
    if not features:
        return ""

    # Take top 3 features
    top_features = features[:3]
    summary = "; ".join([f"{f.get('name')}:{f.get('impact'):.2f}" for f in top_features])
    return summary


async def main():
    """Main entry point."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("FinShield AI — 100 Random Test Cases")
    logger.info("=" * 80)

    # Get auth token
    token = await get_auth_token()

    # Generate test cases
    logger.info(f"\nGenerating 100 random test transactions...")
    test_cases = [generate_random_transaction() for _ in range(100)]

    # Run all cases
    logger.info(f"\nSubmitting {len(test_cases)} test cases to simulator...\n")

    results = []
    async with httpx.AsyncClient() as client:
        for i, txn_data in enumerate(test_cases):
            result = await run_test_case(client, token, i, txn_data)
            if result:
                results.append(result)

            # Small delay to avoid overwhelming the server
            if (i + 1) % 10 == 0:
                await asyncio.sleep(0.5)

    # Write CSV
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Writing results to CSV: {OUTPUT_CSV}")

    if results:
        fieldnames = results[0].keys()

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"✓ CSV created with {len(results)} rows")

        # Summary statistics
        fraud_scores = [r.get("fraud_score", 0) for r in results]
        avg_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

        decision_counts = {}
        for r in results:
            dec = r.get("decision", "UNKNOWN")
            decision_counts[dec] = decision_counts.get(dec, 0) + 1

        logger.info(f"\nSummary Statistics:")
        logger.info(f"  Total cases: {len(results)}")
        logger.info(f"  Average fraud score: {avg_score:.3f}")
        logger.info(f"  Decision distribution: {decision_counts}")
        logger.info(f"  CSV file: {OUTPUT_CSV}")
    else:
        logger.error("✗ No results collected!")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
