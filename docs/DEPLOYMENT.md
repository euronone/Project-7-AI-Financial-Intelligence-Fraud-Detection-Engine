# Deployment Guide — FinShield AI

## Prerequisites

| Requirement | Version |
|---|---|
| Azure Subscription | Active with Contributor role |
| Azure CLI | >= 2.50 |
| Terraform | >= 1.5 |
| Docker Desktop | Latest stable |
| Node.js | >= 20 |
| Python | 3.12 |
| Poetry | >= 1.7 |
| GitHub Account | With Actions enabled |

---

## Quick Start (Local Development)

### 1. Clone the Repository

```bash
git clone <repo-url>
cd Project-7-AI-Financial-Intelligence-Fraud-Detection-Engine
```

### 2. Start Infrastructure Services

```bash
docker compose up -d
```

This starts PostgreSQL 16, Redis 7, and MailHog (SMTP testing).

### 3. Backend Setup

```bash
cd backend
cp .env.example .env
poetry install
poetry run alembic upgrade head
poetry run python scripts/seed_data.py
poetry run uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

Open a new terminal:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### 5. Access Points

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| MailHog UI | http://localhost:8025 |

### 6. Default Credentials

| Field | Value |
|---|---|
| Email | `admin@finshield.dev` |
| Password | `Admin123!@#` |

---

## Azure Deployment

### Step 1 — Bootstrap Azure Resources

Run the one-time subscription bootstrap script. This creates the resource group, storage account for Terraform state, and service principal for CI/CD.

```bash
cd infrastructure/scripts
chmod +x setup-azure.sh
./setup-azure.sh
```

The script outputs values you will store as GitHub Actions secrets.

### Step 2 — Initialize Terraform Backend

```bash
./init-terraform.sh --environment dev
```

This configures the remote state backend in Azure Storage.

### Step 3 — Plan Infrastructure

```bash
cd ../terraform
terraform plan -var-file=environments/dev.tfvars
```

Review the plan output to verify all resources (VNet, PostgreSQL, Redis, Container Apps Environment, Key Vault, ACR, Event Hubs, monitoring).

### Step 4 — Apply Infrastructure

```bash
terraform apply -var-file=environments/dev.tfvars
```

Terraform provisions the full Azure topology described in the architecture docs.

### Step 5 — Push Container Images to ACR

```bash
# Log in to Azure Container Registry
az acr login --name finshieldacrdev

# Build and push backend image
docker build -t finshieldacrdev.azurecr.io/backend-api:latest ./backend
docker push finshieldacrdev.azurecr.io/backend-api:latest

# Build and push frontend image
docker build -t finshieldacrdev.azurecr.io/frontend:latest ./frontend
docker push finshieldacrdev.azurecr.io/frontend:latest
```

### Step 6 — Deploy to Container Apps

```bash
# Deploy backend API
az containerapp update \
  --name finshield-dev-api \
  --resource-group finshield-dev-rg \
  --image finshieldacrdev.azurecr.io/backend-api:latest

# Deploy frontend
az containerapp update \
  --name finshield-dev-frontend \
  --resource-group finshield-dev-rg \
  --image finshieldacrdev.azurecr.io/frontend:latest

# Run migrations against Azure PostgreSQL
az containerapp exec \
  --name finshield-dev-api \
  --resource-group finshield-dev-rg \
  --command "alembic upgrade head"
```

---

## CI/CD Pipeline

