export type ModelType = "fraud_classifier" | "anomaly_detector" | "risk_scorer" | "behavioral_profiler";
export type ModelStatus = "training" | "validating" | "active" | "retired" | "failed";

export interface MLModel {
  id: string;
  name: string;
  model_type: ModelType;
  version: string;
  status: ModelStatus;
  framework: string;
  metrics: Record<string, number>;
  parameters: Record<string, unknown> | null;
  artifact_path: string;
  training_dataset_info: Record<string, unknown> | null;
  promoted_at: string | null;
  promoted_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface MLModelListResponse {
  total: number;
  items: MLModel[];
}

export interface ModelCompareResponse {
  models: MLModel[];
  metric_comparison: Record<string, Record<string, number | null>>;
}
