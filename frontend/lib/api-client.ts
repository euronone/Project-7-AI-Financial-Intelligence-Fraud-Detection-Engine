/**
 * FinShield API client — thin wrapper around fetch that:
 * - Reads the base URL from NEXT_PUBLIC_API_URL
 * - Attaches the JWT from the auth store automatically
 * - Returns typed responses
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003/api/v1";

// ── Shared types ─────────────────────────────────────────────────────────────
export interface PaymentMethod {
  id: string;
  payment_type: "upi" | "credit_card" | "debit_card";
  upi_vpa: string | null;
  upi_provider: string | null;
  card_last4: string | null;
  card_network: string | null;
  card_expiry_month: number | null;
  card_expiry_year: number | null;
  card_bank_name: string | null;
  is_primary: boolean;
  display_label: string;
}

export interface SchemaField {
  field: string;
  type: string;
  required: boolean;
  description: string;
}

/** ML Training — algorithm catalogue entry. */
export interface AlgorithmInfo {
  id: string;
  name: string;
  description: string;
  library: string;
  tunable: boolean;
  recommended: boolean;
  available?: boolean;
}

/** Summary row returned by GET /ml/training/jobs */
export interface TrainingJobSummary {
  job_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
  algorithms: string[];
  data_window_days: number;
  auto_optimize: boolean;
  best_algorithm: string | null;
  training_samples: number;
  result_model_id: string | null;
  parent_job_id: string | null;
  created_at: string | null;
  completed_at: string | null;
}

/** Full status returned by GET /ml/training/jobs/{job_id} */
export interface TrainingJobStatus {
  job_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
  log_lines: { ts: string; msg: string }[];
  metrics: Record<string, Record<string, number | string | Record<string, number>>>;
  best_algorithm: string | null;
  training_samples: number;
  feature_count: number;
  result_model_id: string | null;
  optimization_rounds: number;
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
}

/** Per-field entry in a schema mapping (v2 format). */
export interface FieldMapping {
  client_column: string;
  enabled: boolean;
}

/** A custom column defined by the customer (not part of FinShield's canonical schema). */
export interface CustomColumn {
  field: string;         // FinShield internal name (editable)
  type: string;          // e.g. "STRING", "DECIMAL", "INTEGER"
  description: string;
  client_column: string; // customer's actual DB column
  enabled: boolean;
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json() as T;
}

