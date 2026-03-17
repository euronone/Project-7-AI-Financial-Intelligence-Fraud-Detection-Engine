export const APP_NAME = "FinShield AI";
export const APP_DESCRIPTION = "AI Financial Intelligence & Fraud Detection Engine";

export const RISK_LEVELS = {
  low: { label: "Low", color: "text-success-600", bg: "bg-success-50", max: 0.3 },
  medium: { label: "Medium", color: "text-warning-600", bg: "bg-warning-50", max: 0.6 },
  high: { label: "High", color: "text-orange-600", bg: "bg-orange-50", max: 0.8 },
  critical: { label: "Critical", color: "text-danger-600", bg: "bg-danger-50", max: 1.0 },
} as const;

export const ALERT_STATUSES = [
  "open",
  "investigating",
  "escalated",
  "resolved_fraud",
  "resolved_false_positive",
  "dismissed",
] as const;

export const TRANSACTION_STATUSES = [
  "pending",
  "completed",
  "failed",
  "reversed",
  "flagged",
  "blocked",
] as const;

export const USER_ROLES = ["admin", "analyst", "investigator", "viewer"] as const;

export const PAGINATION_DEFAULT_PAGE_SIZE = 25;
