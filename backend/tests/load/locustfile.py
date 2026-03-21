"""
FinShield AI — Locust load test suite.

Target: 1 000 TPS sustained with < 200 ms P95 across all endpoints.

Usage:
    locust -f backend/tests/load/locustfile.py --host http://localhost:9000
    locust -f backend/tests/load/locustfile.py --host http://localhost:9000 \
           --headless -u 200 -r 20 --run-time 5m
"""

from __future__ import annotations

import logging
import os
import random
import string
import uuid

from locust import HttpUser, between, events, task

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"
AUTH_EMAIL = os.getenv("FINSHIELD_TEST_EMAIL", "admin@finshield.local")
AUTH_PASSWORD = os.getenv("FINSHIELD_TEST_PASSWORD", "Admin123!@#")

# ── Realistic data generators ──────────────────────────────────────────────

CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SGD"]
CHANNELS = ["online", "pos", "atm", "mobile", "wire", "ach"]
TXN_TYPES = ["payment", "transfer", "withdrawal", "deposit", "refund"]
COUNTRIES = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "SG", "BR", "IN", "NG", "AE"]
MCC_CODES = ["5411", "5912", "5541", "5812", "5999", "7011", "4812", "5311", "5944", "5621"]
FIRST_NAMES = ["James", "Maria", "Chen", "Aisha", "Carlos", "Yuki", "Olga", "Ahmed", "Priya", "Lars"]
LAST_NAMES = ["Smith", "Garcia", "Wang", "Okafor", "Mueller", "Tanaka", "Petrov", "Khan", "Patel", "Andersen"]
ENTITY_TYPES = ["individual", "business", "merchant"]
ALERT_STATUSES = ["investigating", "escalated", "resolved_fraud", "resolved_false_positive", "dismissed"]


def _rand_ip() -> str:
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _rand_device_fp() -> str:
    return "".join(random.choices(string.hexdigits.lower(), k=32))


def _rand_amount() -> float:
    """Realistic transaction amounts: mostly small, occasional large."""
    r = random.random()
    if r < 0.60:
        return round(random.uniform(5.0, 150.0), 2)
    if r < 0.85:
        return round(random.uniform(150.0, 2_000.0), 2)
    if r < 0.97:
        return round(random.uniform(2_000.0, 25_000.0), 2)
    return round(random.uniform(25_000.0, 500_000.0), 2)


def _rand_coords(country: str) -> tuple[float, float]:
    coords = {
        "US": (38.0, -97.0), "GB": (54.0, -2.0), "DE": (51.0, 10.0),
        "FR": (46.0, 2.0), "CA": (56.0, -106.0), "AU": (-25.0, 134.0),
        "JP": (36.0, 138.0), "SG": (1.35, 103.8), "BR": (-14.0, -51.0),
        "IN": (20.0, 77.0), "NG": (9.0, 8.0), "AE": (24.0, 54.0),
    }
    base_lat, base_lng = coords.get(country, (40.0, -74.0))
    return (
        round(base_lat + random.uniform(-3.0, 3.0), 7),
        round(base_lng + random.uniform(-3.0, 3.0), 7),
    )


def build_transaction_payload() -> dict:
    country = random.choice(COUNTRIES)
    lat, lng = _rand_coords(country)
    return {
        "external_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
        "source_entity_id": str(uuid.uuid4()),
        "destination_entity_id": str(uuid.uuid4()) if random.random() > 0.2 else None,
        "amount": _rand_amount(),
        "currency": random.choice(CURRENCIES),
        "transaction_type": random.choice(TXN_TYPES),
        "channel": random.choice(CHANNELS),
        "merchant_category_code": random.choice(MCC_CODES),
        "description": f"Load-test txn {uuid.uuid4().hex[:8]}",
        "ip_address": _rand_ip(),
        "device_fingerprint": _rand_device_fp(),
        "geolocation_lat": lat,
        "geolocation_lng": lng,
        "country_code": country,
        "card_present": random.choice([True, False]),
    }


# ── Auth mixin ──────────────────────────────────────────────────────────────

class LoginMixin:
    """Authenticates on start and injects Authorization header."""

    _token: str | None = None

    def login(self):
        resp = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
            name="POST /auth/login",
        )
        if resp.status_code == 200:
            data = resp.json()
            self._token = data.get("access_token") or data.get("token")
            if self._token:
                self.client.headers.update({"Authorization": f"Bearer {self._token}"})
        else:
            logger.warning("Login failed: %s %s", resp.status_code, resp.text[:200])

    def on_start(self):
        self.login()


# ── User classes ────────────────────────────────────────────────────────────

class HealthCheckUser(LoginMixin, HttpUser):
    weight = 1
    wait_time = between(1, 3)

    @task
    def health(self):
        self.client.get(f"{API_PREFIX}/health", name="GET /health")