### Overview

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | Pull request | Lint, type-check, test (backend + frontend) |
| `cd-staging.yml` | Push to `main` | Build images, deploy to staging, smoke tests |
| `cd-production.yml` | Manual dispatch | Blue-green deploy to production with approval gate |
| `infrastructure.yml` | Push to `main` (paths: `infrastructure/**`) | Terraform plan/apply |
| `ml-pipeline.yml` | Manual / weekly schedule | Model training, evaluation, registry |
| `security-scan.yml` | Push to `main` | Dependency audit, SAST, secret detection |

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `AZURE_CLIENT_ID` | Service principal app ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Target subscription |
| `ACR_LOGIN_SERVER` | e.g. `finshieldacrdev.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |

### CI Pipeline (`ci.yml`)

Runs on every pull request:

1. **Frontend checks** — `npm ci`, ESLint, `tsc --noEmit`, Vitest, `next build`
2. **Backend checks** — `poetry install`, `ruff check`, `ruff format --check`, `mypy`, `pytest` (unit + integration with service containers for Postgres and Redis)
3. **Security scan** — `npm audit`, `pip-audit`, Semgrep, Gitleaks

### CD Staging (`cd-staging.yml`)

On merge to `main`:

1. Build and push Docker images tagged with commit SHA
2. Run Trivy container vulnerability scan
3. Deploy new revisions to staging Container Apps
4. Run `alembic upgrade head` on staging database
5. Execute smoke tests against staging endpoints
6. Post result to Slack

### CD Production (`cd-production.yml`)

Manual trigger with GitHub Environment approval:

1. **Blue-green deployment**: deploy new revision at 0 % traffic
2. Health check the new revision
3. Shift 10 % traffic; monitor error rates for 5 minutes
4. If error rate < 0.1 %: shift to 100 % and deactivate old revision
5. If error rate >= 0.1 %: rollback to previous revision
6. Run database migrations
7. Invalidate CDN cache on Azure Front Door
8. Tag the release in Git

---

## Environment Variables

### Backend

| Variable | Description | Example |
|---|---|---|
| `APP_ENV` | Runtime environment | `development` / `staging` / `production` |
| `DEBUG` | Enable debug mode | `true` / `false` |
| `LOG_LEVEL` | Structlog log level | `DEBUG` / `INFO` / `WARNING` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `JWT_SECRET` | Secret for signing JWTs | (Key Vault in production) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON list) | `["https://app.finshield.com"]` |
| `RATE_LIMIT_AUTH` | Requests per minute for auth routes | `100` |
| `RATE_LIMIT_DATA` | Requests per minute for data routes | `1000` |
| `ML_MODEL_PATH` | Path to serialized ONNX models | `app/ml/models` |
| `ML_FRAUD_MODEL_VERSION` | Active model version tag | `latest` |
| `EVENT_HUB_CONNECTION_STRING` | Azure Event Hub connection | (Key Vault) |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob storage connection | (Key Vault) |
| `SMTP_HOST` | SMTP mail host | `localhost` |
| `SMTP_PORT` | SMTP mail port | `1025` |

### Frontend

| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_WS_URL` | WebSocket server URL | `http://localhost:8000` |
| `NEXTAUTH_URL` | NextAuth canonical URL | `http://localhost:3000` |
| `NEXTAUTH_SECRET` | NextAuth encryption secret | (Key Vault) |
| `AZURE_AD_CLIENT_ID` | Azure AD app client ID | (Key Vault) |
| `AZURE_AD_CLIENT_SECRET` | Azure AD app secret | (Key Vault) |

---

## Monitoring

### Application Insights

All backend services emit structured logs and traces to Azure Application Insights via the OpenTelemetry SDK.

Key dashboards:

- **Request performance** — latency percentiles, throughput, failure rate
- **Dependency tracking** — PostgreSQL, Redis, Event Hub call durations
- **Custom metrics** — transactions processed/sec, fraud detection rate, model inference latency
- **Live Metrics Stream** — real-time request/failure/dependency view

### Log Analytics

Structured JSON logs are forwarded to an Azure Log Analytics workspace. Useful KQL queries:

```kql
// Requests slower than 500ms
AppRequests
| where DurationMs > 500
| project TimeGenerated, Name, DurationMs, ResultCode

// Fraud score distribution (last 24h)
customMetrics
| where name == "fraud_score"
| where timestamp > ago(24h)
| summarize avg(value), percentile(value, 95) by bin(timestamp, 1h)
```

