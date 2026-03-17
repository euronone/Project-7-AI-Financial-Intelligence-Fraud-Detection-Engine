# CLAUDE.md — AI Financial Intelligence & Fraud Detection Engine

## Project Overview 


**Project Name:** FinShield AI — AI Financial Intelligence & Fraud Detection Engine
**Version:** 1.0.0
**Type:** Full-Stack Real-Time Fraud Detection Platform
**Target Users:** Banks, Fintechs, Payment Gateways, Financial Institutions
**Deployment Target:** Microsoft Azure (Fully Autonomous, Zero Human Intervention) 

FinShield AI is a production-grade, real-time system that detects fraud, assesses risk, and identifies anomalies in financial transactions. It combines machine learning models, rule-based engines, and behavioral analytics to provide sub-second fraud scoring on every transaction flowing through the system.

---

## Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| UI Library | React 18 |
| Styling | Tailwind CSS 3 |
| Language | TypeScript 5 |
| State Management | Zustand |
| Data Fetching | TanStack Query (React Query) v5 |
| Charts/Viz | Recharts + D3.js |
| Real-Time | Socket.IO Client |
| Forms | React Hook Form + Zod validation |
| Tables | TanStack Table v8 |
| Auth UI | NextAuth.js (Azure AD provider) |
| Testing | Vitest + React Testing Library + Playwright |

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.12) |
| Language | Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Task Queue | Celery + Redis |
| WebSocket | FastAPI WebSockets + Socket.IO (python-socketio) |
| ML Framework | scikit-learn, XGBoost, PyTorch |
| ML Serving | ONNX Runtime |
| API Docs | Auto-generated OpenAPI/Swagger |
| Auth | OAuth2 + JWT (python-jose) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio + httpx |

### Data & Infrastructure
| Layer | Technology |
|---|---|
| Primary DB | PostgreSQL 16 (Azure Database for PostgreSQL) |
| Cache/Broker | Redis 7 (Azure Cache for Redis) |
| Search/Analytics | Azure Cognitive Search |
| Object Storage | Azure Blob Storage |
| Message Streaming | Azure Event Hubs (Kafka-compatible) |
| ML Registry | Azure Machine Learning |
| Monitoring | Azure Monitor + Application Insights |
| Logging | Structured logging (structlog) → Azure Log Analytics |
| Container Runtime | Azure Container Apps |
| CI/CD | GitHub Actions |
| IaC | Terraform + Azure Resource Manager (ARM) |
| Secrets | Azure Key Vault |
| DNS/CDN | Azure Front Door |
| Container Registry | Azure Container Registry (ACR) |

---

## Project Structure

