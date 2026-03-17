from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.risk_scoring import router as risk_scoring_router

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

@app.get("/")
async def root():
    return {"message": "Welcome to FinShield AI API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/v1/ml/models")
async def get_ml_models():
    # Mock data for now, would typically come from DB or registry
    return [
        {"id": "xgb_fraud", "name": "XGBoost Fraud Classifier", "version": "v1.2.0", "status": "Active", "accuracy": 0.95, "type": "Classification"},
        {"id": "if_anomaly", "name": "Isolation Forest Anomaly Detector", "version": "v1.0.1", "status": "Active", "accuracy": 0.89, "type": "Anomaly Detection"},
        {"id": "nn_behavioral", "name": "Neural Net Behavioral Profiler", "version": "v2.0.0", "status": "Shadow", "accuracy": 0.92, "type": "Profiling"},
        {"id": "graph_network", "name": "Network Analyzer", "version": "v1.0.0", "status": "Active", "accuracy": 0.91, "type": "Graph Analysis"},
    ]
