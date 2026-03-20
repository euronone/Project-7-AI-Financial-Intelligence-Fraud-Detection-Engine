export type CaseStatus = "open" | "in_progress" | "pending_review" | "escalated" | "closed_confirmed_fraud" | "closed_false_positive";
export type CasePriority = "low" | "medium" | "high" | "critical";

export interface Case {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  priority: CasePriority;
  assigned_to: string | null;
  total_amount_at_risk: number | null;
  alert_ids: string[] | null;
  timeline: { events: TimelineEvent[] } | null;
  findings: string | null;
  created_by: string;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  type: string;
  timestamp: string;
  user_id: string;
  notes?: string;
  new_status?: string;
  assigned_to?: string;
}

export interface CaseListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: Case[];
}

export interface CaseStatistics {
  total: number;
  open: number;
  in_progress: number;
  pending_review: number;
  escalated: number;
  closed_confirmed_fraud: number;
  closed_false_positive: number;
  by_priority: Record<string, number>;
}
