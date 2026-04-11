"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Shield, Database, Save, Zap, Loader2, CheckCircle2,
  AlertCircle, Eye, EyeOff, ExternalLink, Settings, Bell,
  Key, User, CreditCard, ChevronDown, ChevronUp,
  Mail, MessageSquare, Activity, TrendingUp, AlertTriangle,
  FlaskConical, Users, Table, Brain, X, Plus, LogOut,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore, DbConfig, DbType } from "@/store/auth-store";
import { apiClient } from "@/lib/api-client";

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
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "api-keys",      label: "API Keys",      icon: Key },
  { id: "account",       label: "Account",       icon: User },
  { id: "billing",       label: "Billing",       icon: CreditCard },
];

// ── Component ────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { user, dbConfig, updateDbConfig, token, clearAuth } = useAuthStore();
  const router = useRouter();

  const [activeSection, setActiveSection] = useState("database");
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
  // Multiple company alert emails stored as an array; saved as comma-separated string
  const [alertEmails, setAlertEmails] = useState<string[]>([]);
  const [emailDraft, setEmailDraft] = useState(""); // current input before adding
  const [notifSmsEnabled, setNotifSmsEnabled] = useState(true);
  const [notifResendKey, setNotifResendKey] = useState("");
  const [notifTwilioSid, setNotifTwilioSid] = useState("");
  const [notifTwilioToken, setNotifTwilioToken] = useState("");
  const [notifTwilioFrom, setNotifTwilioFrom] = useState("");
  const [notifSaving, setNotifSaving] = useState(false);
  const [notifSaved, setNotifSaved] = useState(false);
  const [notifError, setNotifError] = useState("");
  const [showNotifSecrets, setShowNotifSecrets] = useState<Record<string, boolean>>({});
  // Tracks whether a key is already saved in DB (so we can show "Saved ✓" badge)
  const [hasResend, setHasResend] = useState(false);
  const [hasTwilio, setHasTwilio] = useState(false);

  useEffect(() => {
    if (!token) return;
    apiClient.getNotificationSettings(token)
      .then((data) => {
        // Parse comma-separated company alert emails into array
        const raw: string = data.company_alert_email || "";
        setAlertEmails(raw ? raw.split(",").map((e: string) => e.trim()).filter(Boolean) : []);
        setNotifSmsEnabled(data.sms_enabled ?? true);
        setHasResend(data.has_resend ?? false);
        setHasTwilio(data.has_twilio ?? false);
      })
      .catch(() => {});
  }, [token]);

  const handleSaveNotifications = async () => {
    if (!token) return;
    setNotifSaving(true);
    setNotifError("");
    try {
      const body: Record<string, string | boolean> = {
        company_alert_email: alertEmails.join(","),
        sms_enabled: notifSmsEnabled,
      };
      if (notifResendKey.trim())   body.resend_api_key     = notifResendKey.trim();
      if (notifTwilioSid.trim())   body.twilio_account_sid = notifTwilioSid.trim();
      if (notifTwilioToken.trim()) body.twilio_auth_token  = notifTwilioToken.trim();
      if (notifTwilioFrom.trim())  body.twilio_from_number = notifTwilioFrom.trim();
      await apiClient.saveNotificationSettings(body, token);
      // Update saved-key indicators based on what was just submitted
      if (notifResendKey.trim()) setHasResend(true);
      if (notifTwilioSid.trim() && notifTwilioToken.trim() && notifTwilioFrom.trim()) setHasTwilio(true);
      // Clear input fields after save (key is now in DB — show badge instead)
      setNotifResendKey("");
      setNotifTwilioSid("");
      setNotifTwilioToken("");
      setNotifTwilioFrom("");
      setNotifSaved(true);
      setTimeout(() => setNotifSaved(false), 4000);
    } catch (e: unknown) {
      setNotifError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setNotifSaving(false);
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
        {user && (
          <div className="p-4 border-t border-[#1E1E2E]">
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
            <button
              onClick={() => { clearAuth(); router.push("/login"); }}
              className="w-full flex items-center justify-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-2 rounded-lg hover:border-gray-600 transition-all"
            >
              <LogOut size={13} /> Sign Out
            </button>
          </div>
        )}
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

          {/* ── Notifications Section ── */}
          {activeSection === "notifications" && (
            <div>
              <h2 className="text-xl font-black mb-1">Notification Services</h2>
              <p className="text-gray-500 text-sm mb-6">
                Configure where fraud alerts are sent. The company alert email is required for your team to receive notifications. All API keys are optional — the platform falls back gracefully to in-app alerts.
              </p>

              {/* Company Alert Emails — multi-email tag input */}
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
              </div>

              {/* SMS toggle */}
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare size={15} className="text-[#3B82F6]" />
                    <div>
                      <div className="text-sm font-semibold">SMS Alerts via Twilio</div>
                      <div className="text-xs text-gray-500 mt-0.5">Send SMS to customer phone for CRITICAL and HIGH severity fraud events</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setNotifSmsEnabled((v) => !v)}
                    className="flex items-center gap-1.5 transition-all"
                  >
                    {notifSmsEnabled ? (
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-[#00FF87]">
                        <span className="w-10 h-5 bg-[#00FF87]/30 border border-[#00FF87]/50 rounded-full flex items-center px-0.5">
                          <span className="w-4 h-4 bg-[#00FF87] rounded-full ml-auto shadow-sm" />
                        </span>
                        ON
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500">
                        <span className="w-10 h-5 bg-[#1E1E2E] border border-[#2E2E3E] rounded-full flex items-center px-0.5">
                          <span className="w-4 h-4 bg-gray-600 rounded-full shadow-sm" />
                        </span>
                        OFF
                      </span>
                    )}
                  </button>
                </div>
              </div>

              {/* API Key fields */}
              <div className="space-y-5">
                {/* Resend */}
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <label className="text-sm text-gray-400 font-medium">Resend.com API Key — Email</label>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20 font-mono">3,000/mo free</span>
                    <a href="https://resend.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-400"><ExternalLink size={11} /></a>
                    {hasResend && !notifResendKey && (
                      <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/30 font-semibold">
                        <CheckCircle2 size={9} /> Key saved
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600 mb-1.5">Preferred email provider. Sign up at resend.com — API key starts with <span className="font-mono">re_</span></div>
                  <div className="relative">
                    <input
                      type={showNotifSecrets["resend"] ? "text" : "password"}
                      value={notifResendKey}
                      onChange={(e) => setNotifResendKey(e.target.value)}
                      placeholder={hasResend ? "re_•••••••••••• (saved — enter new key to replace)" : "re_xxxxxxxxxxxxxxxxxx"}
                      className={`w-full bg-[#111118] border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none transition-colors pr-10 ${hasResend && !notifResendKey ? "border-[#00FF87]/30 focus:border-[#00FF87]/60" : "border-[#1E1E2E] focus:border-[#00FF87]/60"}`}
                    />
                    <button type="button" onClick={() => setShowNotifSecrets(p => ({...p, resend: !p.resend}))} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
                      {showNotifSecrets["resend"] ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                {/* Twilio */}
                <div className={`bg-[#111118] rounded-2xl p-4 space-y-4 ${hasTwilio ? "border border-[#3B82F6]/30" : "border border-[#1E1E2E]"}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <MessageSquare size={13} className="text-[#3B82F6]" />
                    <span className="text-sm font-semibold text-gray-300">Twilio SMS Credentials</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 font-mono">Paid ~₹0.10/SMS</span>
                    <a href="https://console.twilio.com/" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-400"><ExternalLink size={11} /></a>
                    {hasTwilio && !notifTwilioSid && (
                      <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/30 font-semibold">
                        <CheckCircle2 size={9} /> Credentials saved
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600">Required for SMS alerts to customers. All three fields must be filled to enable SMS.</div>
                  {[
                    { key: "sid",   label: "Account SID",  val: notifTwilioSid,   set: setNotifTwilioSid,   ph: hasTwilio ? "AC•••••••••••••••• (saved)" : "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
                    { key: "token", label: "Auth Token",   val: notifTwilioToken, set: setNotifTwilioToken, ph: hasTwilio ? "•••••••••••••••••• (saved)" : "your_32_char_auth_token" },
                    { key: "from",  label: "From Number",  val: notifTwilioFrom,  set: setNotifTwilioFrom,  ph: hasTwilio ? "+1••••••••• (saved)" : "+12025551234" },
                  ].map(({ key, label: lbl, val, set, ph }) => (
                    <div key={key}>
                      <label className="block text-xs text-gray-500 mb-1">{lbl}</label>
                      <div className="relative">
                        <input
                          type={showNotifSecrets[key] ? "text" : "password"}
                          value={val}
                          onChange={(e) => set(e.target.value)}
                          placeholder={ph}
                          className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#3B82F6]/60 transition-colors pr-10"
                        />
                        <button type="button" onClick={() => setShowNotifSecrets(p => ({...p, [key]: !p[key]}))} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
                          {showNotifSecrets[key] ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Save */}
              <div className="flex items-center gap-3 mt-6">
                <button
                  onClick={handleSaveNotifications}
                  disabled={notifSaving}
                  className="flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                >
                  {notifSaving ? <Loader2 size={14} className="animate-spin" />
                    : notifSaved ? <CheckCircle2 size={14} />
                    : <Save size={14} />}
                  {notifSaving ? "Saving…" : notifSaved ? "Saved!" : "Save Notification Settings"}
                </button>
              </div>
              {notifError && (
                <div className="mt-3 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]">
                  <AlertCircle size={13} /> {notifError}
                </div>
              )}
              {notifSaved && (
                <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                  className="mt-3 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl bg-[#00FF87]/10 border border-[#00FF87]/30 text-[#00FF87]">
                  <CheckCircle2 size={13} /> Notification settings saved successfully.
                </motion.div>
              )}
            </div>
          )}

                    {/* ── API Keys Section ── */}
          {activeSection === "api-keys" && (
            <div>
              <h2 className="text-xl font-black mb-1">Fraud Intelligence API Keys</h2>
              <p className="text-gray-500 text-sm mb-7">
                Optional third-party enrichment services. FinShield uses built-in fallbacks when not configured.
              </p>
              <div className="space-y-6">
                {[
                  {
                    label: "IPQualityScore — IP Reputation & Proxy Detection",
                    placeholder: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    badge: "5,000/mo free",
                    link: "https://www.ipqualityscore.com/documentation/overview",
                    hint: "Detects VPN, Tor, proxy, and malicious IP addresses in real time",
                    secret: true,
                  },
                  {
                    label: "MaxMind GeoIP2 — Geolocation & Fraud Score",
                    placeholder: "xxxxxxxxxx",
                    badge: null,
                    link: "https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/",
                    hint: "Provides country, city, and fraud risk score per IP. GeoLite2 is free.",
                    secret: true,
                  },
                  {
                    label: "Fingerprint.js — Device Intelligence",
                    placeholder: "fp_xxxxxxxxxxxxxxxxxxxxxxxxxx",
                    badge: "Free tier",
                    link: "https://dev.fingerprint.com/",
                    hint: "Browser/device fingerprinting to detect device spoofing and account takeover",
                    secret: true,
                  },
                  {
                    label: "OFAC / Sanctions Screening API",
                    placeholder: "your_ofac_api_key",
                    badge: "Free (OFAC direct)",
                    link: "https://ofac.treasury.gov/",
                    hint: "Screens customers against US OFAC Specially Designated Nationals list",
                    secret: true,
                  },
                  {
                    label: "ThreatMetrix / LexisNexis — Identity Risk",
                    placeholder: "tmx_xxxxxxxxxxxxxxxx",
                    badge: null,
                    link: "https://risk.lexisnexis.com/products/threatmetrix",
                    hint: "Enterprise identity intelligence and device reputation scoring",
                    secret: true,
                  },
                  {
                    label: "Razorpay API Key — Payment Gateway",
                    placeholder: "rzp_live_xxxxxxxxxxxxxxxx",
                    badge: null,
                    link: "https://razorpay.com/docs/api/",
                    hint: "For Razorpay webhook integration and transaction verification",
                    secret: true,
                  },
                ].map(({ label: l, placeholder, badge, link, hint, secret }) => (
                  <div key={l}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <label className="text-sm text-gray-400 font-medium">{l}</label>
                      {badge && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 font-mono">
                          {badge}
                        </span>
                      )}
                      {link && (
                        <a href={link} target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-400">
                          <ExternalLink size={11} />
                        </a>
                      )}
                    </div>
                    {hint && <div className="text-xs text-gray-600 mb-1.5">{hint}</div>}
                    <input
                      type={secret ? "password" : "text"}
                      placeholder={placeholder}
                      className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                    />
                  </div>
                ))}
              </div>
              <button className="mt-6 flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all">
                <Save size={14} /> Save API Keys
              </button>
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
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 mb-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-400">Current Plan</span>
                  <span
                    className="text-sm font-bold px-3 py-1 rounded-full capitalize"
                    style={{
                      color: planColor,
                      backgroundColor: `${planColor}15`,
                      border: `1px solid ${planColor}40`,
                    }}
                  >
                    {user?.plan}
                  </span>
                </div>
                {user?.plan === "free" && (
                  <Link
                    href="/signup"
                    className="block w-full text-center bg-[#3B82F6] text-white font-bold py-2.5 rounded-xl hover:bg-[#2563EB] transition-all text-sm"
                  >
                    Upgrade to Pro — ₹9,999/mo
                  </Link>
                )}
              </div>
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