### Alert Rules

| Alert | Condition | Severity |
|---|---|---|
| High error rate | Error rate > 1 % over 5 min | Critical |
| High latency | P95 > 500 ms over 5 min | Warning |
| Container restart loop | > 3 restarts in 10 min | Critical |
| Database CPU | CPU > 80 % for 10 min | Warning |
| Redis memory | Memory > 80 % | Warning |
| Fraud rate anomaly | Fraud rate > 2× 7-day average | Warning |

---

## Security Checklist

### Secrets Management

- [ ] All secrets stored in Azure Key Vault
- [ ] Managed identities used for service-to-service auth (no stored credentials)
- [ ] Key Vault access policies scoped to individual managed identities
- [ ] Secret rotation schedule documented and automated (90-day cycle)

### Network

- [ ] VNet integration enabled for all Container Apps
- [ ] Private endpoints for PostgreSQL, Redis, and Storage
- [ ] NSG rules restrict traffic to required ports only
- [ ] Azure Front Door WAF enabled with OWASP 3.2 rule set

### Application

- [ ] CORS origins restricted to frontend domain only
- [ ] CSP headers applied via `SecurityHeadersMiddleware`
- [ ] HSTS enabled in production
- [ ] Rate limiting on auth (100 req/min) and data (1000 req/min) endpoints
- [ ] PII masked in all log output via `pii_masker.mask_dict()`
- [ ] Input validation on every endpoint (Pydantic schemas)
- [ ] RBAC enforced on all protected resources

### CI/CD

- [ ] Dependency vulnerability scanning (Dependabot, pip-audit, npm audit)
- [ ] Container image scanning (Trivy)
- [ ] SAST scanning (Semgrep)
- [ ] Secret detection (Gitleaks)
- [ ] Production deploys require manual approval

---

## Troubleshooting

### Backend won't start

**Symptom:** `ConnectionRefusedError` on startup.

**Cause:** PostgreSQL or Redis not running.

**Fix:**

```bash
docker compose up -d
docker compose ps   # verify all services are healthy
```

### Database migrations fail

**Symptom:** `alembic upgrade head` exits with an error.

**Fix:**

```bash
# Check current migration head
poetry run alembic current

# If the database is out of sync, stamp the current state
poetry run alembic stamp head

# Then re-run
poetry run alembic upgrade head
```

### Frontend can't reach backend API

**Symptom:** Network errors or CORS failures in the browser console.

**Cause:** Backend not running, or `NEXT_PUBLIC_API_URL` misconfigured.

**Fix:**

1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
3. Verify `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000`

### Container App not responding after deploy

**Symptom:** 502 or 503 from Azure Front Door.

**Fix:**

```bash
# Check container logs
az containerapp logs show \
  --name finshield-dev-api \
  --resource-group finshield-dev-rg \
  --follow

# Check revision status
az containerapp revision list \
  --name finshield-dev-api \
  --resource-group finshield-dev-rg \
  -o table
```

### Redis connection timeout

**Symptom:** `ConnectionError: Error connecting to Redis` in logs.

**Fix (local):** Restart the Redis container: `docker compose restart redis`

**Fix (Azure):** Verify the private endpoint is healthy and the connection string in Key Vault is correct.

### ML model inference errors

**Symptom:** `ONNXRuntimeError` or `FileNotFoundError` for model artifacts.

**Fix:**

1. Verify model files exist at the path specified by `ML_MODEL_PATH`
2. For Azure deployments, ensure the Blob Storage container `ml-models` has the expected ONNX files
3. Check that `ML_FRAUD_MODEL_VERSION` matches an available model version in the registry

### High fraud alert volume (false positives)

**Fix:**

1. Review rule hit rates at `/api/v1/rules/{id}/performance`
2. Disable or tune overly aggressive rules
3. Check model drift — retrain if precision has dropped
4. Adjust risk score thresholds in system settings
