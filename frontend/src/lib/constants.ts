/**
 * App-wide constants — label maps, colour tokens, and configuration values.
 */
import type { RiskLevel, TransactionChannel, TransactionStatus } from "@/types/transaction";

// ── Risk level ────────────────────────────────────────────────────────────────

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export const RISK_LEVEL_SCORE_RANGE: Record<RiskLevel, [number, number]> = {
  low: [0, 0.3],
  medium: [0.3, 0.6],
  high: [0.6, 0.8],
  critical: [0.8, 1.0],
};

// ── Transaction status ────────────────────────────────────────────────────────

export const TRANSACTION_STATUS_LABELS: Record<TransactionStatus, string> = {
  pending: "Pending",
  completed: "Completed",
  failed: "Failed",
  reversed: "Reversed",
  flagged: "Flagged",
  blocked: "Blocked",
};

export const TRANSACTION_STATUS_COLORS: Record<TransactionStatus, string> = {
  pending: "bg-gray-100 text-gray-700",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  reversed: "bg-purple-100 text-purple-800",
  flagged: "bg-yellow-100 text-yellow-800",
  blocked: "bg-red-200 text-red-900",
};

// ── Channel ───────────────────────────────────────────────────────────────────

export const CHANNEL_LABELS: Record<TransactionChannel, string> = {
  online: "Online",
  pos: "POS",
  atm: "ATM",
  mobile: "Mobile",
  wire: "Wire",
  ach: "ACH",
};

// ── Fraud decision colours ────────────────────────────────────────────────────

export const DECISION_COLORS: Record<string, string> = {
  PASS: "bg-green-100 text-green-800",
  FLAG: "bg-yellow-100 text-yellow-800",
  ALERT: "bg-orange-100 text-orange-800",
  BLOCK: "bg-red-100 text-red-800",
};

// ── Pagination defaults ───────────────────────────────────────────────────────

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 200;

// ── Export ────────────────────────────────────────────────────────────────────

export const EXPORT_FORMATS = ["csv", "json"] as const;
export type ExportFormat = (typeof EXPORT_FORMATS)[number];
