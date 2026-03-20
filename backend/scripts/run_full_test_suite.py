#!/usr/bin/env python3
"""
Comprehensive API test suite for FinShield AI.
Tests every major feature/endpoint of the platform.

Prerequisites:
  - Backend running: poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
  - Database seeded: poetry run python scripts/seed_data.py

Usage: poetry run python scripts/run_full_test_suite.py
       or: python scripts/run_full_test_suite.py (from backend dir)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
LOGIN_EMAIL = "admin@finshield.dev"
LOGIN_PASSWORD = "Admin123!@#"

passed = 0
failed = 0
errors = []


def ok(name: str):
    global passed
    passed += 1
    print(f"  [PASS] {name}")


def fail(name: str, msg: str):
    global failed, errors
    failed += 1
    errors.append((name, msg))
    print(f"  [FAIL] {name}: {msg}")


def run_tests():
    global passed, failed
    print("\n" + "=" * 60)
    print("FinShield AI - Full API Test Suite")
    print("=" * 60)

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # --- Auth ---
        print("\n[1] Authentication")
        r = client.post(f"{API_PREFIX}/auth/login", json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD})
        if r.status_code != 200:
            fail("Login", f"status={r.status_code}, body={r.text[:200]}")
            print("\n  Cannot continue without auth. Ensure backend is running and DB is seeded.")
            return
        ok("Login")
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = client.get(f"{API_PREFIX}/auth/me", headers=headers)
        if r.status_code == 200:
            ok("Get current user (me)")
        else:
            fail("Get me", f"status={r.status_code}")

        # --- Health ---
        print("\n[2] Health")
        r = client.get(f"{API_PREFIX}/health")
        if r.status_code == 200:
            ok("Health check")
        else:
            fail("Health", f"status={r.status_code}")

        # --- Transactions ---
        print("\n[3] Transactions")
        r = client.get(f"{API_PREFIX}/transactions", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            data = r.json()
            if "items" in data and "total" in data:
                ok("List transactions")
            else:
                fail("List transactions", "unexpected response shape")
        else:
            fail("List transactions", f"status={r.status_code}")

        if r.status_code == 200 and data.get("items"):
            txn_id = data["items"][0]["id"]
            r2 = client.get(f"{API_PREFIX}/transactions/{txn_id}", headers=headers)
            if r2.status_code == 200:
                ok("Get transaction detail")
            else:
                fail("Get transaction", f"status={r2.status_code}")

        # --- Entities ---
        print("\n[4] Entities")
        r = client.get(f"{API_PREFIX}/entities", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            data = r.json()
            if "items" in data:
                ok("List entities")
                if data["items"]:
                    ent_id = data["items"][0]["id"]
                    r2 = client.get(f"{API_PREFIX}/entities/{ent_id}", headers=headers)
                    if r2.status_code == 200:
                        ok("Get entity 360 view")
                    else:
                        fail("Get entity", f"status={r2.status_code}")
            else:
                fail("List entities", "no items")
        else:
            fail("List entities", f"status={r.status_code}")

        # --- Watchlists ---
        print("\n[5] Watchlists")
        r = client.get(f"{API_PREFIX}/watchlists", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("List watchlist entries")
        else:
            fail("List watchlists", f"status={r.status_code}")

        # --- Rules Engine ---
        print("\n[6] Rules Engine")
        r = client.get(f"{API_PREFIX}/rules", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            data = r.json()
            ok("List rules")
            if data.get("items"):
                rule_id = data["items"][0]["id"]
                r2 = client.get(f"{API_PREFIX}/rules/{rule_id}", headers=headers)
                if r2.status_code == 200:
                    ok("Get rule detail")
                r3 = client.get(f"{API_PREFIX}/rules/templates", headers=headers)
                if r3.status_code == 200:
                    ok("Get rule templates")
        else:
            fail("List rules", f"status={r.status_code}")

        # --- ML Models ---
        print("\n[7] ML Models")
        r = client.get(f"{API_PREFIX}/models", headers=headers)
        if r.status_code == 200:
            ok("List ML models")
            data = r.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            if items:
                model_id = items[0]["id"]
                r2 = client.get(f"{API_PREFIX}/models/{model_id}", headers=headers)
                if r2.status_code == 200:
                    ok("Get model detail")
        else:
            fail("List models", f"status={r.status_code}")

        # --- Risk Scoring ---
        print("\n[8] Risk Scoring")
        r = client.get(f"{API_PREFIX}/risk/distribution", headers=headers)
        if r.status_code == 200:
            ok("Risk distribution")
        else:
            fail("Risk distribution", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/risk/top-risk", headers=headers, params={"limit": 5})
        if r.status_code == 200:
            ok("Top risk entities")
        else:
            fail("Top risk", f"status={r.status_code}")

        # Score a transaction (need txn + entity from seed)
        r_txn = client.get(f"{API_PREFIX}/transactions", headers=headers, params={"page": 1, "page_size": 1})
        if r_txn.status_code == 200 and r_txn.json().get("items"):
            txn_id = r_txn.json()["items"][0]["id"]
            r = client.post(f"{API_PREFIX}/risk/transactions/{txn_id}/score", headers=headers)
            if r.status_code == 200:
                ok("Score transaction (ML pipeline)")
            else:
                fail("Score transaction", f"status={r.status_code}")

        # --- Fraud Alerts ---
        print("\n[9] Fraud Alerts")
        r = client.get(f"{API_PREFIX}/alerts", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("List fraud alerts")
        else:
            fail("List alerts", f"status={r.status_code}")

        r = client.get("/alerts/statistics", headers=headers)
        if r.status_code == 200:
            ok("Alert statistics")
        else:
            fail("Alert stats", f"status={r.status_code}")

        if r.status_code == 200:
            r_alerts = client.get(f"{API_PREFIX}/alerts", headers=headers, params={"page": 1, "page_size": 1})
            if r_alerts.status_code == 200 and r_alerts.json().get("items"):
                alert_id = r_alerts.json()["items"][0]["id"]
                r2 = client.get(f"{API_PREFIX}/alerts/{alert_id}", headers=headers)
                if r2.status_code == 200:
                    ok("Get alert detail")
                r3 = client.patch(
                    f"{API_PREFIX}/alerts/{alert_id}/status",
                    headers=headers,
                    json={"status": "in_review"},
                )
                if r3.status_code == 200:
                    ok("Update alert status")
        else:
            pass  # skip if alerts list failed

        # --- Case Management ---
        print("\n[10] Case Management")
        r = client.get(f"{API_PREFIX}/cases", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("List cases")
        else:
            fail("List cases", f"status={r.status_code}")

        r = client.get("/cases/statistics", headers=headers)
        if r.status_code == 200:
            ok("Case statistics")
        else:
            fail("Case stats", f"status={r.status_code}")

        # --- Analytics ---
        print("\n[11] Analytics & Reporting")
        r = client.get(f"{API_PREFIX}/analytics/overview", headers=headers)
        if r.status_code == 200:
            ok("Overview stats")
        else:
            fail("Overview", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/fraud-trends", headers=headers, params={"period": "30d"})
        if r.status_code == 200:
            ok("Fraud trends")
        else:
            fail("Fraud trends", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/transaction-volume", headers=headers, params={"period": "7d"})
        if r.status_code == 200:
            ok("Transaction volume")
        else:
            fail("Transaction volume", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/risk-distribution", headers=headers)
        if r.status_code == 200:
            ok("Risk distribution")
        else:
            fail("Risk distribution", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/top-patterns", headers=headers)
        if r.status_code == 200:
            ok("Top fraud patterns")
        else:
            fail("Top patterns", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/geographic", headers=headers)
        if r.status_code == 200:
            ok("Geographic data")
        else:
            fail("Geographic", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/analytics/model-performance", headers=headers)
        if r.status_code == 200:
            ok("Model performance")
        else:
            fail("Model performance", f"status={r.status_code}")

        # --- Network Analysis ---
        print("\n[12] Network Analysis")
        r = client.get(f"{API_PREFIX}/network/graph", headers=headers, params={"limit": 50})
        if r.status_code == 200:
            ok("Network graph")
        else:
            fail("Network graph", f"status={r.status_code}")

        # --- Audit & Notifications ---
        print("\n[13] Audit & Notifications")
        r = client.get(f"{API_PREFIX}/audit/logs", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("Audit logs")
        else:
            fail("Audit logs", f"status={r.status_code}")

        r = client.get(f"{API_PREFIX}/audit/notifications", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("Notifications")
        else:
            fail("Notifications", f"status={r.status_code}")

        # --- Webhooks ---
        print("\n[14] Webhooks")
        r = client.get(f"{API_PREFIX}/webhooks", headers=headers)
        if r.status_code == 200:
            ok("List webhooks")
        else:
            fail("List webhooks", f"status={r.status_code}")

        # --- Settings ---
        print("\n[15] Settings")
        r = client.get(f"{API_PREFIX}/settings/system", headers=headers)
        if r.status_code == 200:
            ok("System settings")
        else:
            fail("System settings", f"status={r.status_code}")

        r = client.get("/settings/team", headers=headers)
        if r.status_code == 200:
            ok("Team list")
        else:
            fail("Team list", f"status={r.status_code}")

        # --- Users (admin) ---
        print("\n[16] User Management (Admin)")
        r = client.get(f"{API_PREFIX}/users", headers=headers, params={"page": 1, "page_size": 5})
        if r.status_code == 200:
            ok("List users")
        else:
            fail("List users", f"status={r.status_code}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    if errors:
        print("\nFailed tests:")
        for name, msg in errors:
            print(f"  - {name}: {msg}")
    print()


if __name__ == "__main__":
    try:
        run_tests()
    except httpx.ConnectError as e:
        print("\n  [X] Cannot connect to backend. Is it running on http://127.0.0.1:8000 ?")
        print(f"    {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [X] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    sys.exit(1 if failed > 0 else 0)
