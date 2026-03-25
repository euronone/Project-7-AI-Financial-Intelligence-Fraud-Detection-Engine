# Architecture

## High-Level Components
- **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS, Zustand, React Query
- **Backend API:** FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic v2
- **Background Workers:** Celery + Redis
- **Stream Processing:** Azure Event Hubs + python-socketio
- **Database:** PostgreSQL 16 (Azure Flexible Server)
- **Cache/Queue:** Redis 7 (Azure Cache for Redis)
- **AI/ML:** scikit-learn, XGBoost, PyTorch, ONNX Runtime, Azure ML
- **Infrastructure:** Azure Container Apps, Terraform, Azure Front Door

## Layering (Backend)
- **API Routes (`api/v1/`):** HTTP request/response handling, dependency injection.
- **Services (`services/`):** Core business logic, orchestration.
- **ML Pipeline (`ml/`):** Feature engineering, model inference, SHAP explanations.
- **Rules Engine (`rules/`):** Rule evaluation, condition parsing.
- **Repositories/Models (`models/`):** SQLAlchemy ORM, database interactions.
- **Streaming (`streaming/`):** Event Hub consumers/producers, WebSocket manager.

## ML Pipeline Flow
1. Transaction Ingested
2. Feature Engineering (200+ features extracted)
3. Rules Engine & ML Models (parallel execution)
4. Risk Score Aggregation
5. Decision Engine (Pass, Flag, Alert, Block)
6. Post-Processing (Update risk profile, create alerts, emit WebSockets, audit log)

## Principles
- Clean architecture with service layer pattern
- Real-time, event-driven processing
- High availability and auto-scaling
- Secure by default (RBAC, Key Vault, VNet integration)
- Observable and testable (structlog, OpenTelemetry)
