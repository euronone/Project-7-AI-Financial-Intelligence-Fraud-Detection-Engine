export type AlertType = "ml_detection" | "rule_trigger" | "manual" | "watchlist_match" | "anomaly" | "velocity";
export type AlertSeverity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "open" | "investigating" | "escalated" | "resolved_fraud" | "resolved_false_positive" | "dismissed";

export interface FraudAlert {
  id: string;
  transaction_id: string;
  entity_id: string | null;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  description: string;
  confidence_score: number | null;
  rule_id: string | null;
  model_id: string | null;
  evidence: Record<string, unknown> | null;
  assigned_to: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: FraudAlert[];
}

export interface AlertStatistics {
  total: number;
  open: number;
  investigating: number;
  escalated: number;
  resolved_fraud: number;
  resolved_false_positive: number;
  dismissed: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}