```
project7/
├── CLAUDE.md                          # This PRD file
├── README.md                          # Quick-start guide
│
├── frontend/                          # Next.js Frontend Application
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── postcss.config.js
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── .env.local.example
│   ├── .eslintrc.json
│   ├── .prettierrc
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── logo.svg
│   │   └── assets/
│   │       └── images/
│   │
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   │   ├── layout.tsx             # Root layout
│   │   │   ├── page.tsx               # Landing/redirect
│   │   │   ├── globals.css            # Global styles
│   │   │   ├── loading.tsx            # Global loading
│   │   │   ├── error.tsx              # Global error boundary
│   │   │   ├── not-found.tsx          # 404 page
│   │   │   │
│   │   │   ├── (auth)/               # Auth route group
│   │   │   │   ├── login/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── register/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── forgot-password/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── layout.tsx
│   │   │   │
│   │   │   ├── (dashboard)/           # Main dashboard route group
│   │   │   │   ├── layout.tsx         # Dashboard shell (sidebar + topbar)
│   │   │   │   ├── dashboard/
│   │   │   │   │   └── page.tsx       # Overview dashboard
│   │   │   │   │
│   │   │   │   ├── transactions/
│   │   │   │   │   ├── page.tsx       # Transaction list with filters
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Transaction detail + fraud analysis
│   │   │   │   │
│   │   │   │   ├── fraud-alerts/
│   │   │   │   │   ├── page.tsx       # Active fraud alerts
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Alert detail + investigation
│   │   │   │   │
│   │   │   │   ├── risk-scoring/
│   │   │   │   │   ├── page.tsx       # Risk score dashboard
│   │   │   │   │   └── profiles/
│   │   │   │   │       └── [id]/
│   │   │   │   │           └── page.tsx  # Entity risk profile
│   │   │   │   │
│   │   │   │   ├── analytics/
│   │   │   │   │   ├── page.tsx       # Analytics overview
│   │   │   │   │   ├── trends/
│   │   │   │   │   │   └── page.tsx   # Fraud trend analysis
│   │   │   │   │   ├── patterns/
│   │   │   │   │   │   └── page.tsx   # Pattern recognition view
│   │   │   │   │   └── reports/
│   │   │   │   │       └── page.tsx   # Generate & export reports
│   │   │   │   │
│   │   │   │   ├── rules-engine/
│   │   │   │   │   ├── page.tsx       # Rule management
│   │   │   │   │   ├── create/
│   │   │   │   │   │   └── page.tsx   # Rule builder
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Edit rule
│   │   │   │   │
│   │   │   │   ├── case-management/
│   │   │   │   │   ├── page.tsx       # Investigation case list
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Case detail + timeline
│   │   │   │   │
│   │   │   │   ├── ml-models/
│   │   │   │   │   ├── page.tsx       # Model registry & performance
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Model detail + metrics
│   │   │   │   │
│   │   │   │   ├── entities/
│   │   │   │   │   ├── page.tsx       # Customer/merchant entity list
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx   # Entity 360 view
│   │   │   │   │
│   │   │   │   ├── watchlists/
│   │   │   │   │   └── page.tsx       # Sanctions & watchlist management
│   │   │   │   │
│   │   │   │   ├── audit-log/
│   │   │   │   │   └── page.tsx       # System audit trail
│   │   │   │   │
│   │   │   │   ├── settings/
│   │   │   │   │   ├── page.tsx       # General settings
│   │   │   │   │   ├── team/
│   │   │   │   │   │   └── page.tsx   # Team & role management
│   │   │   │   │   ├── integrations/
│   │   │   │   │   │   └── page.tsx   # Third-party integrations
│   │   │   │   │   ├── notifications/
│   │   │   │   │   │   └── page.tsx   # Alert notification config
│   │   │   │   │   └── api-keys/
│   │   │   │   │       └── page.tsx   # API key management
│   │   │   │   │
│   │   │   │   └── network-graph/
│   │   │   │       └── page.tsx       # Transaction network visualization
│   │   │   │
│   │   │   └── api/                   # Next.js API routes (BFF)
│   │   │       ├── auth/
│   │   │       │   └── [...nextauth]/
│   │   │       │       └── route.ts
│   │   │       └── proxy/
│   │   │           └── [...path]/
│   │   │               └── route.ts   # Proxy to FastAPI backend
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # Base UI primitives
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── modal.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   ├── tooltip.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   ├── progress.tsx
│   │   │   │   ├── avatar.tsx
│   │   │   │   ├── switch.tsx
│   │   │   │   ├── slider.tsx
│   │   │   │   ├── data-table.tsx
│   │   │   │   └── pagination.tsx
│   │   │   │
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   ├── topbar.tsx
│   │   │   │   ├── breadcrumbs.tsx
│   │   │   │   └── footer.tsx
│   │   │   │
│   │   │   ├── charts/
│   │   │   │   ├── fraud-trend-chart.tsx
│   │   │   │   ├── risk-distribution-chart.tsx
│   │   │   │   ├── transaction-volume-chart.tsx
│   │   │   │   ├── geo-heatmap.tsx
│   │   │   │   ├── anomaly-scatter-plot.tsx
│   │   │   │   └── model-performance-chart.tsx
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── stats-card.tsx
│   │   │   │   ├── alert-feed.tsx
│   │   │   │   ├── recent-transactions.tsx
│   │   │   │   ├── risk-gauge.tsx
│   │   │   │   └── live-activity-ticker.tsx
│   │   │   │
│   │   │   ├── transactions/
│   │   │   │   ├── transaction-table.tsx
│   │   │   │   ├── transaction-filters.tsx
│   │   │   │   ├── transaction-detail-card.tsx
│   │   │   │   └── fraud-score-indicator.tsx
│   │   │   │
│   │   │   ├── fraud/
│   │   │   │   ├── alert-card.tsx
│   │   │   │   ├── alert-timeline.tsx
│   │   │   │   ├── investigation-panel.tsx
│   │   │   │   └── evidence-viewer.tsx
│   │   │   │
│   │   │   ├── rules/
│   │   │   │   ├── rule-builder.tsx
│   │   │   │   ├── condition-editor.tsx
│   │   │   │   ├── rule-test-panel.tsx
│   │   │   │   └── rule-list-item.tsx
│   │   │   │
│   │   │   ├── network/
│   │   │   │   ├── graph-canvas.tsx
│   │   │   │   ├── node-tooltip.tsx
│   │   │   │   └── graph-controls.tsx
│   │   │   │
│   │   │   └── shared/
│   │   │       ├── risk-badge.tsx
│   │   │       ├── status-indicator.tsx
│   │   │       ├── date-range-picker.tsx
│   │   │       ├── search-bar.tsx
│   │   │       ├── export-button.tsx
│   │   │       ├── empty-state.tsx
│   │   │       └── confirmation-dialog.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── use-auth.ts
│   │   │   ├── use-socket.ts
│   │   │   ├── use-transactions.ts
│   │   │   ├── use-alerts.ts
│   │   │   ├── use-risk-scores.ts
│   │   │   ├── use-rules.ts
│   │   │   ├── use-analytics.ts
│   │   │   ├── use-models.ts
│   │   │   ├── use-debounce.ts
│   │   │   └── use-pagination.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api-client.ts          # Axios/fetch wrapper for FastAPI
│   │   │   ├── socket.ts             # Socket.IO client setup
│   │   │   ├── auth.ts               # NextAuth config
│   │   │   ├── utils.ts              # General utilities
│   │   │   ├── formatters.ts         # Currency, date, number formatters
│   │   │   ├── constants.ts          # App-wide constants
│   │   │   └── validators.ts         # Zod schemas shared with forms
│   │   │
│   │   ├── stores/
│   │   │   ├── auth-store.ts
│   │   │   ├── alert-store.ts
│   │   │   ├── filter-store.ts
│   │   │   └── ui-store.ts
│   │   │
│   │   ├── types/
│   │   │   ├── transaction.ts
│   │   │   ├── alert.ts
│   │   │   ├── rule.ts
│   │   │   ├── entity.ts
│   │   │   ├── risk.ts
│   │   │   ├── model.ts
│   │   │   ├── analytics.ts
│   │   │   ├── case.ts
│   │   │   ├── user.ts
│   │   │   └── api.ts                 # API response/request types
│   │   │
│   │   └── styles/
│   │       └── theme.ts              # Tailwind theme extensions
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── lib/
│   │   └── e2e/
│   │       ├── auth.spec.ts
│   │       ├── dashboard.spec.ts
│   │       ├── transactions.spec.ts
│   │       ├── fraud-alerts.spec.ts
│   │       └── rules-engine.spec.ts
│   │
│   └── Dockerfile
│
├── backend/                           # FastAPI Backend Application
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── alembic.ini
│   ├── .env.example
│   ├── Dockerfile
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── dependencies.py            # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Main API router aggregator
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py            # Login, register, token refresh
│   │   │       ├── transactions.py    # Transaction CRUD + search
│   │   │       ├── fraud_alerts.py    # Alert CRUD + actions
│   │   │       ├── risk_scoring.py    # Risk score endpoints
│   │   │       ├── analytics.py       # Analytics & reporting
│   │   │       ├── rules.py           # Rules engine CRUD
│   │   │       ├── cases.py           # Case management
│   │   │       ├── entities.py        # Customer/merchant entities
│   │   │       ├── models.py          # ML model registry
│   │   │       ├── watchlists.py      # Sanctions & watchlists
│   │   │       ├── audit.py           # Audit log
│   │   │       ├── settings.py        # System settings
│   │   │       ├── users.py           # User management
│   │   │       ├── webhooks.py        # Webhook management
│   │   │       ├── network.py         # Network/graph analysis
│   │   │       └── health.py          # Health check
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # JWT, password hashing, OAuth2
│   │   │   ├── permissions.py        # RBAC permission system
│   │   │   ├── rate_limiter.py       # API rate limiting
│   │   │   ├── middleware.py          # Custom middleware (logging, CORS, timing)
│   │   │   ├── exceptions.py         # Custom exception handlers
│   │   │   └── events.py             # Startup/shutdown events
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base model with audit fields
│   │   │   ├── user.py
│   │   │   ├── transaction.py
│   │   │   ├── fraud_alert.py
│   │   │   ├── rule.py
│   │   │   ├── case.py
│   │   │   ├── entity.py
│   │   │   ├── risk_score.py
│   │   │   ├── watchlist.py
│   │   │   ├── audit_log.py
│   │   │   ├── ml_model.py
│   │   │   ├── notification.py
│   │   │   └── webhook.py
│   │   │
│   │   ├── schemas/                   # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── transaction.py
│   │   │   ├── fraud_alert.py
│   │   │   ├── rule.py
│   │   │   ├── case.py
│   │   │   ├── entity.py
│   │   │   ├── risk_score.py
│   │   │   ├── watchlist.py
│   │   │   ├── audit.py
│   │   │   ├── ml_model.py
│   │   │   ├── analytics.py
│   │   │   ├── user.py
│   │   │   └── common.py             # Pagination, filters, base schemas
│   │   │
│   │   ├── services/                  # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── fraud_detection_service.py
│   │   │   ├── risk_scoring_service.py
│   │   │   ├── rules_engine_service.py
│   │   │   ├── case_service.py
│   │   │   ├── entity_service.py
│   │   │   ├── watchlist_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── ml_service.py
│   │   │   ├── network_analysis_service.py
│   │   │   └── webhook_service.py
│   │   │
│   │   ├── ml/                        # Machine Learning Module
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py           # ML inference pipeline
│   │   │   ├── feature_engineering.py # Feature extraction & transformation
│   │   │   ├── model_registry.py     # Model versioning & loading
│   │   │   ├── anomaly_detector.py   # Isolation Forest / Autoencoder
│   │   │   ├── fraud_classifier.py   # XGBoost / Neural net classifier
│   │   │   ├── risk_scorer.py        # Risk score computation
│   │   │   ├── behavioral_profiler.py # User behavior profiling
│   │   │   ├── network_analyzer.py   # Graph-based fraud detection
│   │   │   ├── explainability.py     # SHAP / LIME explanations
│   │   │   ├── training/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── train_fraud_model.py
│   │   │   │   ├── train_anomaly_model.py
│   │   │   │   ├── train_risk_model.py
│   │   │   │   ├── evaluate.py
│   │   │   │   └── data_prep.py
│   │   │   └── models/               # Serialized model files (.onnx)
│   │   │       └── .gitkeep
│   │   │
│   │   ├── rules/                     # Rules Engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py             # Rule evaluation engine
│   │   │   ├── conditions.py         # Condition types & operators
│   │   │   ├── actions.py            # Rule action handlers
│   │   │   └── templates.py          # Pre-built rule templates
│   │   │
│   │   ├── streaming/                 # Real-Time Processing
│   │   │   ├── __init__.py
│   │   │   ├── consumer.py           # Event Hub consumer
│   │   │   ├── producer.py           # Event Hub producer
│   │   │   ├── processor.py          # Stream processing pipeline
│   │   │   └── websocket_manager.py  # WebSocket connection manager
│   │   │
│   │   ├── integrations/             # Third-Party Integrations
│   │   │   ├── __init__.py
│   │   │   ├── azure_ml.py           # Azure ML integration
│   │   │   ├── azure_storage.py      # Blob storage operations
│   │   │   ├── azure_keyvault.py     # Secret management
│   │   │   ├── email_service.py      # Email notifications (SendGrid/Azure)
│   │   │   ├── sms_service.py        # SMS notifications (Twilio)
│   │   │   └── sanctions_api.py      # External sanctions list API
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── session.py            # Async DB session factory
│   │       ├── migrations/           # Alembic migrations
│   │       │   ├── env.py
│   │       │   ├── script.py.mako
│   │       │   └── versions/
│   │       └── seed.py               # Database seeding script
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Fixtures (test DB, client, auth)
│   │   ├── unit/
│   │   │   ├── test_fraud_detection.py
│   │   │   ├── test_risk_scoring.py
│   │   │   ├── test_rules_engine.py
│   │   │   ├── test_feature_engineering.py
│   │   │   ├── test_auth.py
│   │   │   └── test_services.py
│   │   ├── integration/
│   │   │   ├── test_transaction_flow.py
│   │   │   ├── test_alert_workflow.py
│   │   │   ├── test_case_management.py
│   │   │   └── test_api_endpoints.py
│   │   └── load/
│   │       ├── locustfile.py         # Load testing with Locust
│   │       └── scenarios.py
│   │
│   └── scripts/
│       ├── seed_data.py              # Generate realistic test data
│       ├── train_models.py           # Model training orchestrator
│       └── migrate.py               # Migration runner
│
├── infrastructure/                    # Azure Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf                   # Root module
│   │   ├── variables.tf             # Input variables
│   │   ├── outputs.tf               # Outputs (URLs, connection strings)
│   │   ├── providers.tf             # Azure provider config
│   │   ├── backend.tf               # Terraform state backend (Azure Storage)
│   │   ├── terraform.tfvars.example
│   │   │
│   │   ├── modules/
│   │   │   ├── networking/
│   │   │   │   ├── main.tf           # VNet, subnets, NSGs, private endpoints
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── database/
│   │   │   │   ├── main.tf           # PostgreSQL Flexible Server
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── cache/
│   │   │   │   ├── main.tf           # Azure Cache for Redis
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── container_apps/
│   │   │   │   ├── main.tf           # Container Apps Environment + Apps
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── event_hubs/
│   │   │   │   ├── main.tf           # Event Hubs namespace + hubs
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── storage/
│   │   │   │   ├── main.tf           # Blob Storage accounts
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── monitoring/
│   │   │   │   ├── main.tf           # Log Analytics, App Insights, alerts
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── security/
│   │   │   │   ├── main.tf           # Key Vault, managed identities
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── ml/
│   │   │   │   ├── main.tf           # Azure ML workspace
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   ├── frontdoor/
│   │   │   │   ├── main.tf           # Azure Front Door + WAF
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   │
│   │   │   └── acr/
│   │   │       ├── main.tf           # Azure Container Registry
│   │   │       ├── variables.tf
│   │   │       └── outputs.tf
│   │   │
│   │   └── environments/
│   │       ├── dev.tfvars
│   │       ├── staging.tfvars
│   │       └── prod.tfvars
│   │
│   └── scripts/
│       ├── setup-azure.sh            # One-time Azure subscription setup
│       ├── init-terraform.sh         # Initialize Terraform backend
│       └── destroy.sh                # Teardown script
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint + test on every PR
│       ├── cd-staging.yml            # Auto-deploy to staging on merge to main
│       ├── cd-production.yml         # Deploy to production (manual trigger + approval)
│       ├── infrastructure.yml        # Terraform plan/apply
│       ├── ml-pipeline.yml           # Model training & registry push
│       └── security-scan.yml        # Dependency & container scanning
│
├── docker-compose.yml                # Local development environment
├── docker-compose.override.yml       # Dev overrides (hot reload, volumes)
├── .gitignore
├── .editorconfig
└── Makefile                          # Common dev commands
```

