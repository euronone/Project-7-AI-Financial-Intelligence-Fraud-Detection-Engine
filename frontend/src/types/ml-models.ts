// Phase 3 — ML Model Registry: TypeScript types (F2.7 / F2.8 / F2.9)

export type ModelType =
  | "fraud_classifier"
  | "anomaly_detector"
  | "risk_scorer"
  | "behavioral_profiler";

export type ModelStatus =
  | "training"
  | "validating"
  | "active"
  | "retired"
  | "failed";

export interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  auc_roc?: number;
  auc_pr?: number;
  n_train_samples?: number;
  [key: string]: number | undefined;
}

export interface RegisteredModel {
  id: string;
  name: string;
  model_type: ModelType;
  version: string;
  status: ModelStatus;
  metrics: ModelMetrics;
  artifact_path: string;
  training_dataset_info: Record<string, unknown>;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface RegisterModelRequest {
  name: string;
  model_type: ModelType;
  version: string;
  description?: string;
  metrics?: ModelMetrics;
  artifact_path?: string;
  training_dataset_info?: Record<string, unknown>;
}

export interface RetrainRequest {
  model_type: ModelType;
  n_samples?: number;
  reason?: string;
}

export interface RetrainResponse {
  job_id: string;
  model_type: ModelType;
  status: string;
  message: string;
  metrics: ModelMetrics;
}

export interface InferenceRequest {
  features: number[][];
}

export interface InferenceResponse {
  model_id: string;
  model_name: string;
  version: string;
  probabilities: number[];
  predictions: boolean[];
  latency_ms: number;
  backend: string;
}

// UI helpers
export const MODEL_TYPE_LABELS: Record<ModelType, string> = {
  fraud_classifier: "Fraud Classifier",
  anomaly_detector: "Anomaly Detector",
  risk_scorer: "Risk Scorer",
  behavioral_profiler: "Behavioral Profiler",
};

export const MODEL_STATUS_CONFIG: Record<
  ModelStatus,
  { label: string; color: string; bg: string }
> = {
  active: { label: "Active", color: "text-green-700", bg: "bg-green-100" },
  validating: { label: "Validating", color: "text-blue-700", bg: "bg-blue-100" },
  training: { label: "Training", color: "text-yellow-700", bg: "bg-yellow-100" },
  retired: { label: "Retired", color: "text-gray-600", bg: "bg-gray-100" },
  failed: { label: "Failed", color: "text-red-700", bg: "bg-red-100" },
};

export const KEY_METRICS: Array<{ key: keyof ModelMetrics; label: string }> = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1", label: "F1" },
  { key: "auc_roc", label: "AUC-ROC" },
  { key: "auc_pr", label: "AUC-PR" },
];
