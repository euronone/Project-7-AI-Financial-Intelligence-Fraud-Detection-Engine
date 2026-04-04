#!/usr/bin/env python3
"""
FinShield AI — 25 Comprehensive Test Cases (All Decision Types)
================================================================

Generates exactly 25 test cases designed to produce ALL fraud outcomes:
  ✅ PASS       — ~7 legitimate transactions
  ⚠️  FLAG       — ~6 suspicious transactions
  🔴 ALERT      — ~6 high-risk transactions
  ⛔ BLOCK      — ~6 critical fraud transactions

Usage:
  python scripts/run_25_comprehensive.py
"""

import asyncio
import csv
import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

API_BASE_URL = "http://localhost:8003/api/v1"
AUTH_ENDPOINT = f"{API_BASE_URL}/auth/login"
SIMULATOR_ENDPOINT = f"{API_BASE_URL}/simulator/predict"

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "test_results"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


# ─────────────────────────────────────────────────────────────────────
# 25 hand-crafted test scenarios
# ─────────────────────────────────────────────────────────────────────

TEST_SCENARIOS = [
    # ── PASS cases (low risk, legitimate) ─────────────────────────
    {
        "label": "Normal grocery purchase",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Priya Sharma",
            "email": "priya@example.com",
            "mobile_number": "+919876543210",
            "card_number": "4111111111111111",
            "card_type": "visa",
            "cvv": "123",
            "expiry_month": 12,
            "expiry_year": 2027,
            "amount": 1200.0,
            "currency": "INR",
            "purchase_type": "grocery",
            "channel": "pos_physical",
            "merchant_name": "D-Mart",
            "city": "Mumbai",
            "country_code": "IN",
            "location_lat": 19.0760,
            "location_lng": 72.8777,
            "device_type": "pos_terminal",
            "is_new_device": False,
        },
    },
    {
        "label": "Lunch at restaurant",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Amit Patel",
            "email": "amit@example.com",
            "mobile_number": "+919876543211",
            "card_number": "4222222222222222",
            "card_type": "visa",
            "cvv": "456",
            "expiry_month": 6,
            "expiry_year": 2028,
            "amount": 850.0,
            "currency": "INR",
            "purchase_type": "restaurant",
            "channel": "pos_physical",
            "merchant_name": "Barbeque Nation",
            "city": "Bangalore",
            "country_code": "IN",
            "location_lat": 12.9716,
            "location_lng": 77.5946,
            "device_type": "pos_terminal",
            "is_new_device": False,
        },
    },
    {
        "label": "Fuel purchase daytime",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Sunita Reddy",
            "email": "sunita@example.com",
            "mobile_number": "+919876543212",
            "card_number": "5555555555554444",
            "card_type": "mastercard",
            "cvv": "789",
            "expiry_month": 3,
            "expiry_year": 2027,
            "amount": 2500.0,
            "currency": "INR",
            "purchase_type": "fuel",
            "channel": "pos_physical",
            "merchant_name": "BPCL Petrol Pump",
            "city": "Delhi",
            "country_code": "IN",
            "location_lat": 28.6139,
            "location_lng": 77.2090,
            "device_type": "pos_terminal",
            "is_new_device": False,
        },
    },
    {
        "label": "Small online purchase known device",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Rahul Jain",
            "email": "rahul@example.com",
            "mobile_number": "+919876543213",
            "card_number": "4333333333333333",
            "card_type": "visa",
            "cvv": "321",
            "expiry_month": 9,
            "expiry_year": 2027,
            "amount": 3500.0,
            "currency": "INR",
            "purchase_type": "online_shopping",
            "channel": "online",
            "merchant_name": "Amazon India",
            "city": "Mumbai",
            "country_code": "IN",
            "location_lat": 19.0760,
            "location_lng": 72.8777,
            "device_type": "mobile",
            "is_new_device": False,
        },
    },
    {
        "label": "Medicine purchase",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Neha Gupta",
            "email": "neha@example.com",
            "mobile_number": "+919876543214",
            "card_number": "4444444444444444",
            "card_type": "visa",
            "cvv": "654",
            "expiry_month": 11,
            "expiry_year": 2026,
            "amount": 1800.0,
            "currency": "INR",
            "purchase_type": "healthcare",
            "channel": "pos_physical",
            "merchant_name": "Apollo Pharmacy",
            "city": "Chennai",
            "country_code": "IN",
            "location_lat": 13.0827,
            "location_lng": 80.2707,
            "device_type": "pos_terminal",
            "is_new_device": False,
        },
    },
    {
        "label": "Weekly grocery shopping",
        "expected": "PASS",
        "payload": {
            "cardholder_name": "Vikram Singh",
            "email": "vikram@example.com",
            "mobile_number": "+919876543215",
            "card_number": "6011111111111117",
            "card_type": "rupay",
            "cvv": "987",
            "expiry_month": 5,
            "expiry_year": 2028,
            "amount": 4200.0,
            "currency": "INR",
            "purchase_type": "grocery",
            "channel": "pos_physical",
            "merchant_name": "Big Bazaar",
            "city": "Pune",
            "country_code": "IN",
            "location_lat": 18.5204,
            "location_lng": 73.8567,
            "device_type": "pos_terminal",
            "is_new_device": False,
        },
    },

    # ── FLAG cases (suspicious, should trigger 0.30–0.59) ─────────
    {
        "label": "Foreign transaction moderate amount",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Kiran Kumar",
            "email": "kiran@example.com",
            "mobile_number": "+919876543216",
            "card_number": "5500005555555559",
            "card_type": "mastercard",
            "cvv": "111",
            "expiry_month": 12,
            "expiry_year": 2027,
            "amount": 35000.0,
            "currency": "INR",
            "purchase_type": "online_shopping",
            "channel": "online",
            "merchant_name": "Amazon UK",
            "city": "London",
            "country_code": "GB",
            "location_lat": 51.5074,
            "location_lng": -0.1278,
            "device_type": "mobile",
            "is_new_device": True,
        },
    },
    {
        "label": "New device + unusual hour purchase",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Deepak Verma",
            "email": "deepak@example.com",
            "mobile_number": "+919876543217",
            "card_number": "5500005555555560",
            "card_type": "mastercard",
            "cvv": "222",
            "expiry_month": 7,
            "expiry_year": 2026,
            "amount": 28000.0,
            "currency": "INR",
            "purchase_type": "electronics",
            "channel": "online",
            "merchant_name": "Croma",
            "city": "Mumbai",
            "country_code": "IN",
            "location_lat": 19.0760,
            "location_lng": 72.8777,
            "device_type": "desktop",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=30).isoformat(),
        },
    },
    {
        "label": "Foreign purchase with new device",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Anjali Mehta",
            "email": "anjali@example.com",
            "mobile_number": "+919876543218",
            "card_number": "378282246310005",
            "card_type": "amex",
            "cvv": "3333",
            "expiry_month": 8,
            "expiry_year": 2027,
            "amount": 22000.0,
            "currency": "INR",
            "purchase_type": "travel",
            "channel": "online",
            "merchant_name": "Booking.com",
            "city": "Dubai",
            "country_code": "AE",
            "location_lat": 25.2048,
            "location_lng": 55.2708,
            "device_type": "tablet",
            "is_new_device": True,
        },
    },
    {
        "label": "Large ATM withdrawal new location",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Sanjay Pandey",
            "email": "sanjay@example.com",
            "mobile_number": "+919876543219",
            "card_number": "6011111111111118",
            "card_type": "rupay",
            "cvv": "444",
            "expiry_month": 2,
            "expiry_year": 2028,
            "amount": 40000.0,
            "currency": "INR",
            "purchase_type": "atm_withdrawal",
            "channel": "atm",
            "merchant_name": "SBI ATM",
            "city": "Jaipur",
            "country_code": "IN",
            "location_lat": 26.9124,
            "location_lng": 75.7873,
            "device_type": "pos_terminal",
            "is_new_device": True,
        },
    },
    {
        "label": "High-risk merchant category + moderate amount",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Rohit Sharma",
            "email": "rohit@example.com",
            "mobile_number": "+919876543220",
            "card_number": "4111111111111112",
            "card_type": "visa",
            "cvv": "555",
            "expiry_month": 10,
            "expiry_year": 2027,
            "amount": 45000.0,
            "currency": "INR",
            "purchase_type": "crypto",
            "channel": "online",
            "merchant_name": "CoinSwitch Kuber",
            "city": "Bangalore",
            "country_code": "IN",
            "location_lat": 12.9716,
            "location_lng": 77.5946,
            "device_type": "desktop",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=2, minute=15).isoformat(),
        },
    },
    {
        "label": "Foreign wire transfer moderate",
        "expected": "FLAG",
        "payload": {
            "cardholder_name": "Meera Iyer",
            "email": "meera@example.com",
            "mobile_number": "+919876543221",
            "card_number": "5105105105105100",
            "card_type": "mastercard",
            "cvv": "666",
            "expiry_month": 4,
            "expiry_year": 2027,
            "amount": 55000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "International Wire",
            "city": "Singapore",
            "country_code": "SG",
            "location_lat": 1.3521,
            "location_lng": 103.8198,
            "device_type": "desktop",
            "is_new_device": False,
        },
    },

    # ── ALERT cases (high risk, should trigger 0.60–0.79) ─────────
    {
        "label": "Foreign + new device + high value + night",
        "expected": "ALERT",
        "payload": {
            "cardholder_name": "Arjun Nair",
            "email": "arjun@example.com",
            "mobile_number": "+919876543222",
            "card_number": "4111111111111113",
            "card_type": "visa",
            "cvv": "777",
            "expiry_month": 12,
            "expiry_year": 2027,
            "amount": 85000.0,
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
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=2, minute=45).isoformat(),
        },
    },
    {
        "label": "Large ATM at 3AM + new device",
        "expected": "ALERT",
        "payload": {
            "cardholder_name": "Pooja Saxena",
            "email": "pooja@example.com",
            "mobile_number": "+919876543223",
            "card_number": "5500005555555561",
            "card_type": "mastercard",
            "cvv": "888",
            "expiry_month": 6,
            "expiry_year": 2026,
            "amount": 95000.0,
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
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=0).isoformat(),
        },
    },
    {
        "label": "Foreign wire + new device + high value",
        "expected": "ALERT",
        "payload": {
            "cardholder_name": "Ramesh Agarwal",
            "email": "ramesh@example.com",
            "mobile_number": "+919876543224",
            "card_number": "378282246310006",
            "card_type": "amex",
            "cvv": "9990",
            "expiry_month": 1,
            "expiry_year": 2028,
            "amount": 120000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "International Wire Transfer",
            "city": "Hong Kong",
            "country_code": "HK",
            "location_lat": 22.3193,
            "location_lng": 114.1694,
            "device_type": "desktop",
            "is_new_device": True,
        },
    },
    {
        "label": "High-risk country + large online + new device",
        "expected": "ALERT",
        "payload": {
            "cardholder_name": "Suresh Pillai",
            "email": "suresh@example.com",
            "mobile_number": "+919876543225",
            "card_number": "4111111111111114",
            "card_type": "visa",
            "cvv": "101",
            "expiry_month": 9,
            "expiry_year": 2027,
            "amount": 75000.0,
            "currency": "INR",
            "purchase_type": "electronics",
            "channel": "online",
            "merchant_name": "AliExpress",
            "city": "Lagos",
            "country_code": "NG",
            "location_lat": 6.5244,
            "location_lng": 3.3792,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=4, minute=20).isoformat(),
        },
    },
    {
        "label": "Very large purchase new device foreign night",
        "expected": "ALERT",
        "payload": {
            "cardholder_name": "Kavita Deshmukh",
            "email": "kavita@example.com",
            "mobile_number": "+919876543226",
            "card_number": "5500005555555562",
            "card_type": "mastercard",
            "cvv": "202",
            "expiry_month": 11,
            "expiry_year": 2026,
            "amount": 180000.0,
            "currency": "INR",
            "purchase_type": "electronics",
            "channel": "online",
            "merchant_name": "Apple Store",
            "city": "London",
            "country_code": "GB",
            "location_lat": 51.5074,
            "location_lng": -0.1278,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=1, minute=30).isoformat(),
        },
    },

    # ── BLOCK cases (critical fraud, should trigger ≥ 0.80) ───────
    {
        "label": "High-risk country + massive amount + new device + 3AM",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Account Takeover",
            "email": "fraud1@test.com",
            "mobile_number": "+919876543227",
            "card_number": "6011111111111119",
            "card_type": "rupay",
            "cvv": "303",
            "expiry_month": 3,
            "expiry_year": 2028,
            "amount": 350000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "Suspicious Wire Transfer",
            "city": "Kyiv",
            "country_code": "UA",
            "location_lat": 50.4501,
            "location_lng": 30.5234,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=15).isoformat(),
        },
    },
    {
        "label": "Sanctioned country + wire + large + new device + night",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Sanctions Violation",
            "email": "fraud2@test.com",
            "mobile_number": "+919876543228",
            "card_number": "4111111111111115",
            "card_type": "visa",
            "cvv": "404",
            "expiry_month": 7,
            "expiry_year": 2027,
            "amount": 500000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "International Wire",
            "city": "Tehran",
            "country_code": "IR",
            "location_lat": 35.6892,
            "location_lng": 51.3890,
            "device_type": "desktop",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=2, minute=0).isoformat(),
        },
    },
    {
        "label": "Massive structuring amount + new device + night",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Money Laundering",
            "email": "fraud3@test.com",
            "mobile_number": "+919876543229",
            "card_number": "5500005555555563",
            "card_type": "mastercard",
            "cvv": "505",
            "expiry_month": 5,
            "expiry_year": 2026,
            "amount": 780000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "Offshore Wire",
            "city": "Moscow",
            "country_code": "RU",
            "location_lat": 55.7558,
            "location_lng": 37.6176,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=4, minute=0).isoformat(),
        },
    },
    {
        "label": "North Korea wire + huge amount + all red flags",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Sanctioned Entity",
            "email": "fraud4@test.com",
            "mobile_number": "+919876543230",
            "card_number": "378282246310007",
            "card_type": "amex",
            "cvv": "6060",
            "expiry_month": 2,
            "expiry_year": 2028,
            "amount": 900000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "Unknown Foreign Wire",
            "city": "Pyongyang",
            "country_code": "KP",
            "location_lat": 39.0392,
            "location_lng": 125.7625,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=1, minute=45).isoformat(),
        },
    },
    {
        "label": "Crypto exchange + high-risk country + massive + night",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Crypto Laundering",
            "email": "fraud5@test.com",
            "mobile_number": "+919876543231",
            "card_number": "6011111111111120",
            "card_type": "rupay",
            "cvv": "707",
            "expiry_month": 8,
            "expiry_year": 2027,
            "amount": 650000.0,
            "currency": "INR",
            "purchase_type": "crypto",
            "channel": "online",
            "merchant_name": "Unknown Crypto Exchange",
            "city": "Accra",
            "country_code": "GH",
            "location_lat": 5.6037,
            "location_lng": -0.1870,
            "device_type": "mobile",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=3, minute=30).isoformat(),
        },
    },
    {
        "label": "Syria wire + extreme amount + all signals",
        "expected": "BLOCK",
        "payload": {
            "cardholder_name": "FRAUD - Terror Finance",
            "email": "fraud6@test.com",
            "mobile_number": "+919876543232",
            "card_number": "4111111111111116",
            "card_type": "visa",
            "cvv": "808",
            "expiry_month": 4,
            "expiry_year": 2027,
            "amount": 999000.0,
            "currency": "INR",
            "purchase_type": "wire_transfer",
            "channel": "wire",
            "merchant_name": "International Wire",
            "city": "Damascus",
            "country_code": "SY",
            "location_lat": 33.5138,
            "location_lng": 36.2765,
            "device_type": "desktop",
            "is_new_device": True,
            "transaction_timestamp": datetime.now(timezone.utc).replace(hour=2, minute=30).isoformat(),
        },
    },
]