---

## Database Schema

### Core Tables

#### `users`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| role | ENUM('admin','analyst','investigator','viewer') | NOT NULL, default 'viewer' |
| is_active | BOOLEAN | default TRUE |
| mfa_enabled | BOOLEAN | default FALSE |
| mfa_secret | VARCHAR(255) | NULLABLE |
| last_login_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `transactions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| external_id | VARCHAR(255) | UNIQUE, NOT NULL |
| source_entity_id | UUID | FK → entities(id) |
| destination_entity_id | UUID | FK → entities(id), NULLABLE |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL (ISO 4217) |
| transaction_type | ENUM('payment','transfer','withdrawal','deposit','refund') | NOT NULL |
| channel | ENUM('online','pos','atm','mobile','wire','ach') | NOT NULL |
| status | ENUM('pending','completed','failed','reversed','flagged','blocked') | NOT NULL |
| merchant_category_code | VARCHAR(4) | NULLABLE |
| description | TEXT | NULLABLE |
| ip_address | INET | NULLABLE |
| device_fingerprint | VARCHAR(255) | NULLABLE |
| geolocation_lat | DECIMAL(10,7) | NULLABLE |
| geolocation_lng | DECIMAL(10,7) | NULLABLE |
| country_code | VARCHAR(2) | NULLABLE |
| card_present | BOOLEAN | NULLABLE |
| fraud_score | DECIMAL(5,4) | NULLABLE (0.0000–1.0000) |
| risk_level | ENUM('low','medium','high','critical') | NULLABLE |
| processed_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | default NOW() |

**Indexes:** `idx_transactions_source_entity`, `idx_transactions_processed_at`, `idx_transactions_fraud_score`, `idx_transactions_status`, `idx_transactions_external_id`
**Partitioning:** Range partition by `processed_at` (monthly)

#### `entities`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| external_id | VARCHAR(255) | UNIQUE |
| entity_type | ENUM('individual','business','merchant') | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NULLABLE |
| phone | VARCHAR(50) | NULLABLE |
| country_code | VARCHAR(2) | NULLABLE |
| risk_score | DECIMAL(5,4) | default 0.0000 |
| risk_level | ENUM('low','medium','high','critical') | default 'low' |
| is_watchlisted | BOOLEAN | default FALSE |
| kyc_status | ENUM('pending','verified','rejected','expired') | default 'pending' |
| metadata | JSONB | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `fraud_alerts`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| transaction_id | UUID | FK → transactions(id) |
| entity_id | UUID | FK → entities(id), NULLABLE |
| alert_type | ENUM('ml_detection','rule_trigger','manual','watchlist_match','anomaly','velocity') | NOT NULL |
| severity | ENUM('low','medium','high','critical') | NOT NULL |
| status | ENUM('open','investigating','escalated','resolved_fraud','resolved_false_positive','dismissed') | NOT NULL, default 'open' |
| title | VARCHAR(500) | NOT NULL |
| description | TEXT | NOT NULL |
| confidence_score | DECIMAL(5,4) | NULLABLE |
| rule_id | UUID | FK → rules(id), NULLABLE |
| model_id | UUID | FK → ml_models(id), NULLABLE |
| evidence | JSONB | NULLABLE |
| assigned_to | UUID | FK → users(id), NULLABLE |
| resolved_by | UUID | FK → users(id), NULLABLE |
| resolved_at | TIMESTAMPTZ | NULLABLE |
| resolution_notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `rules`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | NULLABLE |
| category | ENUM('velocity','amount','geography','pattern','device','custom') | NOT NULL |
| conditions | JSONB | NOT NULL |
| actions | JSONB | NOT NULL |
| severity | ENUM('low','medium','high','critical') | NOT NULL |
| is_active | BOOLEAN | default TRUE |
| priority | INTEGER | default 100 |
| hit_count | BIGINT | default 0 |
| false_positive_rate | DECIMAL(5,4) | NULLABLE |
| created_by | UUID | FK → users(id) |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `cases`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| case_number | VARCHAR(50) | UNIQUE, NOT NULL (auto-generated: CASE-YYYYMMDD-XXXX) |
| title | VARCHAR(500) | NOT NULL |
| description | TEXT | NULLABLE |
| status | ENUM('open','in_progress','pending_review','escalated','closed_confirmed_fraud','closed_false_positive') | NOT NULL |
| priority | ENUM('low','medium','high','critical') | NOT NULL |
| assigned_to | UUID | FK → users(id), NULLABLE |
| total_amount_at_risk | DECIMAL(18,4) | NULLABLE |
| alert_ids | UUID[] | Array of related alert IDs |
| timeline | JSONB | Array of timeline events |
| findings | TEXT | NULLABLE |
| created_by | UUID | FK → users(id) |
| closed_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `risk_scores`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| entity_id | UUID | FK → entities(id) |
| transaction_id | UUID | FK → transactions(id), NULLABLE |
| overall_score | DECIMAL(5,4) | NOT NULL |
| component_scores | JSONB | NOT NULL (breakdown by factor) |
| risk_factors | JSONB | NOT NULL (array of contributing factors) |
| model_version | VARCHAR(50) | NOT NULL |
| explanation | TEXT | NULLABLE (human-readable) |
| created_at | TIMESTAMPTZ | default NOW() |

#### `ml_models`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| model_type | ENUM('fraud_classifier','anomaly_detector','risk_scorer','behavioral_profiler') | NOT NULL |
| version | VARCHAR(50) | NOT NULL |
| status | ENUM('training','validating','active','retired','failed') | NOT NULL |
| framework | VARCHAR(50) | NOT NULL |
| metrics | JSONB | NOT NULL (accuracy, precision, recall, F1, AUC) |
| parameters | JSONB | NULLABLE (hyperparameters) |
| artifact_path | VARCHAR(500) | NOT NULL (Azure Blob path) |
| training_dataset_info | JSONB | NULLABLE |
| promoted_at | TIMESTAMPTZ | NULLABLE |
| promoted_by | UUID | FK → users(id), NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

**UNIQUE:** (name, version)

#### `watchlists`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| list_name | VARCHAR(255) | NOT NULL |
| list_type | ENUM('sanctions','pep','adverse_media','internal_blacklist','custom') | NOT NULL |
| entity_name | VARCHAR(500) | NOT NULL |
| entity_identifiers | JSONB | NOT NULL |
| source | VARCHAR(255) | NOT NULL |
| match_score | DECIMAL(5,4) | NULLABLE |
| is_active | BOOLEAN | default TRUE |
| expires_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

#### `audit_logs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users(id), NULLABLE |
| action | VARCHAR(100) | NOT NULL |
| resource_type | VARCHAR(100) | NOT NULL |
| resource_id | UUID | NULLABLE |
| details | JSONB | NULLABLE |
| ip_address | INET | NULLABLE |
| user_agent | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

