"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Shield, Database, Save, Zap, Loader2, CheckCircle2,
  AlertCircle, Eye, EyeOff, ExternalLink, Settings,
  Key, User, CreditCard, ChevronDown, ChevronUp,
  Mail, Activity, TrendingUp, AlertTriangle,
  FlaskConical, Users, Table, Brain, X, Plus, LogOut,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore, DbConfig, DbType } from "@/store/auth-store";
import { apiClient, CredentialOut } from "@/lib/api-client";

// ── DB type definitions ───────────────────────────────────────────────────────

interface DbFieldDef {
  key: string;
  label: string;
  placeholder: string;
  secret?: boolean;
  type?: "text" | "number" | "select";
  options?: string[];
  hint?: string;
}

interface DbTypeDef {
  id: DbType;
  name: string;
  icon: string;
  color: string;
  description: string;
  badge?: string;
  docs: string;
  fields: DbFieldDef[];
  advancedFields?: DbFieldDef[];
}

const DB_TYPES: DbTypeDef[] = [
  {
    id: "supabase",
    name: "Supabase",
    icon: "⚡",
    color: "#3ECF8E",
    description: "PostgreSQL-backed BaaS — recommended for fast setup",
    badge: "Recommended",
    docs: "https://supabase.com/docs/guides/getting-started",
    fields: [
      { key: "supabase_url",              label: "Project URL",                   placeholder: "https://xyzabc.supabase.co",              hint: "Found in Project Settings → General → Reference ID — e.g. https://<ref>.supabase.co" },
      { key: "supabase_anon_key",         label: "Anon / Public Key",             placeholder: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", secret: true, hint: "SUPABASE_ANON_KEY — safe to use in browser. Project Settings → API → anon public" },
      { key: "supabase_service_key",      label: "Service Key",                   placeholder: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", secret: true, hint: "SUPABASE_SERVICE_KEY — server-side only. Project Settings → API → service_role secret" },
      { key: "supabase_service_role_key", label: "Service Role Key",              placeholder: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", secret: true, hint: "SUPABASE_SERVICE_ROLE_KEY — bypasses RLS. Same JWT as Service Key; enter once if yours are identical" },
      { key: "supabase_db_password",      label: "Database Password",             placeholder: "your-database-password",                  secret: true, hint: "SUPABASE_DB_PASSWORD — Postgres password. Project Settings → Database → Connection string → Password" },
    ],
    advancedFields: [
      { key: "schema_name", label: "Schema", placeholder: "public", hint: "PostgreSQL schema (default: public)" },
    ],
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    icon: "🐘",
    color: "#336791",
    description: "Direct PostgreSQL connection via asyncpg",
    docs: "https://www.postgresql.org/docs/current/",
    fields: [
      { key: "host",        label: "Host",          placeholder: "db.example.com" },
      { key: "port",        label: "Port",          placeholder: "5432", type: "number" },
      { key: "db_name",     label: "Database Name", placeholder: "finshield_prod" },
      { key: "db_user",     label: "Username",      placeholder: "finshield_user" },
      { key: "db_password", label: "Password",      placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "schema_name",         label: "Schema",      placeholder: "public" },
      { key: "ssl_mode",            label: "SSL Mode",    placeholder: "require", type: "select", options: ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] },
      { key: "pool_size",           label: "Pool Size",   placeholder: "10", type: "number" },
      { key: "connection_timeout",  label: "Timeout (s)", placeholder: "30", type: "number" },
    ],
  },
  {
    id: "mysql",
    name: "MySQL / MariaDB",
    icon: "🐬",
    color: "#F29111",
    description: "MySQL or MariaDB via aiomysql",
    docs: "https://dev.mysql.com/doc/refman/8.0/en/",
    fields: [
      { key: "host",        label: "Host",          placeholder: "mysql.example.com" },
      { key: "port",        label: "Port",          placeholder: "3306", type: "number" },
      { key: "db_name",     label: "Database Name", placeholder: "finshield" },
      { key: "db_user",     label: "Username",      placeholder: "finshield_user" },
      { key: "db_password", label: "Password",      placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "ssl_mode",           label: "SSL Mode",    placeholder: "require", type: "select", options: ["disabled", "preferred", "required", "verify_ca", "verify_identity"] },
      { key: "connection_timeout", label: "Timeout (s)", placeholder: "30", type: "number" },
    ],
  },
  {
    id: "mongodb",
    name: "MongoDB",
    icon: "🍃",
    color: "#47A248",
    description: "MongoDB Atlas or self-hosted (transaction data)",
    docs: "https://www.mongodb.com/docs/drivers/node/current/",
    fields: [
      { key: "mongo_connection_string", label: "Connection String", placeholder: "mongodb+srv://user:password@cluster0.abc123.mongodb.net/finshield?retryWrites=true&w=majority", secret: true, hint: "Full MongoDB URI including credentials" },
      { key: "db_name",                label: "Database Name",     placeholder: "finshield" },
    ],
    advancedFields: [
      { key: "auth_source", label: "Auth Source DB", placeholder: "admin", hint: "Database used for authentication (default: admin)" },
    ],
  },
  {
    id: "mssql",
    name: "Microsoft SQL Server",
    icon: "🪟",
    color: "#CC2222",
    description: "SQL Server / Azure SQL Database via pyodbc",
    docs: "https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/",
    fields: [
      { key: "host",        label: "Server / Host", placeholder: "sqlserver.example.com,1433" },
      { key: "port",        label: "Port",          placeholder: "1433", type: "number" },
      { key: "db_name",     label: "Database",      placeholder: "FinShield" },
      { key: "db_user",     label: "Username",      placeholder: "sa" },
      { key: "db_password", label: "Password",      placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "schema_name", label: "Schema",       placeholder: "dbo" },
      { key: "ssl_mode",    label: "Encrypt",      placeholder: "yes", type: "select", options: ["yes", "no", "strict"] },
      { key: "pool_size",   label: "Pool Size",    placeholder: "10", type: "number" },
    ],
  },
  {
    id: "oracle",
    name: "Oracle Database",
    icon: "🔴",
    color: "#F80000",
    description: "Oracle DB via python-oracledb (thin or thick mode)",
    docs: "https://python-oracledb.readthedocs.io/",
    fields: [
      { key: "host",                 label: "Host / Hostname",   placeholder: "oracle.example.com" },
      { key: "port",                 label: "Port",              placeholder: "1521", type: "number" },
      { key: "oracle_service_name",  label: "Service Name / SID", placeholder: "ORCL" },
      { key: "db_user",              label: "Username",          placeholder: "FINSHIELD" },
      { key: "db_password",          label: "Password",          placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "schema_name",           label: "Schema",          placeholder: "FINSHIELD" },
      { key: "oracle_wallet_location", label: "Wallet Path",    placeholder: "/opt/oracle/wallet", hint: "For mTLS / Oracle Cloud Autonomous DB" },
      { key: "pool_size",             label: "Pool Size",       placeholder: "10", type: "number" },
    ],
  },
  {
    id: "redis",
    name: "Redis",
    icon: "🔴",
    color: "#DC382D",
    description: "Redis 7+ for caching and feature store",
    docs: "https://redis.io/docs/",
    fields: [
      { key: "host",           label: "Host",       placeholder: "redis.example.com" },
      { key: "port",           label: "Port",       placeholder: "6379", type: "number" },
      { key: "redis_password", label: "Password",   placeholder: "••••••••", secret: true, hint: "Leave blank for no-auth Redis" },
    ],
    advancedFields: [
      { key: "redis_db_index", label: "DB Index",   placeholder: "0", type: "number", hint: "Redis logical database index (0-15)" },
      { key: "redis_use_tls",  label: "Use TLS",    placeholder: "true", type: "select", options: ["true", "false"] },
    ],
  },
  {
    id: "dynamodb",
    name: "Amazon DynamoDB",
    icon: "🏗️",
    color: "#FF9900",
    description: "AWS DynamoDB via boto3 / aiobotocore",
    docs: "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/",
    fields: [
      { key: "aws_region",            label: "AWS Region",          placeholder: "ap-south-1" },
      { key: "aws_access_key_id",     label: "Access Key ID",       placeholder: "AKIAIOSFODNN7EXAMPLE" },
      { key: "aws_secret_access_key", label: "Secret Access Key",   placeholder: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", secret: true },
    ],
    advancedFields: [
      { key: "aws_session_token",       label: "Session Token",     placeholder: "AQoXnyc4lcK4w...", secret: true, hint: "For assumed-role / temporary credentials" },
      { key: "dynamodb_table_prefix",   label: "Table Prefix",      placeholder: "finshield_", hint: "Prefix prepended to all table names" },
    ],
  },
  {
    id: "firestore",
    name: "Google Firestore",
    icon: "🔥",
    color: "#FFCA28",
    description: "Google Cloud Firestore via firebase-admin",
    docs: "https://firebase.google.com/docs/firestore",
    fields: [
      { key: "gcp_project_id",      label: "GCP Project ID",        placeholder: "my-finshield-project" },
      { key: "service_account_json", label: "Service Account JSON", placeholder: "eyJhbGciOiJSU0EtT...", secret: true, hint: "Base64-encoded service account key JSON" },
    ],
    advancedFields: [
      { key: "firestore_collection_prefix", label: "Collection Prefix", placeholder: "finshield_" },
    ],
  },
  {
    id: "snowflake",
    name: "Snowflake",
    icon: "❄️",
    color: "#29B5E8",
    description: "Snowflake Data Cloud — analytics and batch scoring",
    docs: "https://docs.snowflake.com/en/developer-guide/python-connector/",
    fields: [
      { key: "snowflake_account",    label: "Account Identifier",  placeholder: "xy12345.ap-southeast-1.aws", hint: "Format: <account>.<region>.<cloud>" },
      { key: "snowflake_warehouse",  label: "Warehouse",           placeholder: "FINSHIELD_WH" },
      { key: "snowflake_database",   label: "Database",            placeholder: "FINSHIELD_DB" },
      { key: "db_user",              label: "Username",            placeholder: "FINSHIELD_SVC" },
      { key: "db_password",          label: "Password",            placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "snowflake_schema", label: "Schema",         placeholder: "PUBLIC" },
      { key: "snowflake_role",   label: "Role",           placeholder: "SYSADMIN", hint: "Snowflake role for this connection" },
      { key: "pool_size",        label: "Pool Size",      placeholder: "5", type: "number" },
    ],
  },
  {
    id: "cockroachdb",
    name: "CockroachDB",
    icon: "🪳",
    color: "#6933FF",
    description: "CockroachDB Cloud or self-hosted (PostgreSQL-compatible)",
    docs: "https://www.cockroachlabs.com/docs/stable/connect-to-the-database.html",
    fields: [
      { key: "host",        label: "Host",          placeholder: "free-tier.cockroachlabs.cloud" },
      { key: "port",        label: "Port",          placeholder: "26257", type: "number" },
      { key: "db_name",     label: "Database",      placeholder: "defaultdb" },
      { key: "db_user",     label: "Username",      placeholder: "finshield" },
      { key: "db_password", label: "Password",      placeholder: "••••••••", secret: true },
    ],
    advancedFields: [
      { key: "ssl_mode",   label: "SSL Mode",  placeholder: "verify-full", type: "select", options: ["require", "verify-ca", "verify-full"] },
      { key: "schema_name", label: "Schema",   placeholder: "public" },
    ],
  },
  {
    id: "neon",
    name: "Neon (Serverless Postgres)",
    icon: "🌿",
    color: "#00E5BF",
    description: "Neon serverless PostgreSQL with branching support",
    docs: "https://neon.tech/docs/connect/connect-from-any-app",
    fields: [
      { key: "neon_connection_string", label: "Connection String", placeholder: "postgresql://alex:AbC123dEf@ep-cool-darkness-123456.us-east-2.aws.neon.tech/dbname?sslmode=require", secret: true, hint: "Full Neon connection string from the dashboard" },
    ],
    advancedFields: [
      { key: "schema_name",         label: "Schema",       placeholder: "public" },
      { key: "connection_timeout",  label: "Timeout (s)",  placeholder: "30", type: "number" },
    ],
  },
  {
    id: "planetscale",
    name: "PlanetScale",
    icon: "🪐",
    color: "#F4F4F5",
    description: "PlanetScale MySQL-compatible serverless database",
    docs: "https://planetscale.com/docs/concepts/connection-strings",
    fields: [
      { key: "planetscale_host",     label: "Host",     placeholder: "aws.connect.psdb.cloud" },
      { key: "db_name",              label: "Database", placeholder: "finshield" },
      { key: "planetscale_username", label: "Username", placeholder: "xxxxxxxxxxxxxxxx" },
      { key: "planetscale_password", label: "Password", placeholder: "your_planetscale_password", secret: true },
    ],
  },
  {
    id: "clickhouse",
    name: "ClickHouse",
    icon: "🟡",
    color: "#FACC15",
    description: "ClickHouse — high-performance analytics for fraud trend queries",
    docs: "https://clickhouse.com/docs/en/integrations/python",
    fields: [
      { key: "host",        label: "Host",          placeholder: "clickhouse.example.com" },
      { key: "db_user",     label: "Username",      placeholder: "default" },
      { key: "db_password", label: "Password",      placeholder: "••••••••", secret: true },
      { key: "db_name",     label: "Database",      placeholder: "finshield" },
    ],
    advancedFields: [
      { key: "clickhouse_http_port",   label: "HTTP Port",    placeholder: "8123", type: "number" },
      { key: "clickhouse_native_port", label: "Native Port",  placeholder: "9000", type: "number" },
      { key: "clickhouse_cluster",     label: "Cluster Name", placeholder: "finshield_cluster", hint: "For distributed queries across shards" },
    ],
  },
  {
    id: "rest_api",
    name: "REST API / CSV",
    icon: "🔌",
    color: "#8B5CF6",
    description: "Custom REST endpoint or SFTP/CSV batch upload",
    docs: "#",
    fields: [
      { key: "api_base_url",   label: "Base URL",    placeholder: "https://api.yourbank.com/v1/transactions" },
      { key: "api_key",        label: "API Key",     placeholder: "your_api_key_here", secret: true },
    ],
    advancedFields: [
      { key: "api_auth_header", label: "Auth Header Name", placeholder: "X-API-Key", hint: "Header name for the API key (default: Authorization)" },
    ],
  },
];

const SECTIONS = [
  { id: "database",      label: "Database",      icon: Database },
  { id: "integrations",  label: "Integrations",  icon: Key },
  { id: "api-keys",      label: "API Keys",      icon: Zap },
  { id: "account",       label: "Account",       icon: User },
  { id: "billing",       label: "Billing",       icon: CreditCard },
];

// ── Component ────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { user, dbConfig, updateDbConfig, token, clearAuth } = useAuthStore();
  const router = useRouter();

  // Read ?section= URL param to deep-link into a specific settings section
  const validSectionIds = new Set(SECTIONS.map(s => s.id));
  const getInitialSection = () => {
    if (typeof window !== "undefined") {
      const param = new URLSearchParams(window.location.search).get("section");
      // Accept "notifications" as an alias for "integrations" (legacy link compat)
      if (param === "notifications") return "integrations";
      if (param && validSectionIds.has(param)) return param;
    }
    return "database";
  };

  const [activeSection, setActiveSection] = useState(getInitialSection);
  const [selectedType, setSelectedType] = useState<DbType>(dbConfig?.db_type || "supabase");
  const [label, setLabel] = useState(dbConfig?.label || "");
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);
  const [testMessage, setTestMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");
  // Tracks which secret field keys already have a saved value on the server
  const [savedSecretKeys, setSavedSecretKeys] = useState<Set<string>>(new Set());

  // ── Load saved DB settings from backend on mount ─────────────────────────
  useEffect(() => {
    if (!token) return;
    apiClient.getDbConfig(token).then((data) => {
      if (!data.db_type) return;
      setSelectedType(data.db_type as import("@/store/auth-store").DbType);
      if (data.label) setLabel(data.label);

      // Pre-fill non-secret fields
      const vals: Record<string, string> = {};
      if (data.supabase_url) vals.supabase_url = data.supabase_url;
      if (data.host)         vals.host          = data.host;
      if (data.port)         vals.port          = String(data.port);
      if (data.db_name)      vals.db_name       = data.db_name;
      if (data.db_user)      vals.db_user       = data.db_user;
      if (data.schema_name)  vals.schema_name   = data.schema_name;
      if (data.ssl_mode)     vals.ssl_mode      = data.ssl_mode;
      if (data.pool_size)    vals.pool_size     = String(data.pool_size);
      setFormValues(vals);

      // Map has_xxx flags → field keys for "saved" badge display
      const HAS_MAP: Record<string, string> = {
        has_password:             "db_password",
        has_anon_key:             "supabase_anon_key",
        has_service_key:          "supabase_service_key",
        has_service_role_key:     "supabase_service_role_key",
        has_supabase_db_password: "supabase_db_password",
        has_api_key:              "api_key",
        has_aws_secret:           "aws_secret_access_key",
        has_service_account:      "service_account_json",
        has_planetscale_pass:     "planetscale_password",
        has_redis_password:       "redis_password",
      };
      const saved = new Set<string>();
      for (const [hasKey, fieldKey] of Object.entries(HAS_MAP)) {
        if ((data as unknown as Record<string, unknown>)[hasKey]) saved.add(fieldKey);
      }
      setSavedSecretKeys(saved);
    }).catch(() => {});
  }, [token]);

  // ── Notification settings state ──────────────────────────────────────────
  // Company alert emails — stored as comma-separated in DB, shown as chips in Integrations tab
  const [alertEmails, setAlertEmails] = useState<string[]>([]);
  const [emailDraft, setEmailDraft] = useState("");
  const [notifSaving, setNotifSaving] = useState(false);
  const [notifSaved, setNotifSaved] = useState(false);
  const [notifError, setNotifError] = useState("");

  // ── Billing / plan state ───────────────────────────────────────────────
  const [planData, setPlanData] = useState<{
    plan: string;
    plan_label: string;
    usage: { transactions_this_month: number; monthly_limit: number | null; usage_pct: number | null };
    plans: { id: string; price_inr: number; price_display: string; color: string; features: string[] }[];
  } | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planUpgrading, setPlanUpgrading] = useState<string | null>(null);
  const [planError, setPlanError] = useState("");

  useEffect(() => {
    if (!token) return;
    apiClient.getNotificationSettings(token)
      .then((data) => {
        const raw: string = data.company_alert_email || "";
        setAlertEmails(raw ? raw.split(",").map((e: string) => e.trim()).filter(Boolean) : []);
      })
      .catch(() => {});
  }, [token]);

  const handleSaveNotifications = async () => {
    if (!token) return;
    setNotifSaving(true);
    setNotifError("");
    try {
      await apiClient.saveNotificationSettings(
        { company_alert_email: alertEmails.join(",") },
        token
      );
      setNotifSaved(true);
      setTimeout(() => setNotifSaved(false), 4000);
    } catch (e: unknown) {
      setNotifError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setNotifSaving(false);
    }
  };

  // ── BYOK Integrations state ───────────────────────────────────────────────
  const [credentials, setCredentials] = useState<CredentialOut[]>([]);
  const [credLoading, setCredLoading] = useState(false);
  const [credForm, setCredForm] = useState<{ service: string; key_name: string; value: string; label: string }>({ service: "", key_name: "", value: "", label: "" });
  const [credSaving, setCredSaving] = useState(false);
  const [credSaved, setCredSaved] = useState(false);
  const [credError, setCredError] = useState("");
  const [credShowValue, setCredShowValue] = useState(false);
  const [credTestResults, setCredTestResults] = useState<Record<string, { success: boolean; message: string; latency_ms?: number }>>({});
  const [credTesting, setCredTesting] = useState<string | null>(null);
  const [credDeleting, setCredDeleting] = useState<string | null>(null);

  // ── Quick-save state for dedicated email / SMS provider blocks ────────────
  const [resendInput, setResendInput] = useState("");
  const [resendSaving, setResendSaving] = useState(false);
  const [resendSaved, setResendSaved] = useState(false);
  const [brevoInput, setBrevoInput] = useState("");
  const [brevoSaving, setBrevoSaving] = useState(false);
  const [brevoSaved, setBrevoSaved] = useState(false);
  const [fromEmailInput, setFromEmailInput] = useState("");
  const [fromEmailSaving, setFromEmailSaving] = useState(false);
  const [fromEmailSaved, setFromEmailSaved] = useState(false);
  const [twilioSidInput, setTwilioSidInput] = useState("");
  const [twilioTokenInput, setTwilioTokenInput] = useState("");
  const [twilioFromInput, setTwilioFromInput] = useState("");
  const [twilioSaving, setTwilioSaving] = useState(false);
  const [twilioSaved, setTwilioSaved] = useState(false);
  const [providerError, setProviderError] = useState("");

  useEffect(() => {
    if (!token || activeSection !== "integrations") return;
    setCredLoading(true);
    apiClient.listCredentials(token)
      .then(setCredentials)
      .catch(() => {})
      .finally(() => setCredLoading(false));
  }, [token, activeSection]);

  // ── Billing: fetch plan info when billing tab is opened ──────────────────
  useEffect(() => {
    if (!token || activeSection !== "billing") return;
    setPlanLoading(true);
    setPlanError("");
    apiClient.getPlan(token)
      .then(setPlanData)
      .catch((e: unknown) => setPlanError(e instanceof Error ? e.message : "Failed to load plan info"))
      .finally(() => setPlanLoading(false));
  }, [token, activeSection]);

  const handleUpgradePlan = async (targetPlan: string) => {
    if (!token) return;
    setPlanUpgrading(targetPlan);
    setPlanError("");
    try {
      await apiClient.upgradePlan(targetPlan, token);
      // Reload plan data
      const fresh = await apiClient.getPlan(token);
      setPlanData(fresh);
    } catch (e: unknown) {
      setPlanError(e instanceof Error ? e.message : "Upgrade failed");
    } finally {
      setPlanUpgrading(null);
    }
  };

  const handleSaveCredential = async () => {
    if (!token) return;
    const { service, key_name, value } = credForm;
    if (!service.trim() || !key_name.trim() || !value.trim()) {
      setCredError("Service, key name, and value are required.");
      return;
    }
    setCredSaving(true);
    setCredError("");
    try {
      const saved = await apiClient.upsertCredential(
        { service: service.trim(), key_name: key_name.trim(), value: value.trim(), label: credForm.label.trim() || undefined },
        token
      );
      setCredentials((prev) => {
        const idx = prev.findIndex((c) => c.service === saved.service && c.key_name === saved.key_name);
        if (idx >= 0) { const next = [...prev]; next[idx] = saved; return next; }
        return [...prev, saved];
      });
      setCredForm({ service: "", key_name: "", value: "", label: "" });
      setCredSaved(true);
      setTimeout(() => setCredSaved(false), 4000);
    } catch (e: unknown) {
      setCredError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setCredSaving(false);
    }
  };

  // ── Quick-save helpers for email / SMS provider blocks ───────────────────
  const _upsertCred = async (service: string, key_name: string, value: string) => {
    if (!token) throw new Error("Not authenticated");
    const saved = await apiClient.upsertCredential({ service, key_name, value }, token);
    setCredentials((prev) => {
      const idx = prev.findIndex((c) => c.service === service && c.key_name === key_name);
      if (idx >= 0) { const next = [...prev]; next[idx] = saved; return next; }
      return [...prev, saved];
    });
    return saved;
  };

  const handleSaveResendKey = async () => {
    if (!token || !resendInput.trim()) return;
    setResendSaving(true);
    setProviderError("");
    try {
      await _upsertCred("resend", "resend_api_key", resendInput.trim());
      setResendInput("");
      setResendSaved(true);
      setTimeout(() => setResendSaved(false), 4000);
    } catch (e: unknown) {
      setProviderError(e instanceof Error ? e.message : "Failed to save Resend key");
    } finally {
      setResendSaving(false);
    }
  };

  const handleSaveBrevoKey = async () => {
    if (!token || !brevoInput.trim()) return;
    setBrevoSaving(true);
    setProviderError("");
    try {
      await _upsertCred("brevo", "brevo_api_key", brevoInput.trim());
      setBrevoInput("");
      setBrevoSaved(true);
      setTimeout(() => setBrevoSaved(false), 4000);
    } catch (e: unknown) {
      setProviderError(e instanceof Error ? e.message : "Failed to save Brevo key");
    } finally {
      setBrevoSaving(false);
    }
  };

  const handleSaveFromEmail = async () => {
    if (!token || !fromEmailInput.trim()) return;
    setFromEmailSaving(true);
    setProviderError("");
    try {
      await _upsertCred("resend", "from_email", fromEmailInput.trim());
      setFromEmailInput("");
      setFromEmailSaved(true);
      setTimeout(() => setFromEmailSaved(false), 4000);
    } catch (e: unknown) {
      setProviderError(e instanceof Error ? e.message : "Failed to save sender email");
    } finally {
      setFromEmailSaving(false);
    }
  };

  const handleSaveTwilioCreds = async () => {
    if (!token || !twilioSidInput.trim() || !twilioTokenInput.trim()) return;
    setTwilioSaving(true);
    setProviderError("");
    try {
      await _upsertCred("twilio", "twilio_account_sid", twilioSidInput.trim());
      await _upsertCred("twilio", "twilio_auth_token", twilioTokenInput.trim());
      if (twilioFromInput.trim()) {
        await _upsertCred("twilio", "twilio_from_number", twilioFromInput.trim());
      }
      setTwilioSidInput("");
      setTwilioTokenInput("");
      setTwilioFromInput("");
      setTwilioSaved(true);
      setTimeout(() => setTwilioSaved(false), 4000);
    } catch (e: unknown) {
      setProviderError(e instanceof Error ? e.message : "Failed to save Twilio credentials");
    } finally {
      setTwilioSaving(false);
    }
  };

  const handleTestCredential = async (id: string) => {
    if (!token) return;
    setCredTesting(id);
    try {
      const res = await apiClient.testCredential(id, token);
      setCredTestResults((prev) => ({ ...prev, [id]: res }));
    } catch (e: unknown) {
      setCredTestResults((prev) => ({ ...prev, [id]: { success: false, message: e instanceof Error ? e.message : "Test failed" } }));
    } finally {
      setCredTesting(null);
    }
  };

  const handleDeleteCredential = async (id: string) => {
    if (!token) return;
    setCredDeleting(id);
    try {
      await apiClient.deleteCredential(id, token);
      setCredentials((prev) => prev.filter((c) => c.id !== id));
    } catch {} finally {
      setCredDeleting(null);
    }
  };

  const SERVICE_PRESETS = [
    { service: "twilio",   keys: ["twilio_account_sid", "twilio_auth_token", "twilio_from_number"], label: "Twilio (SMS)" },
    { service: "stripe",   keys: ["stripe_secret_key"],                      label: "Stripe (Payments)" },
    { service: "openai",   keys: ["openai_api_key"],                         label: "OpenAI" },
    { service: "firebase", keys: ["firebase_service_account_json"],          label: "Firebase (Push)" },
    { service: "razorpay", keys: ["razorpay_key_id", "razorpay_secret"],     label: "Razorpay" },
  ];

  // ── Fraud Intelligence API Keys state (api-keys tab) ────────────────────
  // Each field maps to a TenantCredential row (service + key_name).
  // On tab open: load existing credentials → show masked values.
  // On save: upsert via credentials API → re-show masked value.
  const FRAUD_API_KEYS = [
    { service: "ipqs",        key_name: "ipqs_api_key",         label: "IPQualityScore — IP Reputation & Proxy Detection", placeholder: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", badge: "5,000/mo free", link: "https://www.ipqualityscore.com/documentation/overview", hint: "Detects VPN, Tor, proxy, and malicious IP addresses in real time" },
    { service: "maxmind",     key_name: "maxmind_license_key",  label: "MaxMind GeoIP2 — License Key",                     placeholder: "XXXXXXXXXX",                      badge: "GeoLite2 free", link: "https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/", hint: "Country, city, and fraud risk score per IP. GeoLite2 is free with registration." },
    { service: "fingerprint", key_name: "fingerprint_api_key",  label: "Fingerprint.js — Device Intelligence",             placeholder: "fp_xxxxxxxxxxxxxxxxxxxxxxxxxx",    badge: "Free tier",     link: "https://dev.fingerprint.com/", hint: "Browser/device fingerprinting to detect device spoofing and account takeover" },
    { service: "ofac",        key_name: "ofac_api_key",         label: "OFAC / Sanctions Screening API",                   placeholder: "your_ofac_api_key",               badge: "Free (direct)", link: "https://ofac.treasury.gov/", hint: "Screens customers against US OFAC Specially Designated Nationals list" },
    { service: "threatmetrix",key_name: "threatmetrix_api_key", label: "ThreatMetrix / LexisNexis — Identity Risk",        placeholder: "tmx_xxxxxxxxxxxxxxxx",            badge: null,            link: "https://risk.lexisnexis.com/products/threatmetrix", hint: "Enterprise identity intelligence and device reputation scoring" },
    { service: "razorpay",    key_name: "razorpay_key_id",      label: "Razorpay API Key — Payment Gateway",               placeholder: "rzp_live_xxxxxxxxxxxxxxxx",       badge: null,            link: "https://razorpay.com/docs/api/", hint: "For Razorpay webhook integration and transaction verification" },
  ] as const;

  // value shown in each input (masked string from API, or plaintext while typing)
  const [apiKeyValues, setApiKeyValues] = useState<Record<string, string>>({});
  // true when the displayed value is the masked string returned by the backend
  const [apiKeyMasked, setApiKeyMasked] = useState<Record<string, boolean>>({});
  // show/hide toggle per field
  const [apiKeyShow, setApiKeyShow] = useState<Record<string, boolean>>({});
  // credential IDs needed for the Test button
  const [apiKeyCredIds, setApiKeyCredIds] = useState<Record<string, string | null>>({});
  // per-field saving/testing
  const [apiKeySaving, setApiKeySaving] = useState<Record<string, boolean>>({});
  const [apiKeyTesting, setApiKeyTesting] = useState<Record<string, boolean>>({});
  const [apiKeyTestResults, setApiKeyTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [apiKeysBulkSaving, setApiKeysBulkSaving] = useState(false);
  const [apiKeysBulkSaved, setApiKeysBulkSaved] = useState(false);

  // Load fraud API key credentials when the tab is opened
  useEffect(() => {
    if (!token || activeSection !== "api-keys") return;
    apiClient.listCredentials(token).then((creds) => {
      const values: Record<string, string> = {};
      const masked: Record<string, boolean> = {};
      const ids: Record<string, string | null> = {};
      for (const fk of FRAUD_API_KEYS) {
        const match = creds.find((c) => c.service === fk.service && c.key_name === fk.key_name);
        const fieldKey = `${fk.service}__${fk.key_name}`;
        values[fieldKey] = match ? match.masked_value : "";
        masked[fieldKey] = !!match;
        ids[fieldKey] = match ? match.id : null;
      }
      setApiKeyValues(values);
      setApiKeyMasked(masked);
      setApiKeyCredIds(ids);
    }).catch(() => {});
  }, [token, activeSection]); // eslint-disable-line react-hooks/exhaustive-deps

  /** Save a single fraud API key and refresh its masked value. */
  const handleSaveFraudApiKey = async (service: string, key_name: string, label: string) => {
    if (!token) return;
    const fieldKey = `${service}__${key_name}`;
    const val = apiKeyValues[fieldKey];
    if (!val || apiKeyMasked[fieldKey]) return; // nothing new to save
    setApiKeySaving((p) => ({ ...p, [fieldKey]: true }));
    try {
      const result = await apiClient.upsertCredential({ service, key_name, value: val, label }, token);
      setApiKeyValues((p) => ({ ...p, [fieldKey]: result.masked_value }));
      setApiKeyMasked((p) => ({ ...p, [fieldKey]: true }));
      setApiKeyCredIds((p) => ({ ...p, [fieldKey]: result.id }));
    } finally {
      setApiKeySaving((p) => ({ ...p, [fieldKey]: false }));
    }
  };

  /** Bulk-save all fraud API keys that have unsaved values. */
  const handleSaveAllFraudApiKeys = async () => {
    if (!token) return;
    setApiKeysBulkSaving(true);
    for (const fk of FRAUD_API_KEYS) {
      const fieldKey = `${fk.service}__${fk.key_name}`;
      const val = apiKeyValues[fieldKey];
      if (val && !apiKeyMasked[fieldKey]) {
        await handleSaveFraudApiKey(fk.service, fk.key_name, fk.label);
      }
    }
    setApiKeysBulkSaving(false);
    setApiKeysBulkSaved(true);
    setTimeout(() => setApiKeysBulkSaved(false), 3000);
  };

  /** Live-test a saved fraud API key. */
  const handleTestFraudApiKey = async (service: string, key_name: string) => {
    if (!token) return;
    const fieldKey = `${service}__${key_name}`;
    const credId = apiKeyCredIds[fieldKey];
    if (!credId) return;
    setApiKeyTesting((p) => ({ ...p, [fieldKey]: true }));
    setApiKeyTestResults((p) => ({ ...p, [fieldKey]: { success: false, message: "" } }));
    try {
      const res = await apiClient.testCredential(credId, token);
      setApiKeyTestResults((p) => ({ ...p, [fieldKey]: { success: res.success, message: res.message } }));
    } catch (e: unknown) {
      setApiKeyTestResults((p) => ({ ...p, [fieldKey]: { success: false, message: e instanceof Error ? e.message : "Test failed" } }));
    } finally {
      setApiKeyTesting((p) => ({ ...p, [fieldKey]: false }));
    }
  };

  const dbDef = DB_TYPES.find((d) => d.id === selectedType)!;

  function fv(key: string) {
    return formValues[key] ?? (dbConfig as Record<string, string> | null)?.[key] ?? "";
  }

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const payload = {
        db_type: selectedType,
        ...Object.fromEntries(
          [...dbDef.fields, ...(dbDef.advancedFields || [])].map((f) => [f.key, fv(f.key) || undefined])
        ),
      };
      if (token) {
        const res = await apiClient.testDbConnection(payload, token);
        setTestResult(res.success ? "success" : "error");
        setTestMessage(res.message + (res.latency_ms ? ` (${res.latency_ms}ms)` : ""));
      } else {
        setTestResult("error");
        setTestMessage("Not authenticated — please log in again.");
      }
    } catch (e: unknown) {
      setTestResult("error");
      setTestMessage(e instanceof Error ? e.message : "Connection test failed.");
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");

    const config: DbConfig = {
      db_type: selectedType,
      label: label || dbDef.name,
      ...Object.fromEntries(
        [...dbDef.fields, ...(dbDef.advancedFields || [])].map((f) => [f.key, fv(f.key)])
      ),
    } as DbConfig;

    try {
      if (token) {
        await apiClient.saveDbConfig(config, token);
        // Refresh saved-secret-keys after a successful save so badges update
        const refreshed = await apiClient.getDbConfig(token);
        const HAS_MAP: Record<string, string> = {
          has_password: "db_password", has_anon_key: "supabase_anon_key",
          has_service_key: "supabase_service_key", has_service_role_key: "supabase_service_role_key",
          has_supabase_db_password: "supabase_db_password", has_api_key: "api_key",
          has_aws_secret: "aws_secret_access_key", has_service_account: "service_account_json",
          has_planetscale_pass: "planetscale_password", has_redis_password: "redis_password",
        };
        const updated = new Set<string>();
        for (const [hk, fk] of Object.entries(HAS_MAP)) {
          if ((refreshed as unknown as Record<string, unknown>)[hk]) updated.add(fk);
        }
        setSavedSecretKeys(updated);
        // Clear secret fields from local form state (they're now saved)
        setFormValues((prev) => {
          const next = { ...prev };
          for (const fk of updated) delete next[fk];
          return next;
        });
      }
      updateDbConfig(config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Silently seed sample data for tenants with zero records (idempotent)
      if (token) {
        apiClient.initializeTenant(token).catch(() => {/* silent — already seeded or DB not ready */});
      }
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "Save failed — check your connection.");
    } finally {
      setSaving(false);
    }
  };

  const planColor =
    user?.plan === "advanced" ? "#8B5CF6" : user?.plan === "pro" ? "#3B82F6" : "#00FF87";

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex">
      {/* App Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-60 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col z-10">
        <div className="p-5 border-b border-[#1E1E2E]">
          <div className="flex items-center gap-2.5">
            <Shield size={22} className="text-[#00FF87]" />
            <span className="font-black text-base">
              Fin<span className="text-[#00FF87]">Shield</span> AI
            </span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {[
            { icon: Activity,       label: "Dashboard",    href: "/dashboard" },
            { icon: TrendingUp,     label: "Transactions", href: "/dashboard/transactions" },
            { icon: AlertTriangle,  label: "Fraud Alerts", href: "/dashboard/alerts" },
            { icon: FlaskConical,   label: "Test Me",      href: "/dashboard/test-me" },
            { icon: Users,          label: "Customers",    href: "/dashboard/customers" },
            { icon: Database,       label: "Data Sources", href: "/dashboard/data-sources" },
            { icon: Table,          label: "Data Schema",  href: "/dashboard/data-schema" },
            { icon: Brain,          label: "ML Training",  href: "/dashboard/ml-training" },
            { icon: Settings,       label: "Settings",     href: "/dashboard/settings", active: true },
          ].map(({ icon: Icon, label: l, href, active }) => (
            <Link
              key={l}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20"
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#111118]"
              }`}
            >
              <Icon size={16} />
              {l}
            </Link>
          ))}
        </nav>

        {/* User profile + sign-out (matches dashboard sidebar) */}
        <div className="p-4 border-t border-[#1E1E2E]">
          {user && (
            <div className="flex items-center gap-3 mb-3">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black shrink-0"
                style={{
                  backgroundColor: `${planColor}20`,
                  color: planColor,
                }}
              >
                {user.avatar_initials}
              </div>
              <div className="min-w-0">
                <div className="text-sm font-semibold truncate flex items-center gap-1.5">
                  {user.full_name}
                  <span
                    className="text-[9px] font-mono px-1.5 py-0.5 rounded-full capitalize shrink-0"
                    style={{
                      color: user.role === "admin" ? "#00FF87" : "#3B82F6",
                      backgroundColor: user.role === "admin" ? "#00FF8715" : "#3B82F615",
                      border: `1px solid ${user.role === "admin" ? "#00FF8740" : "#3B82F640"}`,
                    }}
                  >
                    {user.role}
                  </span>
                </div>
                <div className="text-xs text-gray-500 truncate">{user.email}</div>
              </div>
            </div>
          )}
          <button
            onClick={() => { clearAuth(); router.push("/login"); }}
            className="w-full flex items-center justify-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-2 rounded-lg hover:border-gray-600 transition-all"
          >
            <LogOut size={13} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Settings layout */}
      <div className="ml-60 flex w-full">
        {/* Settings sidebar */}
        <div className="w-52 border-r border-[#1E1E2E] min-h-screen p-4 space-y-1 flex-shrink-0">
          <div className="text-xs text-gray-600 font-mono uppercase tracking-wider px-3 mb-3 mt-2">
            Settings
          </div>
          {SECTIONS.map(({ id, label: l, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveSection(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left ${
                activeSection === id
                  ? "bg-[#111118] text-white border border-[#2E2E3E]"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={15} />
              {l}
            </button>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 p-8 max-w-2xl">

          {/* ── Database Section ── */}
          {activeSection === "database" && (
            <div>
              <h2 className="text-xl font-black mb-1">Database Connection</h2>
              <p className="text-gray-500 text-sm mb-6">
                Connect FinShield to your transaction and customer database. All credentials are encrypted at rest.
              </p>

              {/* DB type picker */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-3 font-medium">Database Type</label>
                <div className="grid grid-cols-1 gap-1.5 max-h-72 overflow-y-auto pr-1 custom-scroll">
                  {DB_TYPES.map((db) => (
                    <button
                      key={db.id}
                      onClick={() => { setSelectedType(db.id); setShowAdvanced(false); setTestResult(null); }}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                        selectedType === db.id ? "border-opacity-80" : "border-[#1E1E2E] hover:border-[#2E2E3E]"
                      }`}
                      style={
                        selectedType === db.id
                          ? { borderColor: db.color, backgroundColor: `${db.color}08` }
                          : {}
                      }
                    >
                      <span className="text-lg w-7 text-center shrink-0">{db.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">{db.name}</span>
                          {db.badge && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono"
                              style={{ backgroundColor: `${db.color}20`, color: db.color, border: `1px solid ${db.color}40` }}>
                              {db.badge}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-600 truncate">{db.description}</div>
                      </div>
                      {db.docs !== "#" && (
                        <a href={db.docs} target="_blank" rel="noopener noreferrer"
                          className="text-gray-600 hover:text-gray-400 ml-1 shrink-0"
                          onClick={(e) => e.stopPropagation()}>
                          <ExternalLink size={11} />
                        </a>
                      )}
                      <div
                        className="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center"
                        style={{
                          borderColor: selectedType === db.id ? db.color : "#2E2E3E",
                          backgroundColor: selectedType === db.id ? db.color : "transparent",
                        }}
                      >
                        {selectedType === db.id && <div className="w-1.5 h-1.5 rounded-full bg-black" />}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Connection label */}
              <div className="mb-5">
                <label className="block text-sm text-gray-400 mb-1.5 font-medium">Connection Label</label>
                <input
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder={`e.g. Production ${dbDef.name}`}
                  className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                />
              </div>

              {/* Required credential fields */}
              <div className="space-y-4 mb-3">
                {dbDef.fields.map((field) => (
                  <FieldInput
                    key={field.key}
                    field={field}
                    value={fv(field.key)}
                    shown={showSecrets[field.key]}
                    isSaved={field.secret ? savedSecretKeys.has(field.key) && !formValues[field.key] : false}
                    onChange={(val) => setFormValues((p) => ({ ...p, [field.key]: val }))}
                    onToggleSecret={() => setShowSecrets((p) => ({ ...p, [field.key]: !p[field.key] }))}
                  />
                ))}
              </div>

              {/* Advanced fields toggle */}
              {dbDef.advancedFields && dbDef.advancedFields.length > 0 && (
                <div className="mb-5">
                  <button
                    onClick={() => setShowAdvanced((v) => !v)}
                    className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showAdvanced ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    {showAdvanced ? "Hide advanced settings" : "Show advanced settings (SSL, pool size, schema…)"}
                  </button>
                  {showAdvanced && (
                    <div className="mt-4 space-y-4 border-l-2 border-[#1E1E2E] pl-4">
                      {dbDef.advancedFields.map((field) => (
                        <FieldInput
                          key={field.key}
                          field={field}
                          value={fv(field.key)}
                          shown={showSecrets[field.key]}
                          isSaved={field.secret ? savedSecretKeys.has(field.key) && !formValues[field.key] : false}
                          onChange={(val) => setFormValues((p) => ({ ...p, [field.key]: val }))}
                          onToggleSecret={() => setShowSecrets((p) => ({ ...p, [field.key]: !p[field.key] }))}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Test + Save */}
              <div className="flex gap-3 items-start mt-2">
                <button
                  onClick={handleTest}
                  disabled={testing}
                  className="flex items-center gap-2 text-sm border border-[#1E1E2E] px-4 py-2.5 rounded-xl hover:border-[#00FF87]/40 text-gray-400 hover:text-white transition-all disabled:opacity-50"
                >
                  {testing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
                  {testing ? "Testing…" : "Test Connection"}
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                >
                  {saving ? <Loader2 size={14} className="animate-spin" />
                    : saved ? <CheckCircle2 size={14} />
                    : <Save size={14} />}
                  {saving ? "Saving…" : saved ? "Saved!" : "Save Changes"}
                </button>
              </div>

              {saveError && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]"
                >
                  <AlertCircle size={14} />
                  {saveError}
                </motion.div>
              )}
              {testResult && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-4 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl ${
                    testResult === "success"
                      ? "bg-[#00FF87]/10 border border-[#00FF87]/30 text-[#00FF87]"
                      : "bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]"
                  }`}
                >
                  {testResult === "success" ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                  {testMessage}
                </motion.div>
              )}
            </div>
          )}

          {/* ── Integrations (BYOK) Section ── */}
          {activeSection === "integrations" && (
            <div>
              <h2 className="text-xl font-black mb-1">Integrations — Bring Your Own Keys</h2>
              <p className="text-gray-500 text-sm mb-6">
                Store third-party API credentials securely. All values are encrypted with AES-256 before being written to the database — raw keys are never exposed to the frontend.
              </p>

              {/* ── Company Alert Emails ── */}
              <div className="bg-[#00FF87]/05 border border-[#00FF87]/20 rounded-2xl p-5 mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <Mail size={16} className="text-[#00FF87]" />
                  <span className="text-sm font-bold text-[#00FF87]">Company Alert Emails</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20 font-mono ml-1">Required for email alerts</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  All fraud alerts will be sent to <strong className="text-gray-400">every email below</strong>. Add your entire fraud team — type an email and press <kbd className="font-mono bg-[#1E1E2E] px-1 rounded text-gray-400">Enter</kbd> or <kbd className="font-mono bg-[#1E1E2E] px-1 rounded text-gray-400">,</kbd> to add.
                </p>

                {/* Tag chips for existing emails */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {alertEmails.map((email) => (
                    <span
                      key={email}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/30 font-mono"
                    >
                      {email}
                      <button
                        type="button"
                        onClick={() => setAlertEmails((prev) => prev.filter((e) => e !== email))}
                        className="text-[#00FF87]/60 hover:text-[#EF4444] transition-colors ml-0.5"
                      >
                        <X size={11} />
                      </button>
                    </span>
                  ))}
                </div>

                {/* Input to add a new email */}
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={emailDraft}
                    onChange={(e) => setEmailDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === ",") {
                        e.preventDefault();
                        const val = emailDraft.trim().replace(/,$/, "");
                        if (val && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val) && !alertEmails.includes(val)) {
                          setAlertEmails((prev) => [...prev, val]);
                        }
                        setEmailDraft("");
                      } else if (e.key === "Backspace" && !emailDraft && alertEmails.length > 0) {
                        setAlertEmails((prev) => prev.slice(0, -1));
                      }
                    }}
                    placeholder={alertEmails.length === 0 ? "fraud@yourcompany.com" : "Add another email…"}
                    className="flex-1 bg-[#0A0A0F] border border-[#00FF87]/30 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/70 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const val = emailDraft.trim().replace(/,$/, "");
                      if (val && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val) && !alertEmails.includes(val)) {
                        setAlertEmails((prev) => [...prev, val]);
                      }
                      setEmailDraft("");
                    }}
                    className="flex items-center gap-1.5 text-xs px-4 py-2.5 rounded-xl bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/30 hover:bg-[#00FF87]/20 transition-all font-semibold"
                  >
                    <Plus size={13} /> Add
                  </button>
                </div>
                {alertEmails.length > 0 && (
                  <p className="text-[11px] text-gray-600 mt-2">
                    {alertEmails.length} recipient{alertEmails.length > 1 ? "s" : ""} — all will receive fraud alert emails.
                  </p>
                )}

                {/* Save email list */}
                <div className="flex items-center gap-3 mt-4">
                  <button
                    onClick={handleSaveNotifications}
                    disabled={notifSaving}
                    className="flex items-center gap-2 text-xs bg-[#00FF87] text-black font-bold px-4 py-2 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                  >
                    {notifSaving ? <Loader2 size={13} className="animate-spin" />
                      : notifSaved ? <CheckCircle2 size={13} />
                      : <Save size={13} />}
                    {notifSaving ? "Saving…" : notifSaved ? "Saved!" : "Save Alert Emails"}
                  </button>
                  {notifError && (
                    <span className="flex items-center gap-1.5 text-xs text-[#EF4444]">
                      <AlertCircle size={12} /> {notifError}
                    </span>
                  )}
                  {notifSaved && (
                    <span className="flex items-center gap-1.5 text-xs text-[#00FF87]">
                      <CheckCircle2 size={12} /> Saved successfully.
                    </span>
                  )}
                </div>
              </div>

              {/* ── Email Provider (Resend) — API Key + Sender Email ── */}
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Mail size={15} className="text-[#3B82F6]" />
                    <span className="text-sm font-bold text-white">Email Provider — Resend</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20">Primary — 3,000 emails/month free</span>
                  </div>
                  {credentials.some(c => c.service === "resend" && c.key_name === "resend_api_key") ? (
                    <span className="flex items-center gap-1 text-xs font-semibold text-[#00FF87]">
                      <CheckCircle2 size={12} /> Configured
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-[#EF4444]">
                      <AlertCircle size={12} /> Not configured — emails won&apos;t fire
                    </span>
                  )}
                </div>

                {/* Row 1 — API Key */}
                <div className="mb-4">
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-gray-500 mb-1.5">
                    API Key <span className="text-[#EF4444]">*</span>
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    Starts with <span className="font-mono text-gray-400">re_</span>. Get a free key at <span className="text-[#3B82F6]">resend.com</span>.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={resendInput}
                      onChange={(e) => setResendInput(e.target.value)}
                      placeholder="re_••••••••••••••••••••••••"
                      autoComplete="new-password"
                      className="flex-1 bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#3B82F6]/60 transition-colors"
                    />
                    <button
                      onClick={handleSaveResendKey}
                      disabled={resendSaving || !resendInput.trim()}
                      className="flex items-center gap-2 text-sm bg-[#3B82F6] text-white font-bold px-5 py-2.5 rounded-xl hover:bg-[#2563EB] transition-all disabled:opacity-50"
                    >
                      {resendSaving ? <Loader2 size={13} className="animate-spin" /> : resendSaved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                      {resendSaving ? "Saving…" : resendSaved ? "Saved!" : "Save"}
                    </button>
                  </div>
                </div>

                {/* Row 2 — Sender Email (From:) */}
                <div className="border-t border-[#1E1E2E] pt-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="block text-[10px] font-mono uppercase tracking-wider text-gray-500">
                      Sender Email — From: address
                    </label>
                    {credentials.some(c => c.service === "resend" && c.key_name === "from_email") ? (
                      <span className="flex items-center gap-1 text-[10px] font-semibold text-[#00FF87]">
                        <CheckCircle2 size={10} /> Set
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] text-[#F59E0B]">
                        <AlertTriangle size={10} /> Using test domain
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mb-1">
                    The address fraud alerts are sent <strong className="text-gray-300">FROM</strong> (e.g. <span className="font-mono text-gray-400">alerts@yourbank.com</span>). Also used by Brevo.
                  </p>
                  <p className="text-xs text-[#F59E0B] mb-2">
                    ⚠️ Without this, Resend uses <span className="font-mono">onboarding@resend.dev</span> — only delivers to your own Resend account inbox. Verify a domain first at <span className="text-[#3B82F6]">resend.com/domains</span>.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={fromEmailInput}
                      onChange={(e) => setFromEmailInput(e.target.value)}
                      placeholder="alerts@yourcompany.com"
                      autoComplete="email"
                      className="flex-1 bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#3B82F6]/60 transition-colors"
                    />
                    <button
                      onClick={handleSaveFromEmail}
                      disabled={fromEmailSaving || !fromEmailInput.trim()}
                      className="flex items-center gap-2 text-sm bg-[#3B82F6] text-white font-bold px-5 py-2.5 rounded-xl hover:bg-[#2563EB] transition-all disabled:opacity-50"
                    >
                      {fromEmailSaving ? <Loader2 size={13} className="animate-spin" /> : fromEmailSaved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                      {fromEmailSaving ? "Saving…" : fromEmailSaved ? "Saved!" : "Save"}
                    </button>
                  </div>
                </div>
              </div>

              {/* ── Email Provider (Brevo) — fallback ── */}
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Mail size={15} className="text-[#0092CC]" />
                    <span className="text-sm font-bold text-white">Email Provider — Brevo</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0092CC]/10 text-[#0092CC] border border-[#0092CC]/20">Fallback — 300 emails/day free</span>
                  </div>
                  {credentials.some(c => c.service === "brevo") ? (
                    <span className="flex items-center gap-1 text-xs font-semibold text-[#00FF87]">
                      <CheckCircle2 size={12} /> Configured
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <AlertCircle size={12} /> Not configured
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mb-1">
                  Paste your <strong className="text-gray-300">Brevo API key</strong> (starts with <span className="font-mono text-gray-400">xkeysib-</span>). Get one free at <span className="text-[#0092CC]">brevo.com</span> — 9,000 emails/month.
                </p>
                <p className="text-xs text-gray-600 mb-3">
                  Used automatically when Resend is not configured. Uses the <strong className="text-gray-400">Sender Email (From:)</strong> saved in the Resend block above.
                </p>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={brevoInput}
                    onChange={(e) => setBrevoInput(e.target.value)}
                    placeholder="xkeysib-••••••••••••••••••••••••"
                    autoComplete="new-password"
                    className="flex-1 bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#0092CC]/60 transition-colors"
                  />
                  <button
                    onClick={handleSaveBrevoKey}
                    disabled={brevoSaving || !brevoInput.trim()}
                    className="flex items-center gap-2 text-sm bg-[#0092CC] text-white font-bold px-5 py-2.5 rounded-xl hover:bg-[#0078a8] transition-all disabled:opacity-50"
                  >
                    {brevoSaving ? <Loader2 size={13} className="animate-spin" /> : brevoSaved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                    {brevoSaving ? "Saving…" : brevoSaved ? "Saved!" : "Save"}
                  </button>
                </div>
              </div>

              {/* ── SMS Provider (Twilio) quick-save block ── */}
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[15px]">📱</span>
                    <span className="text-sm font-bold text-white">SMS Provider — Twilio Credentials</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/20">Optional — High/Critical alerts</span>
                  </div>
                  {credentials.some(c => c.service === "twilio") ? (
                    <span className="flex items-center gap-1 text-xs font-semibold text-[#00FF87]">
                      <CheckCircle2 size={12} /> Configured
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <AlertCircle size={12} /> Not configured — SMS disabled
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-2 mb-2">
                  <input
                    type="password"
                    value={twilioSidInput}
                    onChange={(e) => setTwilioSidInput(e.target.value)}
                    placeholder="Account SID (ACxx…)"
                    autoComplete="new-password"
                    className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#8B5CF6]/60 transition-colors"
                  />
                  <input
                    type="password"
                    value={twilioTokenInput}
                    onChange={(e) => setTwilioTokenInput(e.target.value)}
                    placeholder="Auth Token"
                    autoComplete="new-password"
                    className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#8B5CF6]/60 transition-colors"
                  />
                  <input
                    type="text"
                    value={twilioFromInput}
                    onChange={(e) => setTwilioFromInput(e.target.value)}
                    placeholder="From number (+1…)"
                    autoComplete="new-password"
                    className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#8B5CF6]/60 transition-colors"
                  />
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <button
                    onClick={handleSaveTwilioCreds}
                    disabled={twilioSaving || !twilioSidInput.trim() || !twilioTokenInput.trim()}
                    className="flex items-center gap-2 text-sm bg-[#8B5CF6] text-white font-bold px-5 py-2.5 rounded-xl hover:bg-[#7C3AED] transition-all disabled:opacity-50"
                  >
                    {twilioSaving ? <Loader2 size={13} className="animate-spin" /> : twilioSaved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                    {twilioSaving ? "Saving…" : twilioSaved ? "Saved!" : "Save Twilio Credentials"}
                  </button>
                  {providerError && (
                    <span className="flex items-center gap-1.5 text-xs text-[#EF4444]">
                      <AlertCircle size={12} /> {providerError}
                    </span>
                  )}
                </div>
              </div>

              {/* Saved credentials list */}
              {credLoading ? (
                <div className="flex items-center gap-2 text-gray-500 text-sm mb-6">
                  <Loader2 size={14} className="animate-spin" /> Loading saved credentials…
                </div>
              ) : credentials.length > 0 ? (
                <div className="mb-8 space-y-3">
                  <div className="text-xs text-gray-600 font-mono uppercase tracking-wider mb-2">Saved Credentials</div>
                  {credentials.map((cred) => {
                    const testRes = credTestResults[cred.id];
                    return (
                      <div key={cred.id} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-semibold text-white capitalize">{cred.service}</span>
                              <span className="text-[10px] font-mono text-gray-500 bg-[#1E1E2E] px-2 py-0.5 rounded-full">{cred.key_name}</span>
                              {cred.label && <span className="text-[10px] text-gray-500">{cred.label}</span>}
                            </div>
                            <div className="font-mono text-sm text-gray-400 tracking-wider">{cred.masked_value}</div>
                            {testRes && (
                              <div className={`mt-2 flex items-center gap-1.5 text-xs ${testRes.success ? "text-[#00FF87]" : "text-[#EF4444]"}`}>
                                {testRes.success ? <CheckCircle2 size={11} /> : <AlertCircle size={11} />}
                                {testRes.message}
                                {testRes.latency_ms != null && <span className="text-gray-600">({testRes.latency_ms}ms)</span>}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => handleTestCredential(cred.id)}
                              disabled={credTesting === cred.id}
                              className="flex items-center gap-1.5 text-xs border border-[#1E1E2E] px-3 py-1.5 rounded-xl hover:border-[#00FF87]/40 text-gray-400 hover:text-white transition-all disabled:opacity-50"
                            >
                              {credTesting === cred.id ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
                              Test
                            </button>
                            <button
                              onClick={() => setCredForm({ service: cred.service, key_name: cred.key_name, value: "", label: cred.label || "" })}
                              className="text-xs border border-[#1E1E2E] px-3 py-1.5 rounded-xl text-gray-400 hover:text-white hover:border-[#3B82F6]/40 transition-all"
                            >
                              Replace
                            </button>
                            <button
                              onClick={() => handleDeleteCredential(cred.id)}
                              disabled={credDeleting === cred.id}
                              className="text-xs border border-[#1E1E2E] px-3 py-1.5 rounded-xl text-gray-400 hover:text-[#EF4444] hover:border-[#EF4444]/40 transition-all disabled:opacity-50"
                            >
                              {credDeleting === cred.id ? <Loader2 size={11} className="animate-spin" /> : <X size={11} />}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="bg-[#111118] border border-dashed border-[#2E2E3E] rounded-2xl p-6 mb-8 text-center text-sm text-gray-600">
                  No credentials saved yet. Add your first key below.
                </div>
              )}

              {/* Quick presets */}
              <div className="mb-5">
                <div className="text-xs text-gray-600 font-mono uppercase tracking-wider mb-2">Quick Preset</div>
                <div className="flex flex-wrap gap-2">
                  {SERVICE_PRESETS.map((p) => (
                    <button
                      key={p.service}
                      onClick={() => setCredForm((prev) => ({ ...prev, service: p.service, key_name: p.keys[0] }))}
                      className={`text-xs px-3 py-1.5 rounded-xl border transition-all ${
                        credForm.service === p.service
                          ? "bg-[#3B82F6]/10 border-[#3B82F6]/40 text-[#3B82F6]"
                          : "border-[#1E1E2E] text-gray-500 hover:text-gray-300 hover:border-[#2E2E3E]"
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Add / Replace form */}
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 space-y-4">
                <div className="text-xs text-gray-600 font-mono uppercase tracking-wider">
                  {credForm.service && credentials.some(c => c.service === credForm.service && c.key_name === credForm.key_name) ? "Replace Credential" : "Add Credential"}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1.5">Service</label>
                    <input
                      type="text"
                      value={credForm.service}
                      onChange={(e) => setCredForm((p) => ({ ...p, service: e.target.value.toLowerCase().replace(/\s/g, "_") }))}
                      placeholder="resend"
                      className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1.5">Key Name</label>
                    <input
                      type="text"
                      value={credForm.key_name}
                      onChange={(e) => setCredForm((p) => ({ ...p, key_name: e.target.value.toLowerCase().replace(/\s/g, "_") }))}
                      placeholder="resend_api_key"
                      className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1.5">Label (optional)</label>
                  <input
                    type="text"
                    value={credForm.label}
                    onChange={(e) => setCredForm((p) => ({ ...p, label: e.target.value }))}
                    placeholder="Production API Key"
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1.5">Secret Value</label>
                  <div className="relative">
                    <input
                      type={credShowValue ? "text" : "password"}
                      value={credForm.value}
                      onChange={(e) => setCredForm((p) => ({ ...p, value: e.target.value }))}
                      placeholder="Paste your API key here — encrypted before storage"
                      autoComplete="new-password"
                      className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setCredShowValue((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                    >
                      {credShowValue ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                  <p className="text-[11px] text-gray-600 mt-1.5 flex items-center gap-1">
                    <Shield size={10} className="text-[#00FF87]" />
                    Encrypted with AES-256 (Fernet) before writing to the database. Raw value is never stored.
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-1">
                  <button
                    onClick={handleSaveCredential}
                    disabled={credSaving}
                    className="flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                  >
                    {credSaving ? <Loader2 size={14} className="animate-spin" />
                      : credSaved ? <CheckCircle2 size={14} />
                      : <Save size={14} />}
                    {credSaving ? "Saving…" : credSaved ? "Saved!" : "Save Credential"}
                  </button>
                  {(credForm.service || credForm.value) && (
                    <button
                      type="button"
                      onClick={() => { setCredForm({ service: "", key_name: "", value: "", label: "" }); setCredError(""); }}
                      className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                    >
                      Clear
                    </button>
                  )}
                </div>

                {credError && (
                  <div className="flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]">
                    <AlertCircle size={13} /> {credError}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── API Keys Section — live save/load via TenantCredential ── */}
          {activeSection === "api-keys" && (
            <div>
              <h2 className="text-xl font-black mb-1">Fraud Intelligence API Keys</h2>
              <p className="text-gray-500 text-sm mb-2">
                Optional third-party enrichment services. FinShield uses built-in fallbacks when not configured.
              </p>
              {/* Security note */}
              <div className="flex items-start gap-2 p-3 bg-[#00FF87]/05 border border-[#00FF87]/20 rounded-xl mb-6">
                <Shield size={13} className="text-[#00FF87] mt-0.5 shrink-0" />
                <p className="text-[11px] text-gray-400">
                  All keys are encrypted with <strong className="text-white">AES-256 (Fernet)</strong> before being stored in your Supabase database.
                  On every login they auto-populate as <span className="font-mono text-[#00FF87]">••••••••xxxx</span> — plaintext is never sent to the browser.
                  Each institution&apos;s keys are fully isolated by <code className="text-gray-400">tenant_id</code>.
                </p>
              </div>

              <div className="space-y-5">
                {FRAUD_API_KEYS.map((fk) => {
                  const fieldKey = `${fk.service}__${fk.key_name}`;
                  const val       = apiKeyValues[fieldKey] ?? "";
                  const isMasked  = apiKeyMasked[fieldKey] ?? false;
                  const isShown   = apiKeyShow[fieldKey]   ?? false;
                  const isSaving  = apiKeySaving[fieldKey] ?? false;
                  const isTesting = apiKeyTesting[fieldKey] ?? false;
                  const testRes   = apiKeyTestResults[fieldKey];
                  const credId    = apiKeyCredIds[fieldKey];
                  const hasUnsaved = val && !isMasked;

                  return (
                    <div key={fieldKey} className={`bg-[#111118] border rounded-2xl p-4 transition-colors ${isMasked ? "border-[#00FF87]/25" : "border-[#1E1E2E]"}`}>
                      {/* Header */}
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <label className="text-sm text-gray-300 font-medium">{fk.label}</label>
                        {fk.badge && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 font-mono">
                            {fk.badge}
                          </span>
                        )}
                        {isMasked && (
                          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/25 font-semibold">
                            <CheckCircle2 size={9} /> Encrypted &amp; saved
                          </span>
                        )}
                        <a href={fk.link} target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-400 ml-auto">
                          <ExternalLink size={11} />
                        </a>
                      </div>
                      <div className="text-xs text-gray-600 mb-3">{fk.hint}</div>

                      {/* Input + actions row */}
                      <div className="flex gap-2 items-center">
                        <div className="relative flex-1">
                          <input
                            type={isShown ? "text" : "password"}
                            value={val}
                            onFocus={() => {
                              // Clicking a masked field clears it so user can type a fresh value
                              if (isMasked) {
                                setApiKeyValues((p) => ({ ...p, [fieldKey]: "" }));
                                setApiKeyMasked((p) => ({ ...p, [fieldKey]: false }));
                              }
                            }}
                            onChange={(e) => {
                              setApiKeyValues((p) => ({ ...p, [fieldKey]: e.target.value }));
                              setApiKeyMasked((p) => ({ ...p, [fieldKey]: false }));
                            }}
                            placeholder={isMasked ? val : fk.placeholder}
                            autoComplete="new-password"
                            className={`w-full bg-[#0A0A0F] border rounded-xl px-4 py-2.5 text-sm font-mono pr-10 focus:outline-none transition-colors placeholder-gray-600 ${
                              isMasked
                                ? "border-[#00FF87]/25 text-[#00FF87] focus:border-[#00FF87]/60"
                                : "border-[#1E1E2E] text-white focus:border-[#00FF87]/60"
                            }`}
                          />
                          <button
                            type="button"
                            onClick={() => setApiKeyShow((p) => ({ ...p, [fieldKey]: !p[fieldKey] }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                          >
                            {isShown ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                        </div>

                        {/* Save this key */}
                        {hasUnsaved && (
                          <button
                            onClick={() => handleSaveFraudApiKey(fk.service, fk.key_name, fk.label)}
                            disabled={isSaving}
                            className="shrink-0 flex items-center gap-1.5 text-xs bg-[#00FF87] text-black font-bold px-3 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                          >
                            {isSaving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                            Save
                          </button>
                        )}

                        {/* Live-test (only when a credential is saved) */}
                        {credId && (
                          <button
                            onClick={() => handleTestFraudApiKey(fk.service, fk.key_name)}
                            disabled={isTesting}
                            title="Live-test this key"
                            className="shrink-0 flex items-center gap-1.5 text-xs border border-[#1E1E2E] text-gray-400 px-3 py-2.5 rounded-xl hover:border-[#00FF87]/40 hover:text-white transition-all disabled:opacity-50"
                          >
                            {isTesting ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                            Test
                          </button>
                        )}
                      </div>

                      {/* Test result */}
                      {testRes?.message && (
                        <div className={`mt-2 flex items-center gap-1.5 text-xs ${testRes.success ? "text-[#00FF87]" : "text-[#EF4444]"}`}>
                          {testRes.success ? <CheckCircle2 size={11} /> : <AlertCircle size={11} />}
                          {testRes.message}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Bulk save all unsaved keys */}
              <div className="flex items-center gap-3 mt-6">
                <button
                  onClick={handleSaveAllFraudApiKeys}
                  disabled={apiKeysBulkSaving || FRAUD_API_KEYS.every((fk) => apiKeyMasked[`${fk.service}__${fk.key_name}`] || !apiKeyValues[`${fk.service}__${fk.key_name}`])}
                  className="flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-50"
                >
                  {apiKeysBulkSaving ? <Loader2 size={14} className="animate-spin" />
                    : apiKeysBulkSaved ? <CheckCircle2 size={14} />
                    : <Save size={14} />}
                  {apiKeysBulkSaving ? "Saving…" : apiKeysBulkSaved ? "All Keys Saved!" : "Save All Keys"}
                </button>
                <p className="text-xs text-gray-600">
                  Keys are encrypted &amp; stored per-tenant in Supabase. They auto-populate on next login.
                </p>
              </div>
            </div>
          )}

          {/* ── Account Section ── */}
          {activeSection === "account" && (
            <div>
              <h2 className="text-xl font-black mb-1">Account</h2>
              <p className="text-gray-500 text-sm mb-7">Your profile and institution settings.</p>
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 space-y-4">
                {[
                  { label: "Full Name",        value: user?.full_name || "—" },
                  { label: "Email",            value: user?.email || "—" },
                  { label: "Institution Name", value: user?.institution_name || "—" },
                  { label: "Institution Type", value: user?.institution_type || "—" },
                  { label: "Role",             value: user?.role || "—" },
                  { label: "Plan",             value: user?.plan?.toUpperCase() || "FREE" },
                ].map(({ label: l, value }) => (
                  <div key={l} className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{l}</span>
                    <span className="text-sm font-medium capitalize">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Billing Section ── */}
          {activeSection === "billing" && (
            <div>
              <h2 className="text-xl font-black mb-1">Billing &amp; Plan</h2>
              <p className="text-gray-500 text-sm mb-7">Manage your subscription and usage.</p>

              {planError && (
                <div className="mb-4 bg-red-900/20 border border-red-500/30 rounded-xl p-3 text-sm text-red-400 flex gap-2">
                  <AlertCircle size={14} className="mt-0.5 flex-shrink-0" /> {planError}
                </div>
              )}

              {planLoading ? (
                <div className="flex items-center gap-2 text-gray-500 py-8">
                  <Loader2 size={18} className="animate-spin" /> Loading plan info…
                </div>
              ) : planData ? (
                <>
                  {/* Usage bar */}
                  {planData.usage.monthly_limit !== null && (
                    <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Monthly Transaction Usage</span>
                        <span className="text-sm font-mono text-white">
                          {planData.usage.transactions_this_month.toLocaleString()} / {planData.usage.monthly_limit.toLocaleString()}
                        </span>
                      </div>
                      <div className="w-full bg-[#1E1E2E] rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(100, planData.usage.usage_pct ?? 0)}%`,
                            backgroundColor: (planData.usage.usage_pct ?? 0) > 80 ? "#EF4444" : planColor,
                          }}
                        />
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {planData.usage.usage_pct !== null ? `${planData.usage.usage_pct.toFixed(1)}% used this month` : ""}
                      </div>
                    </div>
                  )}

                  {/* 3 Plan cards */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    {planData.plans.map((p) => {
                      const isCurrent = p.id === planData.plan;
                      const isDowngrade = (
                        (planData.plan === "advanced" && (p.id === "pro" || p.id === "free")) ||
                        (planData.plan === "pro" && p.id === "free")
                      );
                      return (
                        <div
                          key={p.id}
                          className="relative rounded-2xl p-5 border transition-all flex flex-col"
                          style={{
                            borderColor: isCurrent ? p.color : "#1E1E2E",
                            backgroundColor: isCurrent ? `${p.color}08` : "#111118",
                            boxShadow: isCurrent ? `0 0 0 1px ${p.color}40` : undefined,
                          }}
                        >
                          {isCurrent && (
                            <div
                              className="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider"
                              style={{ backgroundColor: p.color, color: "#0A0A0F" }}
                            >
                              Current Plan
                            </div>
                          )}

                          <div className="mb-3">
                            <div className="text-base font-black capitalize mb-0.5" style={{ color: p.color }}>
                              {p.id === "free" ? "Free" : p.id === "pro" ? "Pro" : "Advanced"}
                            </div>
                            <div className="text-2xl font-black text-white">{p.price_display}</div>
                          </div>

                          <ul className="flex-1 space-y-1.5 mb-5">
                            {p.features.map((f) => (
                              <li key={f} className="flex items-start gap-2 text-xs text-gray-400">
                                <CheckCircle2 size={12} className="mt-0.5 flex-shrink-0" style={{ color: p.color }} />
                                {f}
                              </li>
                            ))}
                          </ul>

                          {isCurrent ? (
                            <div
                              className="w-full text-center text-xs font-bold py-2.5 rounded-xl opacity-60"
                              style={{ backgroundColor: `${p.color}20`, color: p.color }}
                            >
                              Active
                            </div>
                          ) : isDowngrade ? (
                            <button
                              disabled
                              className="w-full text-center text-xs font-semibold py-2.5 rounded-xl bg-[#1E1E2E] text-gray-600 cursor-not-allowed"
                            >
                              Downgrade not available
                            </button>
                          ) : (
                            <button
                              onClick={() => handleUpgradePlan(p.id)}
                              disabled={planUpgrading !== null}
                              className="w-full text-center text-xs font-bold py-2.5 rounded-xl transition-all flex items-center justify-center gap-2"
                              style={{
                                backgroundColor: p.color,
                                color: "#0A0A0F",
                                opacity: planUpgrading ? 0.7 : 1,
                              }}
                            >
                              {planUpgrading === p.id ? (
                                <><Loader2 size={13} className="animate-spin" /> Upgrading…</>
                              ) : (
                                `Upgrade to ${p.id === "pro" ? "Pro" : "Advanced"}`
                              )}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : (
                /* Fallback: show current plan from auth store */
                <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Current Plan</span>
                    <span
                      className="text-sm font-bold px-3 py-1 rounded-full capitalize"
                      style={{ color: planColor, backgroundColor: `${planColor}15`, border: `1px solid ${planColor}40` }}
                    >
                      {user?.plan ?? "free"}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── FieldInput sub-component ─────────────────────────────────────────────────
function FieldInput({
  field,
  value,
  shown,
  isSaved = false,
  onChange,
  onToggleSecret,
}: {
  field: DbFieldDef;
  value: string;
  shown: boolean;
  isSaved?: boolean;
  onChange: (v: string) => void;
  onToggleSecret: () => void;
}) {
  const isSecret = field.secret;
  const inputType = isSecret && !shown ? "password" : field.type === "number" ? "number" : "text";

  return (
    <div>
      <div className="flex items-center gap-2 mb-1.5">
        <label className="text-sm text-gray-400 font-medium">{field.label}</label>
        {isSaved && (
          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-mono bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/25">
            🔒 Saved
          </span>
        )}
      </div>
      {field.hint && <div className="text-xs text-gray-600 mb-1.5">{field.hint}</div>}
      {field.type === "select" ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00FF87]/60 transition-colors"
        >
          <option value="">{field.placeholder}</option>
          {field.options?.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      ) : (
        <div className="relative">
          <input
            type={inputType}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={isSaved ? "Enter new value to update…" : field.placeholder}
            autoComplete={isSecret ? "new-password" : "off"}
            className={`w-full bg-[#111118] border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none transition-colors pr-10 ${
              isSaved ? "border-[#00FF87]/25 focus:border-[#00FF87]/60" : "border-[#1E1E2E] focus:border-[#00FF87]/60"
            }`}
          />
          {isSecret && (
            <button
              type="button"
              onClick={onToggleSecret}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
            >
              {shown ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
