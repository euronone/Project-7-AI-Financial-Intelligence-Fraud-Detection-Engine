#!/usr/bin/env python3
"""
FinShield AI - Demo: How the Fraud Detection Platform Works

This script demonstrates a realistic end-to-end fraud detection scenario:
  1. Analyst logs in
  2. A suspicious transaction is ingested (high amount, foreign IP, etc.)
  3. ML pipeline scores the transaction and flags it as high risk
  4. An alert is surfaced (or we use an existing one from seed)
  5. Analyst creates an investigation case from the alert
  6. Dashboard analytics show the impact

Prerequisites:
  - Backend: poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
  - DB seeded: poetry run python scripts/seed_data.py
  - Docker: Postgres + Redis running (docker compose up -d)

Usage: poetry run python scripts/demo_fraud_scenario.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
LOGIN_EMAIL = "analyst1@finshield.dev"
LOGIN_PASSWORD = "Admin123!@#"


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: int, title: str, detail: str = ""):
    print(f"\n--- Step {step}: {title} ---")
    if detail:
        print(detail)


def main():
    print_section("FinShield AI - Fraud Detection Demo")
    print("\nThis demo shows how the platform detects and investigates fraud.")
    print("Scenario: A high-value transaction from an unusual location triggers")
    print("the ML pipeline, creates an alert, and leads to a case.")

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Login
        print_step(1, "Analyst logs in", f"User: {LOGIN_EMAIL}")
        r = client.post(f"{API_PREFIX}/auth/login", json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD})
        if r.status_code != 200:
            print(f"  [X] Login failed: {r.status_code}. Ensure backend is running and DB is seeded.")
            return 1
        token = r.json()["access_token"]
        user = r.json().get("user", {})
        print(f"  [OK] Logged in as {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('role', '')})")
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Get entities for transaction
        print_step(2, "Fetch entities for transaction", "Need source and destination entities")
        r = client.get(f"{API_PREFIX}/entities", headers=headers, params={"page": 1, "page_size": 2})
        if r.status_code != 200 or not r.json().get("items"):
            print("  [X] No entities. Run: poetry run python scripts/seed_data.py")
            return 1
        entities = r.json()["items"]
        source_id = entities[0]["id"]
        dest_id = entities[1]["id"] if len(entities) > 1 else entities[0]["id"]
        print(f"  [OK] Source entity: {entities[0]['name']} ({entities[0]['entity_type']})")
        print(f"  [OK] Destination: {entities[1]['name']}" if len(entities) > 1 else "  [OK] Same entity for demo")

        # Step 3: Ingest a suspicious transaction
        print_step(
            3,
            "Ingest suspicious transaction",
            "High amount ($15,000), foreign IP (Nigeria), online channel - typical fraud pattern",
        )
        txn_payload = {
            "external_id": f"DEMO-{uuid.uuid4().hex[:12]}",
            "source_entity_id": source_id,
            "destination_entity_id": dest_id,
            "amount": 15000.00,
            "currency": "USD",
            "transaction_type": "payment",
            "channel": "online",
            "merchant_category_code": "5411",
            "description": "Electronics purchase - DEMO",
            "ip_address": "41.203.123.45",  # Nigeria - unusual for US entity
            "country_code": "NG",
            "card_present": False,
        }
        r = client.post(f"{API_PREFIX}/transactions", headers=headers, json=txn_payload)
        if r.status_code not in (200, 201):
            # May fail if external_id already exists; try to get existing txn
            r_list = client.get(f"{API_PREFIX}/transactions", headers=headers, params={"page": 1, "page_size": 1})
            if r_list.status_code == 200 and r_list.json().get("items"):
                txn = r_list.json()["items"][0]
                txn_id = txn["id"]
                print(f"  [OK] Using existing transaction: {txn_id}")
            else:
                print(f"  [X] Ingest failed: {r.status_code} - {r.text[:200]}")
                return 1
        else:
            txn = r.json()
            txn_id = txn["id"]
            print(f"  [OK] Transaction ingested: {txn_id}")
            print(f"    Amount: ${txn['amount']} {txn['currency']}, IP: {txn.get('ip_address', 'N/A')}")

        # Step 4: Run ML pipeline (risk scoring)
        print_step(
            4,
            "ML pipeline scores the transaction",
            "Rules engine + fraud classifier + anomaly detector + behavioral profiler",
        )
        r = client.post(f"{API_PREFIX}/risk/transactions/{txn_id}/score", headers=headers)
        if r.status_code != 200:
            print(f"  [X] Scoring failed: {r.status_code}")
            return 1
        result = r.json()
        score = result.get("overall_score", 0)
        level = result.get("risk_level", "unknown")
        factors = result.get("risk_factors", [])
        print(f"  [OK] Risk score: {score:.1%} ({level})")
        if factors:
            print("    Risk factors:")
            for f in factors[:5]:
                print(f"      - {f}")
        if result.get("explanation", {}).get("summary"):
            print(f"    Summary: {result['explanation']['summary']}")

        # Step 5: View fraud alerts
        print_step(5, "View fraud alerts", "Alerts are created when risk exceeds thresholds")
        r = client.get(f"{API_PREFIX}/alerts", headers=headers, params={"page": 1, "page_size": 3, "status": "open"})
        if r.status_code == 200:
            alerts = r.json().get("items", [])
            if alerts:
                a = alerts[0]
                print(f"  [OK] Sample alert: {a['title']}")
                print(f"    Severity: {a['severity']}, Status: {a['status']}")
                alert_id = a["id"]
            else:
                r_all = client.get(f"{API_PREFIX}/alerts", headers=headers, params={"page": 1, "page_size": 1})
                if r_all.status_code == 200 and r_all.json().get("items"):
                    alert_id = r_all.json()["items"][0]["id"]
                    print(f"  [OK] Using alert: {alert_id}")
                else:
                    alert_id = None
                    print("  (No alerts in DB - seed data may have been cleared)")
        else:
            alert_id = None
            print(f"  [X] List alerts failed: {r.status_code}")

        # Step 6: Create case from alert
        if alert_id:
            print_step(6, "Create investigation case from alert", "Analyst escalates to formal case")
            r = client.post(f"{API_PREFIX}/alerts/{alert_id}/create-case", headers=headers)
            if r.status_code in (200, 201):
                case = r.json()
                print(f"  [OK] Case created: {case.get('case_number', case['id'])}")
                print(f"    Title: {case.get('title', '')[:50]}...")
            else:
                print(f"  [X] Create case failed: {r.status_code} - {r.text[:150]}")

        # Step 7: Dashboard analytics
        print_step(7, "Dashboard analytics", "Overview metrics and fraud trends")
        r = client.get(f"{API_PREFIX}/analytics/overview", headers=headers)
        if r.status_code == 200:
            ov = r.json()
            print(f"  [OK] Total transactions: {ov.get('total_transactions', 'N/A')}")
            print(f"  [OK] Total fraud alerts: {ov.get('total_alerts', 'N/A')}")
            print(f"  [OK] Total cases: {ov.get('total_cases', 'N/A')}")
            print(f"  [OK] Fraud rate: {ov.get('fraud_rate', 0):.2%}")
        else:
            print(f"  [X] Overview failed: {r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/fraud-trends", headers=headers, params={"period": "7d"})
        if r.status_code == 200:
            data = r.json()
            points = data.get("data_points", [])
            if points:
                print(f"  [OK] Fraud trend data: {len(points)} data points")
        else:
            print(f"  [X] Fraud trends failed: {r.status_code}")

        # Step 8: Top risk entities
        print_step(8, "Top risk entities", "Entities with highest fraud risk scores")
        r = client.get(f"{API_PREFIX}/risk/top-risk", headers=headers, params={"limit": 3})
        if r.status_code == 200:
            top = r.json()
            for i, e in enumerate(top[:3], 1):
                print(f"  {i}. {e.get('entity_name', 'N/A')} - Score: {e.get('risk_score', 0):.2f}")
        else:
            print(f"  [X] Top risk failed: {r.status_code}")

    print_section("Demo Complete")
    print("\nHow FinShield AI helps:")
    print("  • Real-time transaction ingestion and ML-based risk scoring")
    print("  • Rules engine + behavioral profiling + anomaly detection")
    print("  • Automated alert creation when risk exceeds thresholds")
    print("  • Case management for investigator workflow")
    print("  • Analytics dashboard for trends and top-risk entities")
    print("  • Network analysis to detect fraud rings")
    print("\nNext: Open http://localhost:3000 to use the full UI.")
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.ConnectError:
        print("\n  [X] Cannot connect to backend. Start it with:")
        print("    poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [X] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