export const apiClient = {
  // ── Auth ────────────────────────────────────────────────────────────────
  signup: (body: object) =>
    request<{ access_token: string; refresh_token: string; user: object }>(
      "/auth/signup",
      { method: "POST", body: JSON.stringify(body) }
    ),

  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; user: object }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    ),

  getMe: (token: string) =>
    request<object>("/auth/me", { token }),

  logout: (token: string) =>
    request<{ message: string }>("/auth/logout", { method: "POST", token }),

  // ── Settings ────────────────────────────────────────────────────────────
  getDbConfig: (token: string) =>
    request<{
      db_type: string | null;
      label: string | null;
      is_connected: boolean;
      supabase_url?: string;
      host?: string;
      port?: number;
      db_name?: string;
      db_user?: string;
      schema_name?: string;
      ssl_mode?: string;
      pool_size?: number;
      // Secret presence flags (actual values are never returned)
      has_password?: boolean;
      has_anon_key?: boolean;
      has_service_key?: boolean;
      has_service_role_key?: boolean;
      has_supabase_db_password?: boolean;
      has_api_key?: boolean;
      has_aws_secret?: boolean;
      has_service_account?: boolean;
      has_planetscale_pass?: boolean;
      has_redis_password?: boolean;
    }>("/settings/database", { token }),

  saveDbConfig: (config: object, token: string) =>
    request<object>("/settings/database", {
      method: "PUT",
      body: JSON.stringify(config),
      token,
    }),

  testDbConnection: (config: object, token: string) =>
    request<{ success: boolean; message: string; latency_ms: number }>(
      "/settings/test-connection",
      { method: "POST", body: JSON.stringify(config), token }
    ),

  getNotificationSettings: (token: string) =>
    request<{
      company_alert_email: string;
      sms_enabled: boolean;
      has_resend: boolean;
      has_twilio: boolean;
    }>("/settings/notifications", { token }),

  saveNotificationSettings: (
    body: {
      company_alert_email?: string;
      sms_enabled?: boolean;
      resend_api_key?: string;
      twilio_account_sid?: string;
      twilio_auth_token?: string;
      twilio_from_number?: string;
    },
    token: string
  ) =>
    request<{ success: boolean; message: string }>("/settings/notifications", {
      method: "PUT",
      body: JSON.stringify(body),
      token,
    }),

  // ── Analytics ───────────────────────────────────────────────────────────
  getOverview: (token: string) =>
    request<{
      transactions_today: number;
      total_transactions: number;
      fraud_count: number;
      fraud_rate_percent: number;
      open_alerts: number;
      critical_alerts: number;
    }>("/analytics/overview", { token }),

  // ── Transactions ────────────────────────────────────────────────────────
  getTransactions: (token: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ items: object[]; total: number }>(`/transactions${qs}`, { token });
  },

  createTransaction: (body: object, token: string) =>
    request<object>("/transactions", {
      method: "POST",
      body: JSON.stringify(body),
      token,
    }),

  // ── Alerts ──────────────────────────────────────────────────────────────
  getAlerts: (token: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ items: object[]; total: number }>(`/alerts${qs}`, { token });
  },

  // ── Customers ───────────────────────────────────────────────────────────
  getCustomerStats: (token: string) =>
    request<{
      total_customers: number;
      fraud_customers: number;
      high_risk_customers: number;
      avg_risk_score: number;
    }>("/customers/stats", { token }),

  getCustomerRiskDist: (token: string) =>
    request<{ bands: { label: string; count: number; color: string }[] }>(
      "/customers/charts/risk-dist", { token }
    ),

  getCustomerFraudLegit: (token: string) =>
    request<{ tiers: { tier: string; fraud: number; legit: number }[] }>(
      "/customers/charts/fraud-legit", { token }
    ),

  getCustomerActivity: (token: string, days = 14) =>
    request<{ dates: string[]; counts: number[] }>(
      `/customers/charts/activity?days=${days}`, { token }
    ),

  getTopRiskyCustomers: (token: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ items: object[]; total: number }>(
      `/customers/top-risky${qs}`, { token }
    );
  },

  // ── Data Sources ─────────────────────────────────────────────────────────
  getDataSources: (token: string) =>
    request<object>("/data-sources", { token }),

  getDataSourceSchema: (token: string) =>
    request<object>("/data-sources/schema", { token }),

  getDataSourceFieldMap: (token: string) =>
    request<object>("/data-sources/field-map", { token }),

  // ── Simulator ─────────────────────────────────────────────────────────────
  simulatorPredict: (body: object, token: string) =>
    request<object>("/simulator/predict", {
      method: "POST",
      body: JSON.stringify(body),
      token,
    }),

  simulatorExamples: (token: string) =>
    request<object[]>("/simulator/examples", { token }),

  /** Fetch up to 5 real sample customers with primary payment method info. */
  simulatorSampleCustomers: (token: string) =>
    request<{
      samples: {
        phone_number: string;
        full_name: string;
        city: string;
        risk_score: number;
        customer_tier: string;
        primary_payment_type: string | null;
        primary_payment_label: string | null;
      }[];
    }>("/simulator/sample-customers", { token }),

  /** Look up a customer by phone number and return pre-fill data for the simulator form. */
  simulatorLookupCustomer: (phone: string, token: string) =>
    request<{
      found: boolean;
      customer_id: string;
      cardholder_name: string;
      email: string;
      city: string;
      country_code: string;
      state_province: string;
      card_last4: string;
      card_type: string;
      risk_score: number;
      customer_tier: string;
      kyc_status: string;
      account_type: string;
      balance_amount: number;
      active_card_count: number;
      payment_methods: PaymentMethod[];
      // Masked card/expiry fields for simulator form auto-population
      masked_cvv: string;
      masked_expiry_month: number | string;
      masked_expiry_year: number | string;
    }>(`/simulator/lookup-customer?phone=${encodeURIComponent(phone)}`, { token }),

  // ── Schema Mapping ──────────────────────────────────────────────────────────
  getSchemaDefinition: (token: string) =>
    request<{
      customers: SchemaField[];
      transactions: SchemaField[];
    }>("/settings/schema-definition", { token }),

  getSchemaMapping: (token: string) =>
    request<{
      customers: Record<string, FieldMapping>;
      transactions: Record<string, FieldMapping>;
      customers_custom: CustomColumn[];
      transactions_custom: CustomColumn[];
      last_updated: string | null;
    }>("/settings/schema-mapping", { token }),

  saveSchemaMapping: (
    body: {
      customers: Record<string, FieldMapping>;
      transactions: Record<string, FieldMapping>;
      customers_custom: CustomColumn[];
      transactions_custom: CustomColumn[];
    },
    token: string
  ) =>
    request<{ success: boolean; message: string }>("/settings/schema-mapping", {
      method: "PUT",
      body: JSON.stringify(body),
      token,
    }),

  // ── ML Training ─────────────────────────────────────────────────────────
  getTrainingAlgorithms: (token: string) =>
    request<{ clustering: AlgorithmInfo[]; supervised: AlgorithmInfo[]; total: number }>(
      "/ml/training/algorithms", { token }
    ),

  startTrainingJob: (
    body: {
      algorithms: string[];
      data_window_days: number;
      auto_optimize: boolean;
      use_custom_columns: boolean;
    },
    token: string
  ) =>
    request<{ job_id: string; status: string; message: string }>(
      "/ml/training/start",
      { method: "POST", body: JSON.stringify(body), token }
    ),

  listTrainingJobs: (token: string) =>
    request<{ jobs: TrainingJobSummary[]; total: number }>(
      "/ml/training/jobs", { token }
    ),

  getTrainingJobStatus: (jobId: string, token: string) =>
    request<TrainingJobStatus>(`/ml/training/jobs/${jobId}`, { token }),

  reoptimizeJob: (jobId: string, newWindowDays: number, token: string) =>
    request<{ job_id: string; parent_job_id: string; status: string; message: string }>(
      `/ml/training/jobs/${jobId}/reoptimize`,
      { method: "POST", body: JSON.stringify({ new_window_days: newWindowDays }), token }
    ),

  promoteTrainingJob: (jobId: string, token: string) =>
    request<{ model_id: string; model_name: string; version: string; auc_roc: number; f1_score: number; message: string }>(
      `/ml/training/jobs/${jobId}/promote`,
      { method: "POST", token }
    ),

  uploadPickleModel: (formData: FormData, token: string): Promise<{ model_id: string; model_name: string; message: string }> => {
    return fetch(`${API_BASE}/ml/training/upload-pickle`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
      }
      return res.json();
    });
  },

  // ── ML Details ──────────────────────────────────────────────────────────
  getMlModels: (token: string) =>
    request<object>("/ml/models", { token }),

  getMlFeatures: (token: string) =>
    request<object>("/ml/features", { token }),

  getMlSampleTransactions: (token: string) =>
    request<object>("/ml/sample-transactions", { token }),

  getMlRegistry: (token: string) =>
    request<object>("/ml/registry", { token }),

  // ── Health ──────────────────────────────────────────────────────────────
  health: () => request<{ status: string }>("/health"),
};

export const isBackendAvailable = async (): Promise<boolean> => {
  try {
    await apiClient.health();
    return true;
  } catch {
    return false;
  }
};