**Partitioning:** Range partition by `created_at` (monthly)

#### `notifications`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| type | ENUM('fraud_alert','case_update','system','rule_trigger','model_update') | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | default FALSE |
| metadata | JSONB | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

#### `webhooks`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| url | VARCHAR(2048) | NOT NULL |
| events | VARCHAR[] | NOT NULL (array of event types) |
| secret | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | default TRUE |
| last_triggered_at | TIMESTAMPTZ | NULLABLE |
| failure_count | INTEGER | default 0 |
| created_by | UUID | FK → users(id) |
| created_at | TIMESTAMPTZ | default NOW() |

---

## API Specification (FastAPI Backend)

Base URL: `/api/v1`

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Login with email/password → JWT |
| POST | `/auth/register` | Register new user (admin only) |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke refresh token |
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/auth/me` | Get current user profile |
| PUT | `/auth/me` | Update current user profile |
| POST | `/auth/mfa/enable` | Enable MFA |
| POST | `/auth/mfa/verify` | Verify MFA token |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/transactions` | List transactions (paginated, filtered, sorted) |
| GET | `/transactions/{id}` | Get transaction detail with fraud analysis |
| POST | `/transactions` | Ingest a new transaction (triggers fraud pipeline) |
| POST | `/transactions/batch` | Batch ingest transactions |
| GET | `/transactions/{id}/risk-scores` | Get risk score history for a transaction |
| GET | `/transactions/{id}/alerts` | Get alerts linked to a transaction |
| GET | `/transactions/{id}/similar` | Find similar transactions (ML-powered) |
| POST | `/transactions/search` | Advanced search with complex filters |
| GET | `/transactions/export` | Export transactions (CSV/JSON) |

**Query Parameters for GET `/transactions`:**
- `page`, `page_size` (pagination)
- `sort_by`, `sort_order`
- `status` (filter)
- `risk_level` (filter)
- `min_amount`, `max_amount` (filter)
- `date_from`, `date_to` (filter)
- `entity_id` (filter)
- `channel` (filter)
- `country_code` (filter)

### Fraud Alerts
| Method | Endpoint | Description |
|---|---|---|
| GET | `/fraud-alerts` | List alerts (paginated, filtered) |
| GET | `/fraud-alerts/{id}` | Get alert detail with evidence |
| PUT | `/fraud-alerts/{id}/status` | Update alert status |
| PUT | `/fraud-alerts/{id}/assign` | Assign alert to analyst |
| POST | `/fraud-alerts/{id}/escalate` | Escalate alert |
| POST | `/fraud-alerts/{id}/resolve` | Resolve alert with notes |
| GET | `/fraud-alerts/statistics` | Alert statistics (counts by status, severity) |
| POST | `/fraud-alerts/{id}/create-case` | Create case from alert |

### Risk Scoring
| Method | Endpoint | Description |
|---|---|---|
| GET | `/risk-scoring/entity/{entity_id}` | Get entity risk profile |
| GET | `/risk-scoring/entity/{entity_id}/history` | Risk score history |
| POST | `/risk-scoring/calculate` | On-demand risk calculation |
| GET | `/risk-scoring/distribution` | Risk distribution across entities |
| GET | `/risk-scoring/top-risk` | Top N highest risk entities |

### Rules Engine
| Method | Endpoint | Description |
|---|---|---|
| GET | `/rules` | List all rules |
| POST | `/rules` | Create a new rule |
| GET | `/rules/{id}` | Get rule detail |
| PUT | `/rules/{id}` | Update rule |
| DELETE | `/rules/{id}` | Delete rule (soft delete) |
| PUT | `/rules/{id}/toggle` | Enable/disable rule |
| POST | `/rules/{id}/test` | Test rule against sample transaction |
| GET | `/rules/templates` | Get pre-built rule templates |
| GET | `/rules/{id}/performance` | Rule hit rate & false positive stats |

### Case Management
| Method | Endpoint | Description |
|---|---|---|
| GET | `/cases` | List cases |
| POST | `/cases` | Create a new case |
| GET | `/cases/{id}` | Get case detail |
| PUT | `/cases/{id}` | Update case |
| PUT | `/cases/{id}/assign` | Assign case |
| POST | `/cases/{id}/timeline` | Add timeline event |
| PUT | `/cases/{id}/close` | Close case with findings |
| GET | `/cases/statistics` | Case statistics |

### Analytics & Reporting
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/overview` | Dashboard overview metrics |
| GET | `/analytics/fraud-trends` | Fraud trend data (time series) |
| GET | `/analytics/transaction-volume` | Transaction volume over time |
| GET | `/analytics/risk-distribution` | Risk score distribution |
| GET | `/analytics/top-fraud-patterns` | Most common fraud patterns |
| GET | `/analytics/model-performance` | ML model performance metrics |
| GET | `/analytics/geographic` | Geographic fraud distribution |
| POST | `/analytics/reports/generate` | Generate a custom report |
| GET | `/analytics/reports/{id}/download` | Download generated report |

### Entities
| Method | Endpoint | Description |
|---|---|---|
| GET | `/entities` | List entities |
| GET | `/entities/{id}` | Entity 360 view |
| GET | `/entities/{id}/transactions` | Entity transaction history |
| GET | `/entities/{id}/alerts` | Entity fraud alerts |
| GET | `/entities/{id}/risk-profile` | Detailed risk profile |
| GET | `/entities/{id}/network` | Entity relationship network |
| PUT | `/entities/{id}/watchlist` | Add/remove from watchlist |

### ML Models
| Method | Endpoint | Description |
|---|---|---|
| GET | `/models` | List all models |
| GET | `/models/{id}` | Model detail + metrics |
| POST | `/models/{id}/promote` | Promote model to active |
| POST | `/models/{id}/retire` | Retire a model |
| GET | `/models/compare` | Compare model performance |
| POST | `/models/retrain` | Trigger model retraining |

### Watchlists
| Method | Endpoint | Description |
|---|---|---|
| GET | `/watchlists` | List watchlist entries |
| POST | `/watchlists` | Add entry to watchlist |
| DELETE | `/watchlists/{id}` | Remove entry |
| POST | `/watchlists/screen` | Screen entity against all lists |
| POST | `/watchlists/import` | Bulk import watchlist (CSV) |

### Network Analysis
| Method | Endpoint | Description |
|---|---|---|
| GET | `/network/graph` | Get transaction network graph data |
| GET | `/network/entity/{entity_id}/connections` | Entity connections |
| POST | `/network/analyze` | Run network-based fraud analysis |

### Audit
| Method | Endpoint | Description |
|---|---|---|
| GET | `/audit` | List audit logs (paginated) |
| GET | `/audit/export` | Export audit logs |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/health/detailed` | Detailed health (DB, Redis, Event Hub) |
| GET | `/settings` | Get system settings |
| PUT | `/settings` | Update system settings |
| GET | `/users` | List users (admin) |
| POST | `/users` | Create user (admin) |
| PUT | `/users/{id}` | Update user (admin) |
| DELETE | `/users/{id}` | Deactivate user (admin) |

### Webhooks
| Method | Endpoint | Description |
|---|---|---|
| GET | `/webhooks` | List webhooks |
| POST | `/webhooks` | Create webhook |
| PUT | `/webhooks/{id}` | Update webhook |
| DELETE | `/webhooks/{id}` | Delete webhook |
| POST | `/webhooks/{id}/test` | Test webhook delivery |

