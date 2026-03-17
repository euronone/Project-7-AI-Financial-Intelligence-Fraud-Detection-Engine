"""Phase 3 — #15: Pydantic v2 schemas for the ML Model Registry API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    FRAUD_CLASSIFIER = "fraud_classifier"
    ANOMALY_DETECTOR = "anomaly_detector"
    RISK_SCORER = "risk_scorer"
    BEHAVIORAL_PROFILER = "behavioral_profiler"


class ModelStatus(str, Enum):
    TRAINING = "training"
    VALIDATING = "validating"
    ACTIVE = "active"
    RETIRED = "retired"
    FAILED = "failed"


class ModelMetrics(BaseModel):
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    precision: Optional[float] = Field(None, ge=0.0, le=1.0)
    recall: Optional[float] = Field(None, ge=0.0, le=1.0)
    f1: Optional[float] = Field(None, ge=0.0, le=1.0)
    auc_roc: Optional[float] = Field(None, ge=0.0, le=1.0)
    auc_pr: Optional[float] = Field(None, ge=0.0, le=1.0)
    n_train_samples: Optional[int] = None

    model_config = {"extra": "allow"}   # allow additional metrics


class RegisteredModelResponse(BaseModel):
    id: str
    name: str
    model_type: ModelType
    version: str
    status: ModelStatus
    metrics: Dict = Field(default_factory=dict)
    artifact_path: str = ""
    training_dataset_info: Dict = Field(default_factory=dict)
    description: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RegisterModelRequest(BaseModel):
    name: str = Field(..., min_length=1)
    model_type: ModelType
    version: str = Field(..., min_length=1)
    description: str = ""
    metrics: Dict = Field(default_factory=dict)
    artifact_path: str = ""
    training_dataset_info: Dict = Field(default_factory=dict)


class UpdateMetricsRequest(BaseModel):
    metrics: Dict = Field(..., description="Metrics to merge into existing record")


class RetrainRequest(BaseModel):
    model_type: ModelType
    n_samples: int = Field(10_000, ge=1_000, le=200_000)
    reason: str = Field("", description="Why retraining was triggered")


class RetrainResponse(BaseModel):
    job_id: str
    model_type: ModelType
    status: str
    message: str
    metrics: Dict = Field(default_factory=dict)


class InferenceRequest(BaseModel):
    features: List[List[float]] = Field(
        ..., description="2-D array: [[f1, f2, ...], ...]"
    )


class InferenceResponse(BaseModel):
    model_id: str
    model_name: str
    version: str
    probabilities: List[float]
    predictions: List[bool]
    latency_ms: float
    backend: str
