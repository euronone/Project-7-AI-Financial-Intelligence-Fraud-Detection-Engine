export interface OverviewStats {
  total_transactions: number;
  total_alerts: number;
  total_cases: number;
  total_entities: number;
  fraud_rate: number;
  avg_risk_score: number;
  total_amount_processed: number;
  active_rules: number;
}

export interface FraudTrendPoint {
  date: string;
  count: number;
  amount: number;
  avg_score: number;
}

export interface FraudTrendsResponse {
  period: string;
  data_points: FraudTrendPoint[];
}

export interface TransactionVolumePoint {
  date: string;
  count: number;
  amount: number;
  by_channel: Record<string, number>;
}

export interface TransactionVolumeResponse {
  period: string;
  data_points: TransactionVolumePoint[];
}

export interface RiskDistributionResponse {
  low: number;
  medium: number;
  high: number;
  critical: number;
  total: number;
}

export interface TopPattern {
  pattern_name: string;
  count: number;
  percentage: number;
  trend: string;
}

export interface TopPatternsResponse {
  patterns: TopPattern[];
}

export interface GeoDataPoint {
  country_code: string;
  count: number;
  fraud_count: number;
  total_amount: number;
  fraud_rate: number;
}

export interface GeoResponse {
  data: GeoDataPoint[];
}

export interface ModelPerformancePoint {
  model_name: string;
  model_type: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  auc_roc: number;
}

export interface ModelPerformanceResponse {
  models: ModelPerformancePoint[];
}

export interface ReportRequest {
  report_type: string;
  date_from?: string;
  date_to?: string;
  filters?: Record<string, unknown>;
}

export interface ReportResponse {
  report_id: string;
  status: string;
  download_url?: string;
  created_at: string;
}
