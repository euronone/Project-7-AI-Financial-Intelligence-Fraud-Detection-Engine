from __future__ import annotations

from pydantic import BaseModel, Field


class NetworkNode(BaseModel):
    id: str
    label: str
    entity_type: str
    risk_score: float = 0.0
    risk_level: str = "low"
    alert_count: int = 0
    transaction_count: int = 0
    country_code: str | None = None


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int = 1
    total_amount: float = 0.0
    avg_fraud_score: float = 0.0
    is_suspicious: bool = False


class NetworkGraphStats(BaseModel):
    node_count: int = 0
    edge_count: int = 0
    cluster_count: int = 0
    avg_connections: float = 0.0


class NetworkGraphResponse(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    stats: NetworkGraphStats


class ConnectionDetail(BaseModel):
    connected_entity_id: str
    name: str
    type: str
    transaction_count: int
    total_amount: float
    direction: str


class EntityConnectionResponse(BaseModel):
    entity_id: str
    entity_name: str
    connections: list[ConnectionDetail]


class NetworkAnalysisRequest(BaseModel):
    entity_ids: list[str] | None = None
    min_transactions: int = Field(default=2, ge=1)
    include_indirect: bool = False
    max_depth: int = Field(default=2, ge=1, le=5)


class ClusterInfo(BaseModel):
    cluster_id: int
    node_count: int
    risk_score: float
    is_suspicious: bool
    nodes: list[str]


class RiskPath(BaseModel):
    path: list[str]
    risk_score: float


class NetworkAnalysisResponse(BaseModel):
    clusters: list[ClusterInfo]
    risk_paths: list[RiskPath]
    overall_risk: float = 0.0
