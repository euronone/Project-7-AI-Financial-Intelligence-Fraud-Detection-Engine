# FinShield AI - Testing & Demo Guide

This document describes how to test all features and run the fraud detection demo.

## Prerequisites

1. **Docker** running (Postgres, Redis, MailHog):
   ```bash
   docker compose up -d
   ```

2. **Database** migrated and seeded:
   ```bash
   cd backend
   poetry run alembic upgrade head
   poetry run python scripts/seed_data.py
   poetry run python scripts/seed_trend_scenario.py   # Adds trend data for dashboard chart
   ```

3. **Backend** running:
   ```bash
   cd backend
   poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

---

## 1. Full API Test Suite

Runs automated tests against **every major API endpoint** (50+ checks).

```bash
cd backend
poetry run python scripts/run_full_test_suite.py
```

### What it tests

| Category | Endpoints |
|----------|-----------|
| **Authentication** | Login, Get current user |
| **Health** | Health check |
| **Transactions** | List, Get detail |
| **Entities** | List, Get 360 view |
| **Watchlists** | List entries |
| **Rules Engine** | List rules, Get rule, Templates |
| **ML Models** | List models, Get model |
| **Risk Scoring** | Distribution, Top risk, Score transaction |
| **Fraud Alerts** | List, Statistics, Get, Update status |
| **Case Management** | List, Statistics |
| **Analytics** | Overview, Fraud trends, Volume, Risk dist, Patterns, Geo, Model perf |
| **Network Analysis** | Graph |
| **Audit** | Logs, Notifications |
| **Webhooks** | List |
| **Settings** | System, Team |
| **Users** | List (admin) |

### Expected output

```
============================================================
FinShield AI - Full API Test Suite
============================================================

[1] Authentication
  ✓ Login
  ✓ Get current user (me)

[2] Health
  ✓ Health check
...
============================================================
Results: 50 passed, 0 failed
============================================================
```

---

## 2. Fraud Detection Demo

Demonstrates **how the platform works** with a realistic scenario.

```bash
cd backend
poetry run python scripts/demo_fraud_scenario.py
```

### Demo flow

1. **Analyst logs in** – Uses `analyst1@finshield.dev` (role: analyst)
2. **Fetch entities** – Gets source/destination for a transaction
3. **Ingest suspicious transaction** – $15,000 payment, foreign IP (Nigeria), online channel
4. **ML pipeline scores** – Rules + fraud classifier + anomaly detector + behavioral profiler
5. **View fraud alerts** – Alerts created when risk exceeds thresholds
6. **Create case** – Escalate alert to formal investigation case
7. **Dashboard analytics** – Overview stats, fraud trends
8. **Top risk entities** – Entities with highest fraud scores

### What it showcases

- **Real-time ingestion** – Transaction data flows into the system
- **ML-based scoring** – Multiple models produce a risk score and factors
- **Alert workflow** – High-risk transactions surface as alerts
- **Case management** – Analysts create and track investigations
- **Analytics** – Trends, patterns, and top-risk entities

### Sample output

```
============================================================
  FinShield AI - Fraud Detection Demo
============================================================

--- Step 1: Analyst logs in ---
  ✓ Logged in as Alice Analyst (analyst)

--- Step 2: Fetch entities for transaction ---
  ✓ Source entity: James Smith (individual)
  ✓ Destination: Mary Johnson

--- Step 3: Ingest suspicious transaction ---
  ✓ Transaction ingested: abc123...
    Amount: $15000.0 USD, IP: 41.203.123.45

--- Step 4: ML pipeline scores the transaction ---
  ✓ Risk score: 72.3% (high)
    Risk factors:
      - High amount for channel
      - Unusual geographic location
      ...
```

---

## 3. Pytest Unit Tests

For unit-level tests (auth, permissions):

```bash
cd backend
poetry run pytest tests/ -v
```

Requires a test database. The `test_auth.py` tests authentication and authorization.

---

## 4. Load Testing (Locust)

For performance testing:

```bash
cd backend
poetry run locust -f tests/load/locustfile.py --host=http://127.0.0.1:8000
```

Then open http://localhost:8089 and configure the load test.

---

## Test Credentials (from seed)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@finshield.dev | Admin123!@# |
| Analyst | analyst1@finshield.dev | Admin123!@# |
| Investigator | investigator1@finshield.dev | Admin123!@# |
| Viewer | viewer1@finshield.dev | Admin123!@# |

---

## Quick Start (all-in-one)

```bash
# Terminal 1: Infrastructure
docker compose up -d

# Terminal 2: Backend
cd backend
poetry run alembic upgrade head
poetry run python scripts/seed_data.py
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 3: Run tests & demo
cd backend
poetry run python scripts/run_full_test_suite.py
poetry run python scripts/demo_fraud_scenario.py
```

---

## Frontend Manual Testing

1. Start frontend: `cd frontend && npm run dev`
2. Open http://localhost:3000
3. Login with `admin@finshield.dev` / `Admin123!@#`
4. Navigate through: Dashboard, Transactions, Entities, Fraud Alerts, Case Management, Rules, ML Models, Analytics, Network Graph, Settings