### WebSocket Events (Socket.IO)

**Namespaces:**
- `/alerts` — Real-time fraud alert notifications
- `/transactions` — Live transaction feed
- `/dashboard` — Dashboard metric updates

**Events Emitted (Server → Client):**
| Event | Namespace | Payload |
|---|---|---|
| `new_alert` | /alerts | Alert object |
| `alert_updated` | /alerts | Updated alert object |
| `new_transaction` | /transactions | Transaction with fraud score |
| `transaction_flagged` | /transactions | Flagged transaction detail |
| `metrics_update` | /dashboard | Updated dashboard metrics |
| `model_status` | /dashboard | Model training/deployment status |

---

## Feature Requirements

### F1: Real-Time Transaction Monitoring
- **F1.1:** Ingest transactions via REST API and Azure Event Hubs (Kafka protocol)
- **F1.2:** Process each transaction through the fraud detection pipeline in <200ms P95 latency
- **F1.3:** Display live transaction feed on dashboard with auto-refresh via WebSocket
- **F1.4:** Support batch ingestion (up to 10,000 transactions per request)
- **F1.5:** Transaction search with full-text, date range, amount range, entity, status, risk level, channel, and geography filters
- **F1.6:** Transaction detail view showing: raw data, fraud score breakdown, risk factors, linked alerts, similar transactions, entity context
- **F1.7:** Export transactions to CSV and JSON with applied filters

### F2: ML-Powered Fraud Detection
- **F2.1:** Fraud Classifier — XGBoost + Neural Network ensemble model trained on historical labeled data. Outputs fraud probability (0.0–1.0) per transaction
- **F2.2:** Anomaly Detection — Isolation Forest + Autoencoder model detecting statistical outliers in transaction patterns
- **F2.3:** Behavioral Profiling — Build per-entity behavioral baselines (typical amounts, frequencies, times, locations, channels). Flag deviations exceeding configurable thresholds
- **F2.4:** Network Analysis — Graph-based detection of fraud rings via connected component analysis and centrality metrics on transaction networks
- **F2.5:** Feature Engineering — Extract 200+ features per transaction including:
  - Transaction features: amount, currency, channel, time of day, day of week
  - Velocity features: count/sum in last 1h/6h/24h/7d/30d per entity
  - Entity features: account age, KYC status, historical fraud rate, risk score
  - Geographic features: country risk rating, distance from last transaction, impossible travel detection
  - Device features: device fingerprint frequency, new device flag, IP risk score
  - Behavioral features: deviation from average amount, unusual time, new merchant category
  - Network features: degree centrality, clustering coefficient, connected component size
- **F2.6:** Model Explainability — SHAP values for every prediction. Show top contributing features on the fraud alert detail page
- **F2.7:** Model Registry — Version, track, promote, and retire models. Compare performance metrics (accuracy, precision, recall, F1, AUC-ROC, AUC-PR) across versions
- **F2.8:** Automated Retraining — Trigger model retraining when performance degrades below configured thresholds. Use feedback loop from resolved alerts (confirmed fraud vs. false positive) as ground truth
- **F2.9:** ONNX Runtime inference for production serving (sub-10ms per prediction)

### F3: Rules Engine
- **F3.1:** Visual rule builder UI with drag-and-drop condition grouping (AND/OR logic)
- **F3.2:** Condition types:
  - Amount thresholds (>, <, between, equals)
  - Velocity checks (N transactions in T timeframe)
  - Geographic rules (blocked countries, cross-border)
  - Time-based rules (unusual hours, weekend)
  - Entity attribute checks (KYC status, account age, risk score)
  - Device/IP rules (new device, known bad IP, VPN detection)
  - Pattern rules (round amounts, structured amounts, rapid succession)
  - Custom field comparison
- **F3.3:** Actions: block transaction, flag for review, adjust risk score, create alert, notify team, trigger webhook
- **F3.4:** Rule testing — dry-run a rule against historical transactions to estimate hit rate and false positive rate before activating
- **F3.5:** Rule templates — pre-built rules for common fraud patterns (card testing, account takeover, money mules, first-party fraud)
- **F3.6:** Rule priority and execution order configuration
- **F3.7:** Rule performance dashboard showing hit counts, false positive rates, and trend over time

### F4: Fraud Alert Management
- **F4.1:** Alert list view with filtering by status, severity, type, date, assigned analyst
- **F4.2:** Alert detail view showing:
  - Transaction details
  - Fraud score with SHAP explanation
  - Rule matches (if rule-triggered)
  - Entity risk profile
  - Historical alerts for same entity
  - Similar transaction patterns
  - Evidence panel (collected data points)
- **F4.3:** Alert workflow: Open → Investigating → Escalated → Resolved (Confirmed Fraud / False Positive) / Dismissed
- **F4.4:** Alert assignment to analysts with workload balancing visibility
- **F4.5:** Bulk actions: bulk assign, bulk resolve, bulk dismiss
- **F4.6:** Alert escalation with reason and notification to senior analysts
- **F4.7:** Resolution notes (mandatory for confirmed fraud, optional for false positive)
- **F4.8:** Create investigation case from one or more related alerts
- **F4.9:** Real-time alert notifications via WebSocket, email, and SMS (configurable per severity)

### F5: Risk Scoring
- **F5.1:** Composite risk score (0.0–1.0) combining ML model output, rule triggers, behavioral deviation, entity history, and watchlist matches
- **F5.2:** Risk level classification: Low (0.0–0.3), Medium (0.3–0.6), High (0.6–0.8), Critical (0.8–1.0) — thresholds configurable
- **F5.3:** Component score breakdown: ML score, rule score, velocity score, behavioral score, network score
- **F5.4:** Risk score history per entity with trend visualization
- **F5.5:** Risk distribution dashboard showing entity count per risk tier
- **F5.6:** Top-N highest risk entities leaderboard
- **F5.7:** Risk score auto-updates on new transaction, alert resolution, or watchlist match

### F6: Case Management
- **F6.1:** Create cases manually or from fraud alerts (one or more alerts per case)
- **F6.2:** Case detail with linked alerts, transactions, entities, and evidence
- **F6.3:** Case timeline: chronological log of all actions and events
- **F6.4:** Case assignment and reassignment
- **F6.5:** Case status workflow: Open → In Progress → Pending Review → Escalated → Closed (Confirmed Fraud / False Positive)
- **F6.6:** Case findings and resolution notes (structured form + free text)
- **F6.7:** Case statistics: open/closed counts, average resolution time, confirmed fraud rate

### F7: Analytics & Reporting
- **F7.1:** Dashboard overview: total transactions (today/week/month), fraud rate, alert count by status, average fraud score, top risk entities
- **F7.2:** Fraud trend chart: fraud count and rate over time (hourly/daily/weekly/monthly)
- **F7.3:** Transaction volume chart: volume over time by channel/status
- **F7.4:** Geographic heatmap: fraud density by country/region
- **F7.5:** Pattern analysis: most common fraud types, emerging patterns
- **F7.6:** Model performance dashboard: accuracy, precision, recall, F1, AUC over time per model
- **F7.7:** Rule effectiveness report: hit rate, false positive rate, catch rate per rule
- **F7.8:** Custom report builder: select metrics, date range, filters → generate PDF/CSV
- **F7.9:** Scheduled reports: daily/weekly/monthly auto-generated and emailed

### F8: Entity Management (Customer/Merchant 360)
- **F8.1:** Entity list with search, filter by type, risk level, KYC status, watchlist status
- **F8.2:** Entity 360 view: profile info, risk score breakdown, transaction history, alerts, cases, behavioral profile, network connections
- **F8.3:** Entity risk profile: historical risk scores, contributing factors, trend
- **F8.4:** Entity transaction pattern visualization (amount distribution, time patterns, geographic spread)
- **F8.5:** Entity network graph showing connections to other entities via transactions
- **F8.6:** Watchlist screening with match scoring

### F9: Watchlist & Sanctions Screening
- **F9.1:** Manage internal watchlists (blacklist, greylist)
- **F9.2:** Integration with external sanctions lists (OFAC, UN, EU)
- **F9.3:** Fuzzy name matching with configurable match threshold
- **F9.4:** Bulk screening of entity database
- **F9.5:** Automatic screening on new entity creation or transaction
- **F9.6:** Watchlist hit alerts with match details and confidence score
- **F9.7:** CSV import/export for watchlist management

