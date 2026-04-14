"""Central API router — registers all v1 sub-routers."""

from fastapi import APIRouter
from app.api.v1 import (
    health,
    auth,
    transactions,
    fraud_alerts,
    analytics,
    settings,
    customers,
    data_sources,
    simulator,
    ml_details,
    ml_training,
    users,
    data_sync,
    credentials,
)

api_router = APIRouter(prefix="/api/v1")

# ── Core ──────────────────────────────────────────────────────────────────────
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(transactions.router)
api_router.include_router(fraud_alerts.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)

# ── Feature additions ─────────────────────────────────────────────────────────
api_router.include_router(customers.router)  # /api/v1/customers/...
api_router.include_router(data_sources.router)  # /api/v1/data-sources/...
api_router.include_router(simulator.router)  # /api/v1/simulator/...
api_router.include_router(ml_details.router)  # /api/v1/ml/...
api_router.include_router(ml_training.router)  # /api/v1/ml/training/...
api_router.include_router(users.router)  # /api/v1/users/...
api_router.include_router(data_sync.router)  # /api/v1/data-sync/...
api_router.include_router(credentials.router)  # /api/v1/credentials/...
