# FinShield AI — Architecture

**Project:** FinShield AI — AI Financial Intelligence & Fraud Detection Engine  
**Deployment:** Microsoft Azure  

This document describes the high-level architecture, tech stack, project structure, and data flows. See docs/PRD.md for features, docs/API_SPEC.md for APIs, docs/DB_SCHEMA.md for schema, and docs/DEPLOYMENT.md for Azure and CI/CD.

---

## Overview

FinShield AI is a real-time fraud detection platform. Transactions are ingested via REST or Azure Event Hubs, passed through feature engineering, a rules engine, and ML models (fraud classifier, anomaly detector, behavioral profiler). A risk score is aggregated and a decision (PASS / FLAG / ALERT / BLOCK) is made. Alerts and notifications are created as needed; state is stored in PostgreSQL and exposed via REST and Socket.IO.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5, Tailwind CSS, Zustand, TanStack Query v5, Recharts/D3, Socket.IO client, NextAuth.js (Azure AD), Vitest, Playwright |
| **Backend** | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, Celery, Socket.IO (python-socketio), scikit-learn/XGBoost/PyTorch, ONNX Runtime |
| **Data** | PostgreSQL 16 (Azure Database for PostgreSQL), Redis 7 (Azure Cache for Redis), Azure Event Hubs, Azure Blob Storage |
| **ML** | Azure Machine Learning (optional), ONNX models in Blob |
| **Infra** | Azure Container Apps, ACR, Azure Front Door + WAF, Azure Key Vault, Terraform, GitHub Actions |

---

## Project Structure (Summary)

- **frontend/** — Next.js app: (auth), (dashboard) with dashboard, transactions, fraud-alerts, risk-scoring, analytics, rules-engine, case-management, ml-models, entities, watchlists, audit-log, settings, network-graph; components, hooks, lib, stores, types.
- **backend/** — FastAPI app: `app/api/v1/` (routes), `app/core/` (config, security, middleware), `app/models/`, `app/schemas/`, `app/services/`, `app/ml/` (pipeline, feature_engineering, model_registry, anomaly_detector, fraud_classifier, risk_scorer, behavioral_profiler, network_analyzer, explainability, training/), `app/rules/` (engine, conditions, actions, templates), `app/streaming/` (Event Hub consumer, producer, processor, websocket_manager), `app/integrations/`, `app/db/` (session, migrations, seed).
- **infrastructure/terraform/** — Azure modules: networking, database, cache, container_apps, event_hubs, storage, monitoring, security, ml, frontdoor, acr; environments (dev, staging, prod).
- **.github/workflows/** — ci.yml, cd-staging.yml, cd-production.yml, infrastructure.yml, ml-pipeline.yml, security-scan.yml.

---

## Interfaces

- **Admin (web):** Config and monitoring — rules, ML models, watchlists, settings, API keys, team, audit. Same Next.js app, admin-only routes.
- **Analyst/Operator (web):** Dashboard, transactions, alerts, cases, risk scoring, analytics, entities, network graph. Same Next.js app, role-based access.
- **Native mobile (optional):** Subset of analyst features via same FastAPI API and Socket.IO; separate codebase.

One API surface serves all; RBAC distinguishes admin vs analyst vs viewer.

---

## Data Flow: Fraud Detection Pipeline

```
Transaction Ingested (REST or Event Hubs)
    │
    ├─→ Feature Engineering (200+ features)
    │
    ├─→ Rules Engine (parallel evaluation of active rules)
    │
    ├─→ ML Models (parallel inference):
    │       Fraud Classifier → fraud probability
    │       Anomaly Detector → anomaly score
    │       Behavioral Profiler → deviation score
    │
    ├─→ Risk Score Aggregation (weighted combination)
    │
    ├─→ Decision Engine:
    │       score < 0.3  → PASS
    │       0.3 ≤ score < 0.6 → FLAG for review
    │       0.6 ≤ score < 0.8 → ALERT
    │       score ≥ 0.8 → BLOCK + ALERT
    │
    └─→ Post-Processing:
            Update entity risk, create fraud alert (if triggered),
            send notifications, emit Socket.IO events, audit log
```

---

## Key Design Principles

- **Clean architecture:** Routes → Services → Repositories/Models; no business logic in routes or schemas.
- **Stateless API and workers:** Session and cache in Redis; canonical state in PostgreSQL.
- **Graceful degradation:** If ML is down, use rules-only scoring.
- **Observability:** Structured logs (structlog), correlation IDs, metrics and tracing to Azure.
- **Security:** No secrets in code; Key Vault and env; RBAC; rate limiting; audit trail.

---

*For implementation details see CLAUDE.md and the referenced docs.*