### F10: Network Graph Visualization
- **F10.1:** Interactive force-directed graph showing entities as nodes and transactions as edges
- **F10.2:** Node size/color based on risk score; edge thickness based on transaction volume
- **F10.3:** Click-to-expand node neighborhoods
- **F10.4:** Filter graph by date range, amount range, risk level
- **F10.5:** Highlight suspicious clusters and fraud rings
- **F10.6:** Zoom, pan, and minimap navigation

### F11: Authentication & Authorization
- **F11.1:** Email/password authentication with JWT (access token: 15min, refresh token: 7d)
- **F11.2:** Azure AD SSO integration via OAuth2/OIDC
- **F11.3:** Multi-factor authentication (TOTP)
- **F11.4:** Role-based access control (RBAC):
  - **Admin:** Full access, user management, system settings
  - **Analyst:** View all, manage alerts and cases, manage rules
  - **Investigator:** View all, manage assigned alerts and cases
  - **Viewer:** Read-only access to dashboards and analytics
- **F11.5:** API key authentication for system-to-system integrations
- **F11.6:** Session management with forced logout capability
- **F11.7:** Password policy: min 12 chars, complexity requirements, history check
- **F11.8:** Account lockout after 5 failed attempts (30min cooldown)

### F12: Audit Trail
- **F12.1:** Log all user actions: login, data access, CRUD operations, config changes
- **F12.2:** Log all system actions: automated alert creation, model predictions, rule executions
- **F12.3:** Tamper-proof append-only log (no updates or deletes)
- **F12.4:** Audit log viewer with filters by user, action, resource, date range
- **F12.5:** Audit log export for compliance reporting

### F13: Notifications & Webhooks
- **F13.1:** In-app notification center with unread badge and mark-as-read
- **F13.2:** Email notifications for critical and high severity alerts
- **F13.3:** SMS notifications for critical alerts (configurable)
- **F13.4:** Webhook support for external system integration (Slack, PagerDuty, SIEM)
- **F13.5:** Notification preferences per user (which events, which channels)
- **F13.6:** Webhook retry with exponential backoff (max 5 retries)
- **F13.7:** Webhook secret for HMAC signature verification

### F14: Settings & Configuration
- **F14.1:** Risk score thresholds (configurable boundaries for low/medium/high/critical)
- **F14.2:** Auto-block threshold (transactions above this fraud score are auto-blocked)
- **F14.3:** Alert auto-assignment rules
- **F14.4:** Notification channel configuration
- **F14.5:** Data retention policies
- **F14.6:** API rate limiting configuration
- **F14.7:** Feature flags for enabling/disabling ML models, rules, integrations

---

## ML Pipeline Specification

### Data Flow
```
Transaction Ingested
    │
    ├─→ Feature Engineering (200+ features extracted)
    │
    ├─→ Rules Engine (parallel evaluation of all active rules)
    │
    ├─→ ML Models (parallel inference):
    │       ├── Fraud Classifier (XGBoost ensemble) → fraud probability
    │       ├── Anomaly Detector (Isolation Forest) → anomaly score
    │       └── Behavioral Profiler → deviation score
    │
    ├─→ Risk Score Aggregation (weighted combination)
    │
    ├─→ Decision Engine:
    │       ├── score < 0.3  → PASS (low risk)
    │       ├── 0.3 ≤ score < 0.6 → FLAG for review
    │       ├── 0.6 ≤ score < 0.8 → ALERT (high priority)
    │       └── score ≥ 0.8 → BLOCK + ALERT (critical)
    │
    └─→ Post-Processing:
            ├── Update entity risk profile
            ├── Create fraud alert (if triggered)
            ├── Send notifications (if configured)
            ├── Emit WebSocket event
            └── Log to audit trail
```

### Model Training Pipeline
```
1. Data Collection → Pull labeled transaction data from PostgreSQL
2. Feature Engineering → Transform raw data into 200+ features
3. Train/Test Split → 80/20 stratified split with time-based ordering
4. Model Training → XGBoost, Isolation Forest, Autoencoder, Neural Net
5. Evaluation → Precision, Recall, F1, AUC-ROC, AUC-PR on test set
6. Comparison → Compare against current production model
7. Export → Serialize to ONNX format
8. Register → Push to Azure ML model registry
9. Validate → Run validation suite on staging data
10. Promote → Deploy to production (via API, requires approval in prod)
```

### Feature Categories
| Category | Count | Examples |
|---|---|---|
| Transaction | ~20 | amount, currency, channel, merchant_category, card_present |
| Temporal | ~15 | hour_of_day, day_of_week, is_weekend, is_holiday, minutes_since_last_txn |
| Velocity (1h) | ~10 | txn_count_1h, txn_sum_1h, unique_merchants_1h, unique_countries_1h |
| Velocity (24h) | ~10 | txn_count_24h, txn_sum_24h, unique_merchants_24h, max_amount_24h |
| Velocity (7d) | ~10 | txn_count_7d, txn_sum_7d, avg_amount_7d, std_amount_7d |
| Velocity (30d) | ~10 | txn_count_30d, txn_sum_30d, avg_amount_30d |
| Entity | ~20 | account_age_days, kyc_status, historical_fraud_count, avg_txn_amount_lifetime |
| Geographic | ~15 | country_risk_score, distance_from_last_txn_km, is_cross_border, impossible_travel |
| Device | ~15 | is_new_device, device_seen_count, ip_risk_score, is_vpn, is_tor |
| Behavioral | ~25 | amount_zscore, time_deviation, new_merchant_flag, unusual_channel |
| Network | ~15 | in_degree, out_degree, clustering_coeff, component_size, pagerank |
| Derived | ~35 | amount_to_avg_ratio, velocity_acceleration, pattern_regularity_score |

---

## Non-Functional Requirements

### Performance
- Transaction fraud scoring: <200ms P95 latency end-to-end
- ML model inference: <10ms per model via ONNX Runtime
- API response time: <100ms P95 for read operations, <500ms P95 for writes
- Dashboard load time: <2 seconds initial load
- WebSocket event delivery: <100ms from detection to client
- Support 1,000 transactions/second sustained throughput
- Support 10,000 concurrent WebSocket connections

### Scalability
- Horizontal scaling via Azure Container Apps (auto-scale 2–20 replicas per service)
- Database connection pooling (min: 10, max: 100 per instance)
- Redis cluster for distributed caching and session storage
- Event Hub partitioning for parallel stream processing (32 partitions)
- Database table partitioning for transactions and audit logs (monthly)

### Reliability
- 99.9% uptime SLA
- Automated health checks with self-healing restarts
- Circuit breaker pattern for external service calls
- Graceful degradation: if ML service is down, fall back to rules-only scoring
- Dead letter queue for failed event processing (retry 3x, then DLQ)
- Database point-in-time recovery (35-day retention)
- Automated backups every 6 hours

### Security
- All data encrypted at rest (AES-256) and in transit (TLS 1.3)
- Azure Key Vault for all secrets (DB credentials, API keys, JWT secrets)
- Managed identities for service-to-service auth (no stored credentials)
- Network security: VNet integration, private endpoints for DB/Redis/Storage
- WAF (Web Application Firewall) via Azure Front Door
- API rate limiting: 100 req/min for auth endpoints, 1000 req/min for data endpoints
- Input validation on all endpoints (Pydantic + custom validators)
- SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- XSS prevention via React's default escaping + CSP headers
- CORS configured to allow only frontend origin
- PII encryption at field level for sensitive data (SSN, card numbers)
- Dependency vulnerability scanning (Dependabot + Snyk)
- Container image scanning (Trivy)

### Compliance
- SOC 2 Type II audit trail requirements
- PCI DSS compliance for cardholder data handling
- GDPR: data subject access requests, right to erasure (soft delete with anonymization)
- Data retention policies: configurable per data type
- Immutable audit logs

### Observability
- Structured JSON logging (structlog) to Azure Log Analytics
- Distributed tracing with OpenTelemetry → Application Insights
- Custom metrics: transactions processed, fraud rate, model latency, alert volumes
- Azure Monitor dashboards for infrastructure health
- Alert rules for: error rate >1%, latency P95 >500ms, fraud rate spike, model drift
- Log correlation IDs across all services

---

## Deployment Architecture (Azure)

### Environment Strategy
| Environment | Purpose | Trigger |
|---|---|---|
| Development | Feature development | Manual / branch push |
| Staging | Pre-production validation | Auto on merge to `main` |
| Production | Live system | Manual trigger + approval gate |

