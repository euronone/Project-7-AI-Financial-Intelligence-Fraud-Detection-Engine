export type TransactionType = "payment" | "transfer" | "withdrawal" | "deposit" | "refund";
export type TransactionChannel = "online" | "pos" | "atm" | "mobile" | "wire" | "ach";
export type TransactionStatus = "pending" | "completed" | "failed" | "reversed" | "flagged" | "blocked";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface Transaction {
  id: string;
  external_id: string;
  source_entity_id: string;
  destination_entity_id: string | null;
  amount: number;
  currency: string;
  transaction_type: TransactionType;
  channel: TransactionChannel;
  status: TransactionStatus;
  merchant_category_code: string | null;
  description: string | null;
  ip_address: string | null;
  country_code: string | null;
  card_present: boolean | null;
  fraud_score: number | null;
  risk_level: RiskLevel | null;
  processed_at: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionFilters {
  status?: string;
  transaction_type?: string;
  channel?: string;
  risk_level?: string;
  currency?: string;
  min_amount?: number;
  max_amount?: number;
  search?: string;
}

export interface TransactionListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: Transaction[];
}
