import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ml_model import ModelStatus, ModelType


class MLModelResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_type: ModelType
    version: str
    status: ModelStatus
    framework: str
    metrics: dict
    parameters: dict | None
    artifact_path: str
    training_dataset_info: dict | None
    promoted_at: datetime | None
    promoted_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MLModelListResponse(BaseModel):
    total: int
    items: list[MLModelResponse]


class ModelCompareResponse(BaseModel):
    models: list[MLModelResponse]
    metric_comparison: dict


class PipelineResultResponse(BaseModel):
    overall_score: float
    risk_level: str
    component_scores: dict
    risk_factors: list[dict]
    fraud_result: dict
    anomaly_result: dict
    behavioral_result: dict
    network_result: dict
    explanation: dict
    feature_count: int


class RiskScoreResponse(BaseModel):
    id: uuid.UUID
    entity_id: uuid.UUID
    transaction_id: uuid.UUID | None
    overall_score: float
    component_scores: dict
    risk_factors: dict
    model_version: str
    explanation: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskScoreListResponse(BaseModel):
    total: int
    items: list[RiskScoreResponse]


class RiskDistribution(BaseModel):
    low: int
    medium_low: int
    medium: int
    high: int
    critical: int
    total: int


class TopRiskEntity(BaseModel):
    entity_id: str
    entity_name: str | None
    risk_score: float
    risk_level: str
    last_scored: datetime | None
