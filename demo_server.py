#!/usr/bin/env python3
"""
Simple demo server for FinShield AI - runs without Docker dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import random
import time

app = FastAPI(
    title="FinShield AI Demo",
    description="AI Financial Intelligence & Fraud Detection Engine - Demo Version",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
users_db = {
    "admin@finshield.dev": {
        "id": 1,
        "email": "admin@finshield.dev",
        "name": "Admin User",
        "role": "admin"
    }
}

class Transaction(BaseModel):
    id: str
    amount: float
    source_account: str
    destination_account: str
    timestamp: str
    risk_score: Optional[float] = None
    status: Optional[str] = None

class FraudAlert(BaseModel):
    id: str
    transaction_id: str
    risk_level: str
    description: str
    created_at: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict

# Mock transactions
transactions = [
    Transaction(
        id=f"txn_{i:04d}",
        amount=round(random.uniform(10, 5000), 2),
        source_account=f"ACC{random.randint(10000, 99999)}",
        destination_account=f"ACC{random.randint(10000, 99999)}",
        timestamp="2024-03-21T10:30:00Z",
        risk_score=round(random.uniform(0.1, 0.9), 2),
        status=random.choice(["PENDING", "APPROVED", "BLOCKED"])
    ) for i in range(1, 51)
]

fraud_alerts = [
    FraudAlert(
        id=f"alert_{i:03d}",
        transaction_id=f"txn_{random.randint(1, 50):04d}",
        risk_level=random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        description=f"Fraud pattern detected in transaction {i}",
        created_at="2024-03-21T10:30:00Z"
    ) for i in range(1, 21)
]

@app.get("/")
async def root():
    return {"message": "FinShield AI Demo Server is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    if login_data.email == "admin@finshield.dev" and login_data.password == "Admin123!@#":
        return {
            "access_token": "demo_token_12345",
            "refresh_token": "demo_refresh_token_67890",
            "user": users_db[login_data.email]
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/v1/auth/me")
async def get_current_user():
    return users_db["admin@finshield.dev"]

@app.post("/api/v1/auth/signup", response_model=LoginResponse)
async def signup(signup_data: LoginRequest):
    # For demo purposes, allow any signup but return the same admin user
    return {
        "access_token": "demo_token_12345",
        "refresh_token": "demo_refresh_token_67890",
        "user": users_db["admin@finshield.dev"]
    }

@app.get("/api/v1/transactions", response_model=List[Transaction])
async def get_transactions():
    return transactions

@app.get("/api/v1/fraud-alerts", response_model=List[FraudAlert])
async def get_fraud_alerts():
    return fraud_alerts

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    return {
        "total_transactions": len(transactions),
        "fraud_blocked": sum(1 for t in transactions if t.status == "BLOCKED"),
        "avg_risk_score": round(sum(t.risk_score or 0 for t in transactions) / len(transactions), 2),
        "active_alerts": len(fraud_alerts),
        "system_status": "operational"
    }

@app.get("/api/v1/analytics/risk-distribution")
async def get_risk_distribution():
    distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for alert in fraud_alerts:
        distribution[alert.risk_level] += 1
    return distribution

if __name__ == "__main__":
    print("🚀 Starting FinShield AI Demo Server...")
    print("📍 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔐 Default credentials: admin@finshield.dev / Admin123!@#")
    print("⚠️  This is a demo version without ML models or database")
    
    uvicorn.run(
        "demo_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )