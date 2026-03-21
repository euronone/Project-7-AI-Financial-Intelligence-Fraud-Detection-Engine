export type EntityType = "individual" | "business" | "merchant";
export type KYCStatus = "pending" | "verified" | "rejected" | "expired";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface Entity {
  id: string;
  external_id: string;
  entity_type: EntityType;
  name: string;
  email: string | null;
  phone: string | null;
  country_code: string | null;
  risk_score: number;
  risk_level: RiskLevel;
  is_watchlisted: boolean;
  kyc_status: KYCStatus;
  created_at: string;
  updated_at: string;
}

export interface EntityDetail extends Entity {
  transaction_count: number;
  total_transaction_amount: number;
  alert_count: number;
  open_case_count: number;
}

export interface EntityFilters {
  entity_type?: string;
  risk_level?: string;
  kyc_status?: string;
  country_code?: string;
  is_watchlisted?: boolean;
  search?: string;
}

export interface EntityListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: Entity[];
}