# ─────────────────────────────────────────────────────────────────────

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"test_25_all_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    logger.info("=" * 90)
    logger.info("FinShield AI — 25 Comprehensive Test Cases (PASS / FLAG / ALERT / BLOCK)")
    logger.info("=" * 90)

    # Auth
    async with httpx.AsyncClient() as client:
        resp = await client.post(AUTH_ENDPOINT, json={
            "email": "admin@finshield.local",
            "password": "Admin123!@#",
        })
    if resp.status_code != 200:
        logger.error(f"Auth failed: {resp.text}")
        return 1
    token = resp.json()["access_token"]
    logger.info("✓ Authenticated\n")

    # Run tests
    results = []
    async with httpx.AsyncClient() as client:
        for i, scenario in enumerate(TEST_SCENARIOS):
            try:
                resp = await client.post(
                    SIMULATOR_ENDPOINT,
                    json=scenario["payload"],
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                if resp.status_code not in (200, 201):
                    logger.warning(f"  #{i+1:2d} {scenario['label'][:35]:35s} | HTTP {resp.status_code}")
                    continue

                r = resp.json()
                score = r.get("risk_score", 0)
                decision = r.get("decision", "?")
                expected = scenario["expected"]
                match = "✓" if decision == expected else "✗"

                row = {
                    "case_num": i + 1,
                    "label": scenario["label"],
                    "expected_decision": expected,
                    "actual_decision": decision,
                    "match": match,
                    "cardholder": scenario["payload"]["cardholder_name"],
                    "amount": scenario["payload"]["amount"],
                    "currency": scenario["payload"]["currency"],
                    "purchase_type": scenario["payload"]["purchase_type"],
                    "channel": scenario["payload"]["channel"],
                    "merchant": scenario["payload"]["merchant_name"],
                    "city": scenario["payload"]["city"],
                    "country": scenario["payload"]["country_code"],
                    "card_type": scenario["payload"]["card_type"],
                    "is_new_device": scenario["payload"]["is_new_device"],
                    "fraud_score": score,
                    "fraud_score_pct": r.get("risk_score_pct", ""),
                    "fraud_category": r.get("fraud_category", ""),
                    "risk_level": r.get("risk_level", ""),
                    "prediction": r.get("prediction", ""),
                    "triggered_rules": json.dumps(r.get("triggered_rules", [])),
                    "processing_ms": r.get("processing_ms", 0),
                    "transaction_id": r.get("transaction_id", ""),
                }
                results.append(row)

                color = {"PASS": "🟢", "FLAG": "🟡", "ALERT": "🟠", "BLOCK": "🔴"}.get(decision, "⚪")
                logger.info(
                    f"  #{i+1:2d} {match} {scenario['label'][:35]:35s} | "
                    f"₹{scenario['payload']['amount']:>10,.0f} | "
                    f"Score: {score:.2f} | {color} {decision:6s} "
                    f"(expected {expected})"
                )
            except Exception as e:
                logger.error(f"  #{i+1:2d} ERROR: {e}")

    # Write CSV
    if results:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        # Summary
        decisions = {}
        matches = 0
        for r in results:
            d = r["actual_decision"]
            decisions[d] = decisions.get(d, 0) + 1
            if r["match"] == "✓":
                matches += 1

        logger.info(f"\n{'=' * 90}")
        logger.info(f"RESULTS: {len(results)} test cases")
        logger.info(f"  Decision distribution: {decisions}")
        logger.info(f"  Expected match rate:   {matches}/{len(results)} ({100*matches/len(results):.0f}%)")
        logger.info(f"  CSV saved: {output_file}")
        logger.info(f"{'=' * 90}")
    else:
        logger.error("No results!")
        return 1
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
