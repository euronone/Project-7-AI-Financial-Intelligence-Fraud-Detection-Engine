# FinShield AI — Deployment

**Target:** Microsoft Azure  
**Environments:** Development (local), Staging (auto on merge to main), Production (manual + approval)  

This document summarizes the Azure topology, container apps, and CI/CD. Full detail is in CLAUDE.md; IaC lives in `infrastructure/terraform/`. Admin, Analyst web, and Native mobile all consume the same backend; document mobile-specific needs (push, deep links) in API_SPEC and here as needed.

---

## Environment Strategy

| Environment | Purpose | Trigger |
|-------------|---------|---------|
| Development | Local feature development | Manual; docker-compose + backend + frontend |
| Staging | Pre-production validation | Auto on merge to `main` |
| Production | Live system | Manual workflow_dispatch + approval |

---

## Azure Resource Topology (Summary)

- **Resource Group:** finshield-{env}-rg  
- **Networking:** VNet (e.g. 10.0.0.0/16), subnets for container-apps, database, cache, private-endpoints; NSGs; Private DNS.  
- **Compute:** Container Apps Environment; Container Apps: frontend (Next.js), backend-api (FastAPI), backend-worker (Celery), backend-stream (Event Hub consumer). ACR for images.  
- **Data:** PostgreSQL Flexible Server (finshield-{env}-pg); Azure Cache for Redis (finshield-{env}-redis).  
- **Messaging:** Event Hubs namespace (transactions, alerts hubs; consumer groups: fraud-processor, analytics, audit).  
- **Storage:** Storage account (ml-models, reports, exports, terraform-state).  
- **AI/ML:** Azure ML Workspace (model registry, compute for training).  
- **Security:** Key Vault (secrets, managed identities for Container Apps).  
- **Monitoring:** Log Analytics, Application Insights, Azure Monitor alert rules.  
- **CDN/WAF:** Azure Front Door (custom domain in prod, WAF, rate limiting, origins to frontend and backend).

---

## Container Apps (Summary)

| App | Image | Scale | Health | Notes |
|-----|--------|--------|--------|------|
| frontend | finshieldacr.azurecr.io/frontend | min 2, max 10 | /api/health:3000 | Next.js; env from Key Vault (NEXTAUTH_*, AZURE_AD_*) |
| backend-api | finshieldacr.azurecr.io/backend-api | min 2, max 20 | /api/v1/health:8000 | FastAPI; DATABASE_URL, REDIS_URL, JWT, EVENT_HUB, STORAGE, ML_MODEL_PATH |
| backend-worker | finshieldacr.azurecr.io/backend-worker | min 2, max 10 | Celery | Same env as backend-api |
| backend-stream | finshieldacr.azurecr.io/backend-stream | min 2, max 10 | — | Event Hub consumer; same env as backend-api |

---

## CI/CD (GitHub Actions)

- **ci.yml (PR):** Frontend (lint, typecheck, unit, build, E2E); Backend (ruff, mypy, pytest unit + integration); Security (audit, SAST, secrets).  
- **cd-staging.yml (merge to main):** Build and push images to ACR; Trivy scan; deploy Container Apps; run migrations; smoke tests; integration and load tests.  
- **cd-production.yml (manual):** Approval gate; blue-green deploy; migrations; CDN invalidation; tag release; post-deploy validation.  
- **infrastructure.yml:** Terraform plan/apply on infra changes (path: infrastructure/**).  
- **ml-pipeline.yml:** Model training and registration (workflow_dispatch / schedule).  
- **security-scan.yml:** Dependency and container scanning.

---

## Local Development

- **Prerequisites:** Node.js 20+, Python 3.12+, Poetry, Docker, Azure CLI (optional).  
- **Start:** `docker-compose up -d` (PostgreSQL, Redis, Event Hub emulator, MailHog); backend: `poetry install`, `alembic upgrade head`, `seed_data.py`, `uvicorn app.main:app --reload --port 8000`; frontend: `npm install`, `npm run dev`.  
- **Env:** Backend `.env`: DATABASE_URL, REDIS_URL, JWT_SECRET, EVENT_HUB_CONNECTION_STRING, AZURE_STORAGE_CONNECTION_STRING, ML_MODEL_PATH, SMTP_*. Frontend `.env.local`: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL, NEXTAUTH_URL, NEXTAUTH_SECRET.  
- **Makefile:** `make dev`, `make backend`, `make frontend`, `make db-migrate`, `make db-seed`, `make test`, `make lint`, `make build`, `make train-models`, `make docs`.

---

## Admin, Analyst Web, and Mobile

- **Admin:** Web only; same Next.js app, admin routes; RBAC admin role.  
- **Analyst/Operator:** Web and optional native mobile; same FastAPI API and Socket.IO; RBAC analyst/investigator/viewer.  
- **Mobile:** Same API and auth (JWT / Azure AD); document push and deep-link endpoints in API_SPEC if added.

---

*For exact Terraform modules, SKUs, and env vars see CLAUDE.md and `infrastructure/terraform/`.*
