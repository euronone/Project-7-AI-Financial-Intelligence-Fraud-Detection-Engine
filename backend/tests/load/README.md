# FinShield AI — Load Testing

Locust-based load tests targeting the FinShield fraud detection API.

## Setup

```bash
pip install locust
```

## Running

### Web UI (interactive)

```bash
locust -f backend/tests/load/locustfile.py --host http://localhost:9000
```

Open http://localhost:8089 in your browser to configure users, ramp-up, and monitor live metrics.

### Headless (CI / automated)

```bash
locust -f backend/tests/load/locustfile.py \
  --host http://localhost:9000 \
  --headless \
  -u 100 -r 10 \
  --run-time 5m
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `FINSHIELD_TEST_EMAIL` | `admin@finshield.local` | Login email for auth |
| `FINSHIELD_TEST_PASSWORD` | `Admin123!@#` | Login password for auth |

## Scenarios

| User class | Weight | Endpoints |
|---|---|---|
| **HealthCheckUser** | 1 | `GET /health` |
| **TransactionUser** | 5 | List, get, and ingest transactions |
| **AlertUser** | 3 | List alerts, statistics, update status |
| **AnalyticsUser** | 2 | Overview, fraud trends, risk distribution |
| **EntityUser** | 2 | List and search entities |
| **RulesUser** | 1 | List rules, get templates |

All users authenticate via `POST /auth/login` on start and attach a Bearer token.

## Benchmarks

| Metric | Target |
|---|---|
| Sustained throughput | 1 000 TPS |
| P95 response time | < 200 ms |
| P99 response time | < 500 ms |
| Error rate | < 0.1 % |

A percentile summary (P50–P99) prints automatically when the test finishes, along with a PASS/FAIL against the P95 target.
