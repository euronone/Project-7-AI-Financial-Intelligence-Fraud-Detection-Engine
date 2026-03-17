// F5 — Risk Scoring: TypeScript types

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type UpdateTrigger =
  | "new_transaction"
  | "alert_resolution"
  | "watchlist_match";

// F5.3 — Component score breakdown
export interface ComponentScores {
  ml_score: number;
  rule_score: number;
  velocity_score: number;
  behavioral_score: number;
  network_score: number;
}

// F5.1 / F5.3 — Entity risk profile
export interface EntityRiskProfile {
  entity_id: string;
  current_score: number;
  risk_level: RiskLevel;
  component_scores: ComponentScores;
  risk_factors: string[];
  model_version: string;
  explanation: string | null;
  last_updated: string;
  score_trend: number[];
}

// F5.4 — Risk score history entry
export interface RiskScoreHistoryEntry {
  id: string;
  overall_score: number;
  risk_level: RiskLevel;
  component_scores: ComponentScores;
  risk_factors: string[];
  transaction_id: string | null;
  created_at: string;
}

export interface RiskScoreHistory {
  entity_id: string;
  history: RiskScoreHistoryEntry[];
  total: number;
}

// F5.1 — On-demand calculate
export interface CalculateRiskRequest {
  entity_id: string;
  transaction_data: Record<string, unknown>;
  watchlist_match?: boolean;
  triggered_rules?: string[];
}

export interface CalculateRiskResponse {
  entity_id: string;
  overall_score: number;
  risk_level: RiskLevel;
  component_scores: ComponentScores;
  risk_factors: string[];
  explanation: string;
  model_version: string;
  record_id: string;
}

// F5.5 — Risk distribution
export interface RiskTierCount {
  risk_level: RiskLevel;
  count: number;
  percentage: number;
}

export interface RiskDistribution {
  total_entities: number;
  tiers: RiskTierCount[];
  thresholds: Record<string, number>;
}

// F5.6 — Top-N leaderboard
export interface TopRiskEntity {
  rank: number;
  entity_id: string;
  overall_score: number;
  risk_level: RiskLevel;
  risk_factors: string[];
  last_updated: string;
}

export interface TopRiskEntities {
  entities: TopRiskEntity[];
  total_returned: number;
}

// F5.7 — Auto-update
export interface AutoUpdateRequest {
  entity_id: string;
  trigger: UpdateTrigger;
  context?: Record<string, unknown>;
}

export interface AutoUpdateResponse {
  entity_id: string;
  trigger: UpdateTrigger;
  previous_score: number;
  new_score: number;
  risk_level: RiskLevel;
  updated: boolean;
}

// UI helpers
export const RISK_LEVEL_CONFIG: Record<
  RiskLevel,
  { label: string; color: string; bg: string; border: string }
> = {
  low: {
    label: "Low",
    color: "text-green-700",
    bg: "bg-green-100",
    border: "border-green-300",
  },
  medium: {
    label: "Medium",
    color: "text-yellow-700",
    bg: "bg-yellow-100",
    border: "border-yellow-300",
  },
  high: {
    label: "High",
    color: "text-orange-700",
    bg: "bg-orange-100",
    border: "border-orange-300",
  },
  critical: {
    label: "Critical",
    color: "text-red-700",
    bg: "bg-red-100",
    border: "border-red-300",
  },
};

export const RISK_CHART_COLORS: Record<RiskLevel, string> = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};
