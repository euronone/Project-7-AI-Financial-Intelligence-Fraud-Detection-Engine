from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.risk_scoring import router as risk_scoring_router
from app.api.v1.models import router as models_router

app = FastAPI(
    title="FinShield AI API",
    description="AI Financial Intelligence & Fraud Detection Engine",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# F5 — Risk Scoring
app.include_router(risk_scoring_router, prefix="/api/v1")

# Phase 3 — ML Model Registry (F2.7 / F2.8 / F2.9)
app.include_router(models_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to FinShield AI API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
