export type RuleCategory = "velocity" | "amount" | "geography" | "pattern" | "device" | "custom";
export type RuleSeverity = "low" | "medium" | "high" | "critical";

export interface RuleCondition {
  field: string;
  operator: string;
  value: unknown;
}

export interface ConditionTree {
  logic?: "and" | "or";
  rules: (RuleCondition | ConditionTree)[];
}

export interface RuleAction {
  type: string;
  [key: string]: unknown;
}

export interface Rule {
  id: string;
  name: string;
  description: string | null;
  category: RuleCategory;
  conditions: ConditionTree;
  actions: { actions: RuleAction[] };
  severity: RuleSeverity;
  is_active: boolean;
  priority: number;
  hit_count: number;
  false_positive_rate: number | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface RuleListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: Rule[];
}

export interface RuleTestResult {
  rule_id: string;
  rule_name: string;
  matched: boolean;
  severity: string;
  priority: number;
  conditions: Array<{ field: string; operator: string; value: unknown; passed: boolean }>;
  actions: Array<{ type: string; executed: boolean; details: Record<string, unknown> }>;
}

export interface RuleTemplate {
  name: string;
  description: string;
  category: RuleCategory;
  severity: RuleSeverity;
  priority: number;
  conditions: ConditionTree;
  actions: { actions: RuleAction[] };
}
