from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    audit,
    auth,
    cases,
    entities,
    fraud_alerts,
    health,
    models,
    network,
    risk_scoring,
    rules,
    settings,
    transactions,
    users,
    watchlists,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/v1/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/v1/users", tags=["Users"])
api_router.include_router(transactions.router, prefix="/v1/transactions", tags=["Transactions"])
api_router.include_router(entities.router, prefix="/v1/entities", tags=["Entities"])
api_router.include_router(watchlists.router, prefix="/v1/watchlists", tags=["Watchlists"])
api_router.include_router(rules.router, prefix="/v1/rules", tags=["Rules Engine"])
api_router.include_router(models.router, prefix="/v1/models", tags=["ML Models"])
api_router.include_router(risk_scoring.router, prefix="/v1/risk", tags=["Risk Scoring"])
api_router.include_router(fraud_alerts.router, prefix="/v1/alerts", tags=["Fraud Alerts"])
api_router.include_router(cases.router, prefix="/v1/cases", tags=["Case Management"])
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics & Reporting"])
api_router.include_router(network.router, prefix="/v1/network", tags=["Network Analysis"])
api_router.include_router(audit.router, prefix="/v1/audit", tags=["Audit & Notifications"])
api_router.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])
api_router.include_router(settings.router, prefix="/v1/settings", tags=["Settings"])
