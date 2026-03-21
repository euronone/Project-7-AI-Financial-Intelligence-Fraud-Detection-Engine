# FinShield AI — AI Financial Intelligence & Fraud Detection Engine

Production-grade, real-time fraud detection platform that combines machine learning models, a configurable rules engine, and behavioral analytics to score every financial transaction in sub-second latency. Built for banks, fintechs, payment gateways, and financial institutions.

---

## Architecture Overview

```
┌──────────────┐      ┌──────────────────────────────────────────────────┐
│  Next.js 14  │◄────►│                  FastAPI Backend                 │
│  (Frontend)  │ REST │  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  React 18    │  +   │  │ Rules      │  │ ML Models  │  │ Risk      │  │
│  Tailwind    │  WS  │  │ Engine     │  │ (ONNX)     │  │ Scoring   │  │
└──────────────┘      │  └────────────┘  └────────────┘  └───────────┘  │
                      └──────────┬──────────────┬──────────────┬────────┘
                                 │              │              │
                      ┌──────────▼──┐  ┌───────▼────┐  ┌─────▼──────┐
                      │ PostgreSQL  │  │   Redis     │  │ Event Hubs │
                      │ 16          │  │   7         │  │ (Kafka)    │
                      └─────────────┘  └────────────┘  └────────────┘
```

Transactions flow through the ingestion API (or Azure Event Hubs), pass through feature engineering (200+ features), parallel rule evaluation, and ML inference, and receive a composite fraud/risk score — all within 200 ms P95.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5, Tailwind CSS 3, Zustand, TanStack Query v5, Recharts + D3.js, Socket.IO Client |
| **Backend** | FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Pydantic v2, Celery + Redis, python-socketio |
| **ML / AI** | scikit-learn, XGBoost, PyTorch, ONNX Runtime, SHAP |
| **Data** | PostgreSQL 16, Redis 7, Azure Event Hubs, Azure Blob Storage |
| **Infrastructure** | Azure Container Apps, Terraform, GitHub Actions, Azure Front Door + WAF |
| **Observability** | structlog, Azure Application Insights, Log Analytics, OpenTelemetry |
| **Security** | JWT + RBAC, Azure Key Vault, PII masking, CSP/HSTS headers, rate limiting |

---

## Quick Start

> Full deployment instructions (including Azure) are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

```bash
# 1. Start infrastructure (Postgres, Redis, MailHog)
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env
poetry install
poetry run alembic upgrade head
poetry run python scripts/seed_data.py
poetry run uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |

**Default credentials:** `admin@finshield.dev` / `Admin123!@#`

---

## Project Structure

```
├── frontend/                  Next.js 14 application
│   ├── src/app/               App Router pages & layouts
│   ├── src/components/        UI, charts, dashboard, fraud, rules, network
│   ├── src/hooks/             Custom React hooks
│   ├── src/lib/               API client, auth, utilities
│   ├── src/stores/            Zustand state stores
│   └── src/types/             TypeScript type definitions
│
├── backend/                   FastAPI application
│   ├── app/api/v1/            REST API routers
│   ├── app/core/              Security, middleware, config, exceptions
│   ├── app/models/            SQLAlchemy ORM models
│   ├── app/schemas/           Pydantic request/response schemas
│   ├── app/services/          Business logic layer
│   ├── app/ml/                ML pipeline, models, training
│   ├── app/rules/             Rules engine
│   ├── app/streaming/         Event Hub consumer/producer, WebSockets
│   └── app/integrations/      Azure ML, Storage, Key Vault, email, SMS
│
├── infrastructure/            Terraform modules & deploy scripts
│   ├── terraform/modules/     networking, database, cache, container_apps, ...
│   └── scripts/               setup-azure.sh, init-terraform.sh
│
├── .github/workflows/         CI/CD pipelines
├── docker-compose.yml         Local dev environment
├── Makefile                   Common dev commands
└── docs/                      PRD, architecture, API spec, DB schema, deployment
```

---

## Development Commands

| Command | Description |
|---|---|
| `make dev` | Start Docker infrastructure |
| `make backend` | Start backend dev server |
| `make frontend` | Start frontend dev server |
| `make db-migrate` | Run Alembic migrations |
| `make db-seed` | Seed database with test data |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests only |
| `make test-frontend` | Run frontend tests only |
| `make lint` | Lint all code (ruff + eslint) |
| `make format` | Auto-format code |
| `make build` | Build Docker images locally |
| `make train-models` | Run ML training pipeline |

---

## API Documentation

Interactive Swagger UI is available at `/docs` when the backend is running. ReDoc is at `/redoc`.

All endpoints are under `/api/v1/` — see [docs/API_SPEC.md](docs/API_SPEC.md) for the full specification.

---

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Follow conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
3. Ensure `make lint` and `make test` pass
4. Open a pull request — CI runs automatically
5. Obtain at least one reviewer approval before merging

---

## Documentation

- [Product Requirements (PRD)](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Specification](docs/API_SPEC.md)
- [Database Schema](docs/DB_SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Build Plan](docs/BUILD_PLAN.md)

---

## License

MIT
