export interface PipelineResult {
  overall_score: number;
  risk_level: string;
  component_scores: Record<string, number>;
  risk_factors: Array<{
    factor: string;
    score: number;
    source: string;
    details?: Record<string, unknown>;
  }>;
  fraud_result: Record<string, unknown>;
  anomaly_result: Record<string, unknown>;
  behavioral_result: Record<string, unknown>;
  network_result: Record<string, unknown>;
  explanation: {
    summary: string;
    top_risk_factors: Array<{
      feature: string;
      value: number;
      impact: number;
      description: string;
    }>;
    top_mitigating_factors: Array<{
      feature: string;
      value: number;
      impact: number;
      description: string;
    }>;
  };
  feature_count: number;
}

export interface RiskScore {
  id: string;
  entity_id: string;
  transaction_id: string | null;
  overall_score: number;
  component_scores: Record<string, number>;
  risk_factors: Record<string, unknown>;
  model_version: string;
  explanation: string | null;
  created_at: string;
}

export interface RiskScoreListResponse {
  total: number;
  items: RiskScore[];
}

export interface RiskDistribution {
  low: number;
  medium_low: number;
  medium: number;
  high: number;
  critical: number;
  total: number;
}

export interface TopRiskEntity {
  entity_id: string;
  entity_name: string | null;
  risk_score: number;
  risk_level: string;
  last_scored: string | null;
}
