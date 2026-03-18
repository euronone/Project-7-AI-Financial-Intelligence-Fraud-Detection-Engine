/**
 * TypeScript types for the Transaction resource.
 * Mirrors the backend Pydantic schemas in app/schemas/transaction.py.
 */

export type TransactionType =
  | "payment"
  | "transfer"
  | "withdrawal"
  | "deposit"
  | "refund";

export type TransactionChannel =
  | "online"
  | "pos"
  | "atm"
  | "mobile"
  | "wire"
  | "ach";

export type TransactionStatus =
  | "pending"
  | "completed"
  | "failed"
  | "reversed"
  | "flagged"
  | "blocked";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type FraudDecision = "PASS" | "FLAG" | "ALERT" | "BLOCK";

// ── Fraud pipeline output ─────────────────────────────────────────────────────

export interface FraudScoreBreakdown {
  ml_score: number;
  anomaly_score: number;
  behavioral_score: number;
  network_score: number;
  rule_score: number;
  composite_score: number;
  decision: FraudDecision;
  triggered_rules: string[];
  top_features: Array<{ feature: string; value: number; impact: number }>;
}

// ── Entity summary (embedded in transaction responses) ────────────────────────

export interface EntitySummary {
  id: string;
  name: string;
  entity_type: "individual" | "business" | "merchant";
  risk_score: number;
  risk_level: RiskLevel;
  is_watchlisted: boolean;
}

// ── Responses ─────────────────────────────────────────────────────────────────

export interface TransactionResponse {
  id: string;
  external_id: string;
  source_entity_id: string;
  destination_entity_id: string | null;
  amount: string; // Decimal serialised as string to preserve precision
  currency: string;
  transaction_type: TransactionType;
  channel: TransactionChannel;
  status: TransactionStatus;
  fraud_score: string | null;
  risk_level: RiskLevel | null;
  country_code: string | null;
  processed_at: string; // ISO 8601
  created_at: string;
}

export interface TransactionDetail extends TransactionResponse {
  merchant_category_code: string | null;
  description: string | null;
  ip_address: string | null;
  device_fingerprint: string | null;
  geolocation_lat: string | null;
  geolocation_lng: string | null;
  card_present: boolean | null;
  fraud_score_breakdown: FraudScoreBreakdown | null;
  source_entity: EntitySummary | null;
  destination_entity: EntitySummary | null;
  alert_count: number;
}

// ── Request bodies ────────────────────────────────────────────────────────────

export interface TransactionCreate {
  external_id: string;
  source_entity_id: string;
  destination_entity_id?: string;
  amount: number;
  currency: string;
  transaction_type: TransactionType;
  channel: TransactionChannel;
  status?: TransactionStatus;
  merchant_category_code?: string;
  description?: string;
  ip_address?: string;
  device_fingerprint?: string;
  geolocation_lat?: number;
  geolocation_lng?: number;
  country_code?: string;
  card_present?: boolean;
  processed_at: string;
}

export interface BatchIngestRequest {
  transactions: TransactionCreate[];
}

export interface BatchIngestResponse {
  accepted: number;
  rejected: number;
  errors: Array<{ external_id: string; error: string }>;
  task_id?: string;
}

// ── Search / filter params ────────────────────────────────────────────────────

export interface TransactionFilters {
  query?: string;
  status?: TransactionStatus[];
  risk_level?: RiskLevel[];
  transaction_type?: TransactionType[];
  channel?: TransactionChannel[];
  min_amount?: number;
  max_amount?: number;
  date_from?: string;
  date_to?: string;
  entity_id?: string;
  country_code?: string;
  min_fraud_score?: number;
  max_fraud_score?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

// ── WebSocket live event payload ──────────────────────────────────────────────

export interface LiveTransactionEvent {
  id: string;
  external_id: string;
  amount: string;
  currency: string;
  channel: TransactionChannel;
  status: TransactionStatus;
  fraud_score: string | null;
  risk_level: RiskLevel | null;
  decision?: FraudDecision;
  processed_at: string;
}