class TransactionUser(LoginMixin, HttpUser):
    weight = 5
    wait_time = between(1, 3)
    _known_ids: list[str]

    def on_start(self):
        super().on_start()
        self._known_ids = []

    @task(5)
    def list_transactions(self):
        page = random.randint(1, 5)
        resp = self.client.get(
            f"{API_PREFIX}/transactions",
            params={"page": page, "page_size": 20},
            name="GET /transactions",
        )
        if resp.status_code == 200:
            items = resp.json().get("items") or resp.json().get("data") or []
            for item in items[:5]:
                if "id" in item:
                    self._known_ids.append(item["id"])
            if len(self._known_ids) > 50:
                self._known_ids = self._known_ids[-50:]

    @task(3)
    def get_transaction(self):
        if not self._known_ids:
            return
        txn_id = random.choice(self._known_ids)
        self.client.get(
            f"{API_PREFIX}/transactions/{txn_id}",
            name="GET /transactions/:id",
        )

    @task(2)
    def ingest_transaction(self):
        self.client.post(
            f"{API_PREFIX}/transactions/ingest",
            json=build_transaction_payload(),
            name="POST /transactions/ingest",
        )


class AlertUser(LoginMixin, HttpUser):
    weight = 3
    wait_time = between(1, 3)
    _known_alert_ids: list[str]

    def on_start(self):
        super().on_start()
        self._known_alert_ids = []

    @task(5)
    def list_alerts(self):
        resp = self.client.get(
            f"{API_PREFIX}/alerts",
            params={"page": 1, "page_size": 20},
            name="GET /alerts",
        )
        if resp.status_code == 200:
            items = resp.json().get("items") or resp.json().get("data") or []
            for item in items[:5]:
                if "id" in item:
                    self._known_alert_ids.append(item["id"])
            if len(self._known_alert_ids) > 50:
                self._known_alert_ids = self._known_alert_ids[-50:]

    @task(3)
    def alert_statistics(self):
        self.client.get(
            f"{API_PREFIX}/alerts/statistics",
            name="GET /alerts/statistics",
        )

    @task(1)
    def update_alert_status(self):
        if not self._known_alert_ids:
            return
        alert_id = random.choice(self._known_alert_ids)
        self.client.patch(
            f"{API_PREFIX}/alerts/{alert_id}/status",
            json={"status": random.choice(ALERT_STATUSES)},
            name="PATCH /alerts/:id/status",
        )


class AnalyticsUser(LoginMixin, HttpUser):
    weight = 2
    wait_time = between(1, 3)

    @task(3)
    def overview(self):
        self.client.get(
            f"{API_PREFIX}/analytics/overview",
            name="GET /analytics/overview",
        )

    @task(3)
    def fraud_trends(self):
        period = random.choice(["7d", "30d", "90d"])
        self.client.get(
            f"{API_PREFIX}/analytics/fraud-trends",
            params={"period": period},
            name="GET /analytics/fraud-trends",
        )

    @task(2)
    def risk_distribution(self):
        self.client.get(
            f"{API_PREFIX}/analytics/risk-distribution",
            name="GET /analytics/risk-distribution",
        )


class EntityUser(LoginMixin, HttpUser):
    weight = 2
    wait_time = between(1, 3)

    @task(5)
    def list_entities(self):
        self.client.get(
            f"{API_PREFIX}/entities",
            params={"page": 1, "page_size": 20},
            name="GET /entities",
        )

    @task(3)
    def search_entities(self):
        name = random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)
        self.client.get(
            f"{API_PREFIX}/entities",
            params={"search": name, "page": 1, "page_size": 10},
            name="GET /entities?search=...",
        )


class RulesUser(LoginMixin, HttpUser):
    weight = 1
    wait_time = between(1, 3)

    @task(5)
    def list_rules(self):
        self.client.get(f"{API_PREFIX}/rules", name="GET /rules")

    @task(3)
    def rule_templates(self):
        self.client.get(f"{API_PREFIX}/rules/templates", name="GET /rules/templates")


# ── Event hooks — percentile report ────────────────────────────────────────

_PERCENTILES = [0.50, 0.75, 0.90, 0.95, 0.99]


@events.quitting.add_listener
def _print_percentiles(environment, **_kwargs):
    """Print P50–P99 response times when Locust finishes."""
    stats = environment.runner.stats
    print("\n" + "=" * 80)
    print("  FinShield Load Test — Percentile Report")
    print("=" * 80)
    print(f"  {'Endpoint':<40} {'P50':>7} {'P75':>7} {'P90':>7} {'P95':>7} {'P99':>7}  {'Reqs':>7}")
    print("-" * 80)

    for entry in sorted(stats.entries.values(), key=lambda e: e.name):
        if entry.num_requests == 0:
            continue
        pcts = entry.percentile()
        vals = [pcts.get(p, 0) for p in _PERCENTILES]
        label = f"{entry.method} {entry.name}" if entry.method else entry.name
        print(f"  {label:<40} {vals[0]:>6.0f}ms {vals[1]:>6.0f}ms {vals[2]:>6.0f}ms {vals[3]:>6.0f}ms {vals[4]:>6.0f}ms {entry.num_requests:>7}")

    total = stats.total
    if total.num_requests > 0:
        pcts = total.percentile()
        vals = [pcts.get(p, 0) for p in _PERCENTILES]
        print("-" * 80)
        print(f"  {'TOTAL':<40} {vals[0]:>6.0f}ms {vals[1]:>6.0f}ms {vals[2]:>6.0f}ms {vals[3]:>6.0f}ms {vals[4]:>6.0f}ms {total.num_requests:>7}")

    p95 = total.percentile().get(0.95, 0) if total.num_requests else 0
    target = 200
    status = "PASS" if p95 <= target else "FAIL"
    print(f"\n  P95 = {p95:.0f} ms  (target: <{target} ms)  [{status}]")
    print("=" * 80 + "\n")