### Azure Resource Topology
```
Azure Subscription
├── Resource Group: finshield-{env}-rg
│
├── Networking
│   ├── Virtual Network: finshield-{env}-vnet (10.0.0.0/16)
│   │   ├── Subnet: container-apps (10.0.1.0/24)
│   │   ├── Subnet: database (10.0.2.0/24)
│   │   ├── Subnet: cache (10.0.3.0/24)
│   │   └── Subnet: private-endpoints (10.0.4.0/24)
│   ├── NSGs per subnet
│   └── Private DNS Zones
│
├── Compute
│   ├── Container Apps Environment: finshield-{env}-cae
│   │   ├── Container App: frontend (Next.js, min: 2, max: 10)
│   │   ├── Container App: backend-api (FastAPI, min: 2, max: 20)
│   │   ├── Container App: backend-worker (Celery, min: 2, max: 10)
│   │   └── Container App: backend-stream (Event consumer, min: 2, max: 10)
│   └── Container Registry: finshieldacr{env}
│
├── Data
│   ├── PostgreSQL Flexible Server: finshield-{env}-pg
│   │   ├── SKU: Standard_D4ds_v5 (prod) / Standard_B2ms (dev/staging)
│   │   ├── Storage: 256GB (prod) / 64GB (dev/staging)
│   │   ├── High Availability: Zone-redundant (prod only)
│   │   └── Databases: finshield, finshield_test
│   └── Azure Cache for Redis: finshield-{env}-redis
│       ├── SKU: Premium P1 (prod) / Standard C1 (dev/staging)
│       └── Cluster: enabled (prod only)
│
├── Messaging
│   └── Event Hubs Namespace: finshield-{env}-eh
│       ├── Hub: transactions (32 partitions, 7-day retention)
│       ├── Hub: alerts (16 partitions, 7-day retention)
│       └── Consumer Groups: fraud-processor, analytics, audit
│
├── Storage
│   └── Storage Account: finshield{env}sa
│       ├── Container: ml-models (model artifacts)
│       ├── Container: reports (generated reports)
│       ├── Container: exports (data exports)
│       └── Container: terraform-state (IaC state)
│
├── AI/ML
│   └── Azure ML Workspace: finshield-{env}-ml
│       ├── Model Registry
│       ├── Compute Instances (training)
│       └── Managed Endpoints (optional)
│
├── Security
│   ├── Key Vault: finshield-{env}-kv
│   │   ├── Secrets: db-connection-string, redis-connection-string,
│   │   │           jwt-secret, event-hub-connection, sendgrid-api-key,
│   │   │           twilio-credentials, encryption-key
│   │   └── Access Policies: managed identities only
│   └── Managed Identities: one per Container App
│
├── Monitoring
│   ├── Log Analytics Workspace: finshield-{env}-logs
│   ├── Application Insights: finshield-{env}-appinsights
│   └── Azure Monitor Alert Rules:
│       ├── High error rate (>1% over 5min)
│       ├── High latency (P95 >500ms over 5min)
│       ├── Container restart loop
│       ├── Database CPU >80%
│       ├── Redis memory >80%
│       └── Fraud rate anomaly
│
└── CDN/WAF
    └── Azure Front Door: finshield-{env}-fd
        ├── Frontend: finshield-{env}.azurefd.net
        ├── Custom domain: app.finshield.com (prod)
        ├── WAF Policy: OWASP 3.2 rule set
        ├── Rate limiting rules
        └── Origins: frontend Container App, backend Container App
```

### Container Specifications

#### Frontend (Next.js)
```yaml
image: finshieldacr.azurecr.io/frontend:{{tag}}
cpu: 0.5
memory: 1Gi
min_replicas: 2
max_replicas: 10
scale_rule: http_concurrent_requests > 50
health_probe: /api/health (HTTP GET, port 3000)
env:
  - NEXT_PUBLIC_API_URL
  - NEXTAUTH_URL
  - NEXTAUTH_SECRET (from Key Vault)
  - AZURE_AD_CLIENT_ID (from Key Vault)
  - AZURE_AD_CLIENT_SECRET (from Key Vault)
```

#### Backend API (FastAPI)
```yaml
image: finshieldacr.azurecr.io/backend-api:{{tag}}
cpu: 1.0
memory: 2Gi
min_replicas: 2
max_replicas: 20
scale_rule: http_concurrent_requests > 100
health_probe: /api/v1/health (HTTP GET, port 8000)
env:
  - DATABASE_URL (from Key Vault)
  - REDIS_URL (from Key Vault)
  - JWT_SECRET (from Key Vault)
  - EVENT_HUB_CONNECTION (from Key Vault)
  - AZURE_STORAGE_CONNECTION (from Key Vault)
  - ML_MODEL_PATH
  - LOG_LEVEL
```

#### Backend Worker (Celery)
```yaml
image: finshieldacr.azurecr.io/backend-worker:{{tag}}
cpu: 1.0
memory: 2Gi
min_replicas: 2
max_replicas: 10
scale_rule: celery_queue_length > 100
command: celery -A app.worker worker --loglevel=info --concurrency=4
env: (same as backend-api)
```

#### Stream Processor (Event Hub Consumer)
```yaml
image: finshieldacr.azurecr.io/backend-stream:{{tag}}
cpu: 1.0
memory: 2Gi
min_replicas: 2
max_replicas: 10
scale_rule: event_hub_lag > 1000
command: python -m app.streaming.consumer
env: (same as backend-api)
```

---

## CI/CD Pipeline Specification

### CI Pipeline (`ci.yml`) — Runs on Every PR

```yaml
triggers: pull_request to main

jobs:
  frontend-checks:
    - Checkout code
    - Setup Node.js 20
    - Install dependencies (npm ci)
    - Lint (eslint)
    - Type check (tsc --noEmit)
    - Unit tests (vitest run --coverage)
    - Build (next build)
    - E2E tests (playwright, against mock API)

  backend-checks:
    - Checkout code
    - Setup Python 3.12
    - Install dependencies (poetry install)
    - Lint (ruff check)
    - Format check (ruff format --check)
    - Type check (mypy)
    - Unit tests (pytest tests/unit --cov)
    - Integration tests (pytest tests/integration, with test PostgreSQL + Redis via services)

  security-scan:
    - Dependency audit (npm audit, pip-audit)
    - SAST scan (Semgrep)
    - Secret detection (Gitleaks)
```

### CD Staging Pipeline (`cd-staging.yml`) — Runs on Merge to `main`

```yaml
triggers: push to main

jobs:
  build-and-push:
    - Checkout code
    - Login to ACR
    - Build frontend Docker image, tag with commit SHA
    - Build backend Docker image, tag with commit SHA
    - Push images to ACR
    - Run Trivy container scan on images

  deploy-staging:
    needs: build-and-push
    - Login to Azure
    - Update Container App revisions (frontend, backend-api, backend-worker, backend-stream)
    - Run database migrations (alembic upgrade head)
    - Wait for health checks to pass
    - Run smoke tests against staging
    - Notify team (Slack webhook)

  integration-tests:
    needs: deploy-staging
    - Run full integration test suite against staging
    - Run load tests (Locust, 5-minute burst)
    - Report results
```

### CD Production Pipeline (`cd-production.yml`) — Manual Trigger

```yaml
triggers: workflow_dispatch (manual)

jobs:
  approval:
    - Environment: production (requires reviewer approval in GitHub)

  deploy-production:
    needs: approval
    - Login to Azure
    - Blue-green deployment:
      1. Deploy new revision (0% traffic)
      2. Run health checks on new revision
      3. Shift 10% traffic to new revision
      4. Monitor error rates for 5 minutes
      5. If error rate < 0.1%: shift to 100%
      6. If error rate >= 0.1%: rollback to previous revision
    - Run database migrations
    - Invalidate CDN cache
    - Tag release in git
    - Notify team

  post-deploy-validation:
    needs: deploy-production
    - Run smoke tests against production
    - Verify health endpoints
    - Check Application Insights for error spikes
    - Generate deployment report
```

### Infrastructure Pipeline (`infrastructure.yml`)

```yaml
triggers: push to main (paths: infrastructure/**)

jobs:
  terraform-plan:
    - Checkout code
    - Setup Terraform
    - terraform init
    - terraform validate
    - terraform plan -out=tfplan
    - Post plan as PR comment (if PR)

  terraform-apply:
    needs: terraform-plan
    if: github.ref == 'refs/heads/main'
    environment: infrastructure (requires approval)
    - terraform apply tfplan
    - Output resource URLs and connection info
```

