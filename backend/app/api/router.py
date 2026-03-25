"""Central API router — registers all v1 sub-routers."""
from fastapi import APIRouter
from app.api.v1 import health, auth, transactions, fraud_alerts, analytics, settings

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(transactions.router)
api_router.include_router(fraud_alerts.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
