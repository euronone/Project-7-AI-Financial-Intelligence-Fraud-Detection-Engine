# FinShield AI — Fraud Detection Platform

> ML-powered, real-time fraud detection for banks, fintechs, and insurance providers.

---


## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start (Local — No Docker)](#quick-start-local--no-docker)
5. [Quick Start (Docker Compose)](#quick-start-docker-compose)
6. [Environment Configuration](#environment-configuration)
7. [Seed Data & ML Model Training](#seed-data--ml-model-training)
8. [Available Routes & Pages](#available-routes--pages)
9. [API Reference](#api-reference)
10. [Makefile Commands](#makefile-commands)
11. [Troubleshooting](#troubleshooting)
12. [Tech Stack](#tech-stack)

---

## Project Overview

FinShield AI connects to a financial institution's customer and transaction databases, trains ML models on historical data, and provides:

- Real-time fraud scoring on every transaction (<100ms)
- Multi-layer ML detection: Rules → Isolation Forest → XGBoost → Neural Network → Ensemble
- Multi-channel alerts: Email, SMS, Push, WebSocket
- Full dashboard: KPI cards, live transaction feed, fraud alerts queue, model performance
- Test Me tab: simulate any transaction and see the full fraud detection journey step-by-step

---

## Architecture
Before running the code you have to add details of supabase (databasse and auth) in 3 places
1. frontend 

```
frontend/           Next.js 16 (App Router, TypeScript, Tailwind CSS)
backend/            FastAPI (Python 3.12+, async, SQLAlchemy 2.0)
  app/
    api/v1/         REST endpoints (auth, transactions, alerts, analytics, settings)
    ml/             Feature engineering, model training, fraud scoring pipeline
    rules/          YAML-based rules engine (20+ built-in rules)
    services/       Business logic layer
    db/             SQLAlchemy models + Alembic migrations
    streaming/      WebSocket manager (real-time dashboard feeds)
  scripts/          Data generation + model training scripts
  data/samples/     Pre-generated CSV data (100 customers, 10,000 transactions)
```

**Default local database:** SQLite (`backend/finshield_dev.db`) — no PostgreSQL needed for development.

---

## Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Python | 3.12+ | `python --version` |
| Poetry | 2.x | `poetry --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Docker Desktop | Any recent | `docker --version` *(only for Docker path)* |

---

## Quick Start (Local — No Docker)

This is the recommended approach for development. Uses SQLite — no external services needed.

### Step 1 — Clone and enter the project

```bash
git clone <repo-url>
cd AI-Financial-Intelligence-Fraud
```

### Step 2 — Configure the backend environment

The `.env` file already exists at `backend/.env` with sensible development defaults (SQLite, no Redis required). Review and edit if needed:

```bash
# backend/.env (key defaults already set)
DATABASE_URL=sqlite+aiosqlite:///./finshield_dev.db
APP_ENV=development
JWT_SECRET=finshield-dev-jwt-secret-change-this-in-production-2026
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Step 3 — Install backend dependencies

```bash
cd backend
poetry install
```

### Step 4 — Start the backend server

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

The backend auto-creates all SQLite tables on first startup in development mode.

Verify it's running:
```bash
curl http://localhost:8003/api/v1/health
# Expected: {"status":"ok","app":"FinShield AI","version":"1.0.0"}
```

### Step 5 — Configure the frontend environment

The `.env.local` already exists at `frontend/.env.local`. It points to the backend at port 8001:

```bash
# frontend/.env.local (already configured)
NEXT_PUBLIC_API_URL=http://localhost:8003/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8003
NEXT_PUBLIC_SUPABASE_URL=https://vmbxtblgkzdugqrgprrg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<key already set>
```

### Step 6 — Install and start the frontend

```bash
cd frontend
npm install        # only needed on first run
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Quick Start (Docker Compose)

Use this for a full-stack environment with PostgreSQL + Redis + MailHog.

```bash
# From the project root:
docker compose up --build
```

Services started:

| Container | URL | Purpose |
|-----------|-----|---------|
| `finshield-frontend` | http://localhost:3000 | Next.js app |
| `finshield-backend` | http://localhost:8000 | FastAPI |
| `finshield-postgres` | localhost:5432 | PostgreSQL 16 |
| `finshield-redis` | localhost:6379 | Redis 7 |
| `finshield-mailhog` | http://localhost:8025 | Email preview UI |

> **Note:** Docker Compose uses port **8000** for the backend. Local (no-Docker) dev uses **8001** to avoid conflicts.

To stop all containers:
```bash
docker compose down
```

To stop and wipe all data volumes:
```bash
docker compose down -v
```

---

## Environment Configuration

### Backend — `backend/.env`

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./finshield_dev.db` | Yes | Database connection string |
| `APP_ENV` | `development` | Yes | `development` or `production` |
| `JWT_SECRET` | *(set in file)* | Yes | Change in production |
| `CORS_ORIGINS` | `http://localhost:3000` | Yes | Comma-separated allowed origins |
| `SUPABASE_URL` | *(set in file)* | No | Only for Supabase connector |
| `SUPABASE_ANON_KEY` | *(set in file)* | No | Only for Supabase connector |
| `SUPABASE_SERVICE_KEY` | *(set in file)* | No | Only for Supabase connector |
| `REDIS_URL` | `redis://localhost:6379/0` | No | Falls back gracefully if unavailable |
| `RESEND_API_KEY` | *(empty)* | No | Email alerts via Resend.com |
| `TWILIO_ACCOUNT_SID` | *(empty)* | No | SMS alerts |
| `TWILIO_AUTH_TOKEN` | *(empty)* | No | SMS alerts |
| `ENCRYPTION_KEY` | `dev-encryption-key-32-bytes-long!!` | Yes | Change in production |

For PostgreSQL instead of SQLite:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/finshield_db
```

### Frontend — `frontend/.env.local`

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8003/api/v1` | Backend API base URL |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8003` | WebSocket URL for live feeds |
| `NEXT_PUBLIC_SUPABASE_URL` | *(set in file)* | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(set in file)* | Supabase public anon key |

---

## Seed Data & ML Model Training

Sample data is already pre-generated in `backend/data/samples/`. You can re-generate or retrain anytime.

### Generate Sample Data (100 customers + 10,000 transactions)

```bash
cd backend
python scripts/seed_data.py
```

This creates:
- 100 realistic customer profiles (Indian locale)
- 10,000 transactions across 90 days (~3% fraud rate)
- 6 fraud pattern types: Card-Not-Present, Account Takeover, Impossible Travel, Velocity, Identity Theft, Money Mule

### Train ML Models

```bash
cd backend
python scripts/train_models.py
```

Trains and saves to `backend/app/ml/models/`:
- `isolation_forest_v1.pkl` — unsupervised anomaly detection
- `xgboost_fraud_classifier_v1.pkl` — primary supervised classifier
- `random_forest_v1.pkl` — ensemble stability
- `feature_scaler_v1.pkl` — feature normalization
- `evaluation_report.json` — precision, recall, AUC-ROC metrics

### Run Database Migrations (PostgreSQL only)

```bash
cd backend
alembic upgrade head
```

Create a new migration after model changes:
```bash
alembic revision --autogenerate -m "describe your change"
```

---

## Available Routes & Pages

### Frontend Pages

| URL | Description |
|-----|-------------|
| `http://localhost:3000/` | Redirects to landing or dashboard |
| `http://localhost:3000/landing` | Marketing landing page (10 ribbon sections) |
| `http://localhost:3000/auth` | Login / Signup |
| `http://localhost:3000/onboarding` | New institution setup wizard |
| `http://localhost:3000/dashboard` | Main fraud analytics dashboard |

### Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/auth/signup` | Register new institution |
| `POST` | `/api/v1/auth/login` | Login, returns JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/me` | Current user profile |
| `POST` | `/api/v1/transactions` | Ingest + score a transaction |
| `GET` | `/api/v1/transactions` | List transactions with filters |
| `GET` | `/api/v1/transactions/{id}` | Transaction detail + fraud breakdown |
| `POST` | `/api/v1/transactions/test` | Submit a test transaction (is_test=true) |
| `GET` | `/api/v1/fraud-alerts` | List fraud alerts |
| `PUT` | `/api/v1/fraud-alerts/{id}/status` | Update alert status |
| `GET` | `/api/v1/analytics/overview` | KPI dashboard data |
| `GET` | `/api/v1/analytics/fraud-trends` | Fraud trend charts |
| `GET` | `/api/v1/settings` | Get tenant settings |
| `PUT` | `/api/v1/settings/database` | Update DB connection |

Full interactive docs: **http://localhost:8003/docs**

### WebSocket

```
ws://localhost:8003/ws/{tenant_id}
```

Events received:
- `connected` — connection confirmed
- `transaction_scored` — new transaction scored in real-time
- `fraud_alert_created` — new alert triggered

---

## Makefile Commands

Run from the **project root**:

```bash
make dev              # Start all via Docker Compose
make backend          # Start backend only (port 8000)
make frontend         # Start frontend only (port 3000)
make db-migrate       # Run Alembic migrations
make db-seed          # Seed 100 customers + 10,000 transactions
make train-models     # Train all ML models
make test             # Run all tests (pytest + npm test)
make test-backend     # pytest only
make test-frontend    # npm test only
make lint             # ruff (backend) + eslint (frontend)
make format           # ruff format (backend)
make build            # Build Docker images
```

---

## Troubleshooting

### Backend won't start — `pyproject.toml` error
```
The Poetry configuration is invalid: Additional properties are not allowed ('python' was unexpected)
```
**Fix:** Remove the duplicate `python = "^3.12"` line from `[tool.poetry]` section. It belongs only under `[tool.poetry.dependencies]`.

### Port already in use
```bash
# Find what's using port 8001
netstat -ano | findstr :8001

# Kill by PID (Windows)
taskkill /PID <pid> /F
```

### Frontend can't reach backend (CORS or connection refused)
- Confirm backend is running: `curl http://localhost:8003/api/v1/health`
- Confirm `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8003/api/v1`
- Confirm backend `.env` has `CORS_ORIGINS=http://localhost:3000`

### SQLite database locked
Only one process can write to the SQLite file at a time. Stop any other running backend instances before starting a new one.

### Redis connection errors
Redis is **optional** for local development. The backend falls back gracefully if Redis is unavailable — notifications will use in-app only. To use Redis, install it or run:
```bash
docker run -p 6379:6379 redis:7-alpine
```

### Poetry dependency conflicts on Python 3.13
Some ML packages (e.g., `onnxruntime`) may not have wheels for Python 3.13 yet. If installation fails:
```bash
# Use Python 3.12 explicitly
poetry env use python3.12
poetry install
```

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.x | React framework (App Router) |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Dark-theme styling |
| Zustand | 5.x | State management |
| Framer Motion | 12.x | Animations |
| React Hook Form + Zod | Latest | Form validation |

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.115+ | Async REST API |
| SQLAlchemy | 2.0 (async) | ORM |
| Alembic | 1.14+ | DB migrations |
| Pydantic v2 | 2.10+ | Request/response validation |
| python-jose | 3.x | JWT authentication |
| passlib + bcrypt | 1.7+ | Password hashing |
| scikit-learn | 1.5+ | Isolation Forest, Random Forest |
| XGBoost | 2.1+ | Primary fraud classifier |
| SHAP | 0.46+ | Model explainability |
| ONNX Runtime | 1.20+ | Fast neural network inference |
| structlog | 24.x | Structured logging |

### Infrastructure
| Service | Local Default | Production |
|---------|--------------|-----------|
| Database | SQLite (aiosqlite) | Supabase / PostgreSQL |
| Cache | None (optional Redis) | Redis 7 |
| Email | In-app only | Resend.com |
| SMS | Disabled | Twilio |
| Deployment | Local | Vercel (frontend) + Railway (backend) |

---

## Default Test Credentials

```
Admin:    admin@finshield.local   /  Admin123!@#
Analyst:  analyst@finshield.local /  Analyst123!@#
```

*(These are created automatically when you run `python scripts/seed_data.py`)*

---

*FinShield AI — Built for financial institutions. Multi-tenant, ML-powered, real-time.*