### ML Pipeline (`ml-pipeline.yml`)

```yaml
triggers: workflow_dispatch / schedule (weekly)

jobs:
  data-preparation:
    - Extract labeled data from production DB (via read replica)
    - Feature engineering
    - Train/test split
    - Upload to Azure ML datastore

  model-training:
    - Train fraud classifier (XGBoost)
    - Train anomaly detector (Isolation Forest)
    - Train behavioral profiler
    - Evaluate all models
    - Compare with current production models

  model-registration:
    if: new model outperforms current
    - Export to ONNX format
    - Register in Azure ML model registry
    - Upload artifact to Blob Storage
    - Create model record in database
    - Notify team for review/promotion
```

---

## Local Development Setup

### Prerequisites
- Node.js 20+
- Python 3.12+
- Poetry (Python package manager)
- Docker Desktop
- Azure CLI (for cloud resource access)

### Quick Start
```bash
# Clone repository
git clone <repo-url> && cd project7

# Start infrastructure (PostgreSQL, Redis, Event Hub emulator)
docker-compose up -d

# Backend setup
cd backend
cp .env.example .env
poetry install
poetry run alembic upgrade head
poetry run python scripts/seed_data.py
poetry run uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Makefile Commands
```makefile
make dev              # Start everything (docker + backend + frontend)
make backend          # Start backend only
make frontend         # Start frontend only
make db-migrate       # Run database migrations
make db-seed          # Seed database with test data
make test             # Run all tests
make test-backend     # Run backend tests
make test-frontend    # Run frontend tests
make lint             # Lint all code
make format           # Format all code
make build            # Build Docker images locally
make train-models     # Run model training pipeline
make docs             # Open API docs
```

### Docker Compose Services
```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: finshield
      POSTGRES_USER: finshield
      POSTGRES_PASSWORD: localdev123
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  eventhub-emulator:
    image: mcr.microsoft.com/azure-messaging/eventhubs-emulator:latest
    ports: ["5672:5672"]

  mailhog:
    image: mailhog/mailhog
    ports: ["1025:1025", "8025:8025"]  # SMTP + UI
```

### Environment Variables

#### Backend (.env)
```
# Database
DATABASE_URL=postgresql+asyncpg://finshield:localdev123@localhost:5432/finshield

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=local-dev-secret-change-in-prod
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Event Hub (emulator)
EVENT_HUB_CONNECTION_STRING=Endpoint=sb://localhost;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=localkey

# Azure Storage (Azurite emulator)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=...;BlobEndpoint=http://localhost:10000/devstoreaccount1

# ML
ML_MODEL_PATH=app/ml/models
ML_FRAUD_MODEL_VERSION=latest

# Email (MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025

# App
APP_ENV=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=local-dev-secret
```

---

## Coding Conventions

### Python (Backend)
- Follow PEP 8 via ruff
- Use async/await for all I/O operations
- Type hints on all function signatures
- Docstrings on public functions (Google style)
- Service layer pattern: API routes → Services → Repositories/Models
- Dependency injection via FastAPI's Depends()
- Use Pydantic models for all request/response schemas
- Custom exceptions inheriting from base app exceptions
- Structured logging with correlation IDs

### TypeScript (Frontend)
- Strict TypeScript (no `any` unless absolutely necessary)
- Functional components only (no class components)
- Custom hooks for reusable logic
- Colocate components with their types and tests
- Use `cn()` utility for conditional Tailwind classes
- Server components by default, client components only when needed
- Prefer server-side data fetching in page components
- Use Zod schemas that mirror backend Pydantic schemas

### Git
- Branch naming: `feature/`, `fix/`, `hotfix/`, `chore/`
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- Squash merge PRs to main
- Require PR review from at least 1 team member
- All CI checks must pass before merge

---

## Testing Strategy

### Backend
| Type | Tool | Coverage Target | What |
|---|---|---|---|
| Unit | pytest | 80% | Services, ML pipeline, rules engine, feature engineering |
| Integration | pytest + httpx | 70% | API endpoints, database operations, full transaction flow |
| Load | Locust | N/A | 1000 TPS sustained for 10 min, P95 <200ms |

### Frontend
| Type | Tool | Coverage Target | What |
|---|---|---|---|
| Unit | Vitest + RTL | 75% | Components, hooks, utilities |
| E2E | Playwright | Critical paths | Auth flow, dashboard, transaction list, alert management, rule builder |

### ML Models
| Type | What |
|---|---|
| Data validation | Schema checks, distribution drift detection |
| Model validation | Precision >0.85, Recall >0.75, AUC-ROC >0.92 on holdout set |
| Shadow scoring | Run new model in shadow mode alongside production for 48h |
| A/B testing | 10% traffic to new model, compare fraud catch rate |

---

## Seed Data Specification

The seed script (`backend/scripts/seed_data.py`) generates:
- 10 users (2 admin, 4 analyst, 2 investigator, 2 viewer)
- 5,000 entities (3,500 individuals, 1,000 businesses, 500 merchants)
- 100,000 transactions (spanning 90 days, ~2% labeled fraud)
- 2,000 fraud alerts (mix of statuses and severities)
- 50 investigation cases
- 20 active rules (from templates)
- 3 ML models (1 active, 1 retired, 1 training)
- 500 watchlist entries
- 50,000 audit log entries

Default admin credentials for local dev:
- Email: `admin@finshield.local`
- Password: `Admin123!@#`

---

## Glossary

| Term | Definition |
|---|---|
| **Fraud Score** | ML-generated probability (0.0–1.0) that a transaction is fraudulent |
| **Risk Score** | Composite score combining ML, rules, behavioral, and entity factors |
| **Velocity Check** | Rule that counts transaction frequency within a time window |
| **Entity** | Any participant in a transaction — individual, business, or merchant |
| **Fraud Ring** | Connected cluster of entities involved in coordinated fraud |
| **False Positive** | A legitimate transaction incorrectly flagged as fraud |
| **SAR** | Suspicious Activity Report — regulatory filing for confirmed fraud |
| **KYC** | Know Your Customer — identity verification process |
| **AML** | Anti-Money Laundering — regulations for detecting money laundering |
| **SHAP** | SHapley Additive exPlanations — ML model interpretability method |
| **ONNX** | Open Neural Network Exchange — portable model format |
| **Dead Letter Queue** | Queue for messages that failed processing after max retries |
| **Shadow Mode** | Running a model alongside production without affecting decisions |
| **Feature Drift** | Statistical shift in input features over time, degrading model accuracy |

---

## Implementation Order

### Phase 1: Foundation (Weeks 1–3)
1. Project scaffolding (Next.js + FastAPI + Docker Compose)
2. Database schema + migrations
3. Authentication (JWT + RBAC)
4. User management CRUD
5. Basic UI shell (sidebar, topbar, auth pages)

### Phase 2: Core Transaction Pipeline (Weeks 4–6)
6. Transaction ingestion API (REST + batch)
7. Feature engineering module
8. Rules engine (core logic + CRUD API)
9. Transaction list + detail UI
10. Basic dashboard with mock data

### Phase 3: ML & Fraud Detection (Weeks 7–9)
11. Fraud classifier training pipeline
12. Anomaly detection model
13. ONNX export + inference pipeline
14. Risk score aggregation
15. ML model registry API + UI

### Phase 4: Alert & Case Management (Weeks 10–12)
16. Fraud alert creation + management API
17. Alert UI (list, detail, workflow)
18. Case management API + UI
19. Notification system (in-app, email)
20. Real-time WebSocket events

### Phase 5: Analytics & Advanced Features (Weeks 13–15)
21. Analytics endpoints + dashboard charts
22. Entity 360 view
23. Network graph visualization
24. Watchlist/sanctions screening
25. Rule builder UI (visual)
26. Audit trail

### Phase 6: Infrastructure & Deployment (Weeks 16–18)
27. Terraform modules for all Azure resources
28. CI/CD pipelines (GitHub Actions)
29. Event Hub integration (streaming)
30. Azure Front Door + WAF
31. Monitoring + alerting
32. Load testing + performance optimization

### Phase 7: Hardening & Launch (Weeks 19–20)
33. Security audit + penetration testing
34. Compliance review
35. Documentation
36. Production deployment
37. Seed production with initial rules + watchlists
38. Go-live monitoring

---

*This PRD is the single source of truth for the FinShield AI project. All development should reference this document for requirements, architecture, and conventions.*
