"use client";

import { useAuthStore, isAdmin, type AuthUser } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, RefreshCw, Brain,
  CheckCircle2, XCircle, Clock, Table2, List, X, BookOpen, Table,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

// ── ML Schema definitions (canonical FinShield expected columns) ─────────────
interface SchemaSpec {
  field: string;
  type: string;
  required: boolean;
  ml_category: string;
  description: string;
}

const CUSTOMER_SCHEMA_SPEC: SchemaSpec[] = [
  { field: "customer_id",          type: "UUID",       required: true,  ml_category: "Entity",       description: "Unique customer identifier — used to join transaction history" },
  { field: "full_name",            type: "STRING",     required: false, ml_category: "Entity",       description: "Customer full name — used for notification only" },
  { field: "email",                type: "STRING",     required: false, ml_category: "Entity",       description: "Email address — used for fraud alert delivery" },
  { field: "phone_number",         type: "STRING",     required: false, ml_category: "Entity",       description: "Mobile number (E.164 format) — used for SMS alerts" },
  { field: "date_of_birth",        type: "DATE",       required: false, ml_category: "Behavioral",   description: "Date of birth — used to compute customer age as an ML feature" },
  { field: "city",                 type: "STRING",     required: false, ml_category: "Geographic",   description: "City of residence — used for impossible travel baseline" },
  { field: "state_province",       type: "STRING",     required: false, ml_category: "Geographic",   description: "State / province — used in geographic risk scoring" },
  { field: "country_code",         type: "STRING(2)",  required: false, ml_category: "Geographic",   description: "ISO-2 country code — used for cross-border fraud detection" },
  { field: "account_type",         type: "ENUM",       required: false, ml_category: "Entity",       description: "personal / business / merchant — affects spend pattern baseline" },
  { field: "account_opening_date", type: "DATE",       required: false, ml_category: "Entity",       description: "Account age in days — new accounts have higher fraud risk" },
  { field: "account_status",       type: "ENUM",       required: false, ml_category: "Entity",       description: "active / inactive / suspended — blocked accounts flag anomalies" },
  { field: "kyc_status",           type: "ENUM",       required: false, ml_category: "Compliance",   description: "pending / verified / rejected — unverified accounts get higher risk weight" },
  { field: "risk_score",           type: "DECIMAL",    required: false, ml_category: "ML Output",    description: "Existing risk score (0–1) — used as a prior in ensemble scoring" },
  { field: "customer_tier",        type: "ENUM",       required: false, ml_category: "Entity",       description: "standard / premium / vip — affects amount anomaly thresholds" },
  { field: "balance_amount",       type: "DECIMAL",    required: false, ml_category: "Amount",       description: "Account balance — used to compute amount-to-balance ratio feature" },
  { field: "active_card_count",    type: "INTEGER",    required: false, ml_category: "Entity",       description: "Number of active cards — multiple cards increase risk exposure" },
];

const TRANSACTION_SCHEMA_SPEC: SchemaSpec[] = [
  { field: "transaction_id",           type: "UUID",        required: true,  ml_category: "Identifier",   description: "Unique transaction ID — primary key" },
  { field: "customer_id",              type: "UUID",        required: true,  ml_category: "Entity Link",  description: "Foreign key to customers — required for all velocity/behavioral features" },
  { field: "amount",                   type: "DECIMAL",     required: true,  ml_category: "Amount ★",     description: "Transaction amount — most important ML feature; used in z-score, ratio, velocity sum" },
  { field: "currency",                 type: "STRING(3)",   required: true,  ml_category: "Amount",       description: "ISO-3 currency code (e.g. INR, USD) — used for currency mismatch detection" },
  { field: "transaction_type",         type: "ENUM",        required: true,  ml_category: "Behavioral",   description: "purchase / withdrawal / transfer / refund — each type has different fraud patterns" },
  { field: "channel",                  type: "ENUM ★",      required: true,  ml_category: "Channel ★",    description: "pos_physical / online / atm / mobile — channel is a top-5 fraud predictor" },
  { field: "merchant_category_code",   type: "STRING(4)",   required: false, ml_category: "Behavioral",   description: "MCC code — unusual category for a customer flags behavioral anomaly" },
  { field: "merchant_name",            type: "STRING",      required: false, ml_category: "Behavioral",   description: "Merchant name — used for new-merchant-category detection" },
  { field: "transaction_location_lat", type: "DECIMAL",     required: false, ml_category: "Geographic ★", description: "Latitude — critical for impossible travel detection (requires lng pair)" },
  { field: "transaction_location_lng", type: "DECIMAL",     required: false, ml_category: "Geographic ★", description: "Longitude — critical for impossible travel detection (requires lat pair)" },
  { field: "transaction_country_code", type: "STRING(2)",   required: false, ml_category: "Geographic",   description: "Country of transaction — cross-border detection, high-risk country scoring" },
  { field: "ip_address",               type: "INET",        required: false, ml_category: "Network",      description: "Client IP — used for proxy/VPN/Tor detection and IP reputation scoring" },
  { field: "device_fingerprint",       type: "STRING ★",    required: false, ml_category: "Device ★",     description: "Device fingerprint hash — is_new_device feature is top-3 fraud predictor" },
  { field: "device_type",              type: "ENUM",        required: false, ml_category: "Device",       description: "mobile / desktop / tablet / pos_terminal — device type affects risk baseline" },
  { field: "status",                   type: "ENUM",        required: true,  ml_category: "Status",       description: "pending / completed / blocked — FinShield writes back status = blocked on fraud" },
  { field: "transaction_timestamp",    type: "TIMESTAMPTZ ★", required: true, ml_category: "Temporal ★",  description: "Transaction time — used for velocity windows, hour-of-day, impossible travel timing" },
  { field: "fraud_score",              type: "DECIMAL",     required: false, ml_category: "ML Output",    description: "FinShield writes fraud score (0–1) here after scoring" },
  { field: "fraud_category",           type: "ENUM",        required: false, ml_category: "ML Output",    description: "FinShield writes: legitimate / suspicious / fraudulent / unscored" },
  { field: "fraud_risk_level",         type: "ENUM",        required: false, ml_category: "ML Output",    description: "FinShield writes: low / medium / high / critical" },
  { field: "is_test",                  type: "BOOLEAN",     required: false, ml_category: "System",       description: "Flag for test transactions — excluded from model training data" },
];

// ── ML Schema Modal ──────────────────────────────────────────────────────────
function MLSchemaModal({
  title,
  subtitle,
  schema,
  onClose,
}: {
  title: string;
  subtitle: string;
  schema: SchemaSpec[];
  onClose: () => void;
}) {
  const categoryColor: Record<string, string> = {
    "Amount ★":      "#00FF87",
    "Amount":        "#00FF87",
    "Channel ★":     "#3B82F6",
    "Geographic ★":  "#F97316",
    "Geographic":    "#F97316",
    "Device ★":      "#8B5CF6",
    "Device":        "#8B5CF6",
    "Temporal ★":    "#EF4444",
    "Behavioral":    "#F59E0B",
    "Entity":        "#6B7280",
    "Entity Link":   "#6B7280",
    "Network":       "#06B6D4",
    "Compliance":    "#10B981",
    "ML Output":     "#00FF87",
    "Identifier":    "#4B5563",
    "Status":        "#4B5563",
    "System":        "#4B5563",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-[#111118] border border-[#1E1E2E] rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-[#1E1E2E]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <BookOpen size={16} className="text-[#00FF87]" />
              <h2 className="text-base font-black">{title}</h2>
            </div>
            <p className="text-xs text-gray-500">{subtitle}</p>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-[10px] text-gray-600">★ = top ML feature</span>
              <span className="flex items-center gap-1 text-[10px] text-[#EF4444]">
                <span className="w-2 h-2 rounded-full bg-[#EF4444] inline-block" /> Required
              </span>
              <span className="flex items-center gap-1 text-[10px] text-gray-500">
                <span className="w-2 h-2 rounded-full bg-gray-600 inline-block" /> Optional
              </span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-600 hover:text-white transition-colors mt-1">
            <X size={18} />
          </button>
        </div>

        {/* Table */}
        <div className="overflow-y-auto flex-1 p-1">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-[#111118] z-10">
              <tr className="border-b border-[#1E1E2E]">
                {["Column Name", "Data Type", "Required", "ML Category", "How It&apos;s Used in ML"].map((h) => (
                  <th key={h} className="text-left text-gray-500 font-medium py-2.5 px-3 first:pl-4">
                    {h.replace("&apos;", "'")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {schema.map((row, i) => {
                const catColor = categoryColor[row.ml_category] || "#6B7280";
                const isOutput = row.ml_category === "ML Output";
                return (
                  <tr
                    key={i}
                    className={`border-b border-[#1E1E2E]/40 hover:bg-[#0A0A0F] transition-all ${
                      isOutput ? "opacity-60" : ""
                    }`}
                  >
                    <td className="py-2 px-3 pl-4">
                      <span className="font-mono text-white">{row.field}</span>
                      {isOutput && (
                        <span className="ml-1.5 text-[9px] text-[#00FF87] border border-[#00FF87]/30 px-1 rounded">
                          written by FinShield
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <span className="font-mono text-[#8B5CF6] bg-[#8B5CF6]/10 px-1.5 py-0.5 rounded text-[10px]">
                        {row.type}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      {row.required ? (
                        <span className="flex items-center gap-1 text-[#EF4444] font-semibold">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444]" /> Yes
                        </span>
                      ) : (
                        <span className="text-gray-600">Optional</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-medium"
                        style={{ backgroundColor: `${catColor}15`, color: catColor }}
                      >
                        {row.ml_category}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-400 leading-relaxed">{row.description}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#1E1E2E] flex items-center justify-between">
          <span className="text-xs text-gray-600">
            {schema.filter((s) => s.required).length} required · {schema.filter((s) => !s.required).length} optional · {schema.length} total columns
          </span>
          <button
            onClick={onClose}
            className="text-xs bg-[#1E1E2E] hover:bg-[#2E2E3E] text-white px-4 py-2 rounded-xl transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Types ────────────────────────────────────────────────────────────────────
interface TableInfo { name: string; row_count: number; size_kb: number; }
interface SourceInfo {
  db_type: string;
  db_url_masked: string;
  status: string;
  latency_ms: number;
  tables: TableInfo[];
  last_checked: string;
}
interface SchemaColumn {
  table: string;
  column: string;
  type: string;
  nullable: boolean;
  description: string;
  sample_values: (string | number | null)[];
}
interface FieldMapEntry {
  column: string;
  fraud_relevance: string;
  values?: string[];
  range?: string;
  notes: string;
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ plan, user, clearAuth, router }: {
  plan: string;
  user: AuthUser;
  clearAuth: () => void;
  router: ReturnType<typeof useRouter>;
}) {
  const planColor = plan === "advanced" ? "#8B5CF6" : plan === "pro" ? "#3B82F6" : "#00FF87";
  const navItems = [
    { icon: Activity,      label: "Dashboard",    href: "/dashboard",             active: false, adminOnly: false },
    { icon: TrendingUp,    label: "Transactions",  href: "/dashboard/transactions", active: false, adminOnly: false },
    { icon: AlertTriangle, label: "Fraud Alerts",  href: "/dashboard/alerts",       active: false, adminOnly: false },
    { icon: FlaskConical,  label: "Test Me",       href: "/dashboard/test-me",      active: false, adminOnly: true },
    { icon: Users,         label: "Customers",     href: "/dashboard/customers",    active: false, adminOnly: false },
    { icon: Database,      label: "Data Sources",  href: "/dashboard/data-sources", active: true,  adminOnly: false },
    { icon: Table,         label: "Data Schema",   href: "/dashboard/data-schema",  active: false, adminOnly: false },
    { icon: Brain,         label: "ML Training",   href: "/dashboard/ml-training",  active: false, adminOnly: false },
    { icon: Settings,      label: "Settings",      href: "/dashboard/settings",     active: false, adminOnly: false },
  ];
  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col z-10">
      <div className="p-5 border-b border-[#1E1E2E]">
        <div className="flex items-center gap-2.5">
          <Shield size={22} className="text-[#00FF87]" />
          <span className="font-black text-base">Fin<span className="text-[#00FF87]">Shield</span> AI</span>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems
          .filter(({ adminOnly }) => !adminOnly || isAdmin(user))
          .map(({ icon: Icon, label, href, active }) => (
          <Link key={label} href={href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              active
                ? "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20"
                : "text-gray-500 hover:text-gray-300 hover:bg-[#111118]"
            }`}>
            <Icon size={16} />{label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-[#1E1E2E]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black"
            style={{ backgroundColor: `${planColor}20`, color: planColor }}>
            {user.avatar_initials}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold truncate">{user.full_name}</div>
            <div className="text-xs text-gray-500 truncate">{user.email}</div>
          </div>
        </div>
        <button onClick={() => { clearAuth(); router.push("/login"); }}
          className="w-full flex items-center justify-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-2 rounded-lg hover:border-gray-600 transition-all">
          <LogOut size={13} /> Sign Out
        </button>
      </div>
    </aside>
  );
}

// ── Relevance badge colors ───────────────────────────────────────────────────
function relevanceColor(r: string) {
  if (r === "critical")  return { bg: "#EF4444", text: "#EF4444" };
  if (r === "high")      return { bg: "#F59E0B", text: "#F59E0B" };
  if (r === "medium")    return { bg: "#3B82F6", text: "#3B82F6" };
  return { bg: "#6B7280", text: "#6B7280" };
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function DataSourcesPage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();

  const [source, setSource] = useState<SourceInfo | null>(null);
  const [schema, setSchema] = useState<SchemaColumn[]>([]);
  const [fieldMap, setFieldMap] = useState<FieldMapEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"schema" | "fieldmap">("schema");
  const [schemaFilter, setSchemaFilter] = useState("");
  const [mlModal, setMlModal] = useState<"customers" | "transactions" | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  const fetchAll = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [src, sch, fm] = await Promise.all([
        apiClient.getDataSources(token),
        apiClient.getDataSourceSchema(token),
        apiClient.getDataSourceFieldMap(token),
      ]);

      // ── Map backend { sources: [...] } → SourceInfo ──────────────────────
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = src as any;
      const firstSrc = (raw.sources || [])[0] || {};
      setSource({
        db_type:       firstSrc.connector_type || firstSrc.type || "Database",
        db_url_masked: firstSrc.connector_type || firstSrc.name || "—",
        status:        firstSrc.status === "live" ? "connected" : firstSrc.status || "unknown",
        latency_ms:    firstSrc.latency_ms ?? 0,
        tables:        (firstSrc.tables || []).map((t: { table_name: string; record_count: number }) => ({
          name:      t.table_name,
          row_count: t.record_count,
          size_kb:   0,
        })),
        last_checked:  firstSrc.last_synced || new Date().toISOString(),
      });

      // ── Flatten backend { schema: [{table, columns:[{name,...}]}] } ───────
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const schRaw = sch as any;
      const flat: SchemaColumn[] = (schRaw.schema || []).flatMap(
        (tbl: { table: string; columns: { name: string; type: string; nullable: boolean; description: string; sample_values: (string | number | null)[] }[] }) =>
          (tbl.columns || []).map((col) => ({
            table:         tbl.table,
            column:        col.name,
            type:          col.type,
            nullable:      col.nullable,
            description:   col.description,
            sample_values: col.sample_values || [],
          }))
      );
      setSchema(flat);

      // ── Map backend { key_fields: [{field, fraud_relevance, ...}] } ──────
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const fmRaw = fm as any;
      const mapped: FieldMapEntry[] = (fmRaw.key_fields || []).map(
        (f: { field: string; fraud_relevance: string; description: string; stats?: { min: number; max: number; avg: number }; enum_distribution?: { value: string; count: number }[] }) => {
          const rel = f.fraud_relevance || "";
          const relevanceKey = rel.toLowerCase().startsWith("critical") ? "critical"
            : rel.toLowerCase().startsWith("high") ? "high"
            : rel.toLowerCase().startsWith("medium") ? "medium"
            : "low";
          return {
            column: f.field,
            fraud_relevance: relevanceKey,
            values:  f.enum_distribution?.map((e) => `${e.value} (${e.count})`),
            range:   f.stats
              ? `Min: ₹${f.stats.min?.toFixed(0)} / Max: ₹${f.stats.max?.toFixed(0)} / Avg: ₹${f.stats.avg?.toFixed(0)}`
              : undefined,
            notes: f.description,
          };
        }
      );
      setFieldMap(mapped);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  const filteredSchema = schema.filter(
    (col) =>
      col.table?.toLowerCase().includes(schemaFilter.toLowerCase()) ||
      col.column?.toLowerCase().includes(schemaFilter.toLowerCase()) ||
      col.type?.toLowerCase().includes(schemaFilter.toLowerCase())
  );

  const DB_ICONS: Record<string, string> = {
    sqlite: "🗄️", supabase: "⚡", postgresql: "🐘", mysql: "🐬", mongodb: "🍃", rest_api: "🔌",
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <Sidebar plan={user.plan} user={user} clearAuth={clearAuth} router={router} />

      <main className="ml-60 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Data Sources</h1>
            <p className="text-gray-500 text-sm mt-1">Connected database, schema explorer, and fraud-relevant fields</p>
          </div>
          <button
            onClick={fetchAll}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Source Card */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 mb-6">
          {loading ? (
            <div className="h-20 bg-[#0A0A0F] rounded-xl animate-pulse" />
          ) : source ? (
            <div className="flex items-center gap-6">
              <div className="w-14 h-14 rounded-2xl bg-[#00FF87]/10 border border-[#00FF87]/20 flex items-center justify-center text-2xl">
                {DB_ICONS[source.db_type] || "🗄️"}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-bold text-lg capitalize">{source.db_type}</span>
                  {source.status === "connected" ? (
                    <span className="flex items-center gap-1.5 text-xs text-[#00FF87] bg-[#00FF87]/10 px-2 py-0.5 rounded-full">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#00FF87] animate-pulse" />
                      Connected
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-xs text-[#EF4444] bg-[#EF4444]/10 px-2 py-0.5 rounded-full">
                      <XCircle size={10} /> Disconnected
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 font-mono">{source.db_url_masked}</div>
              </div>
              <div className="flex gap-6 text-center">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Latency</div>
                  <div className="flex items-center gap-1 text-sm font-semibold">
                    <Clock size={12} className="text-[#3B82F6]" />
                    <span className="text-[#3B82F6]">{source.latency_ms}ms</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Last Check</div>
                  <div className="text-xs text-gray-400">
                    {new Date(source.last_checked).toLocaleTimeString()}
                  </div>
                </div>
              </div>
              <Link
                href="/dashboard/settings"
                className="text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
              >
                Configure
              </Link>
            </div>
          ) : (
            <div className="text-center text-gray-600 text-sm py-4">Could not load source info</div>
          )}
        </div>

        {/* Table row counts */}
        {!loading && source?.tables && source.tables.length > 0 && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            {source.tables.map((tbl) => (
              <div key={tbl.name} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Table2 size={14} className="text-[#3B82F6]" />
                  <span className="text-xs text-gray-400 font-mono">{tbl.name}</span>
                </div>
                <div className="text-2xl font-black text-white">{tbl.row_count.toLocaleString()}</div>
                <div className="text-xs text-gray-600">rows</div>
              </div>
            ))}
          </div>
        )}

        {/* ML Schema Requirements card */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <BookOpen size={15} className="text-[#00FF87]" />
                <span className="text-sm font-bold">ML Schema Requirements</span>
              </div>
              <p className="text-xs text-gray-500 max-w-lg">
                FinShield&apos;s ML engine expects specific columns in your Customer and Transaction tables.
                View the full list of expected fields, their types, and how each one powers fraud detection.
              </p>
            </div>
            <div className="flex gap-3 shrink-0 ml-6">
              <button
                onClick={() => setMlModal("customers")}
                className="flex items-center gap-2 text-xs font-semibold border border-[#3B82F6]/40 text-[#3B82F6] bg-[#3B82F6]/08 hover:bg-[#3B82F6]/15 px-4 py-2.5 rounded-xl transition-all"
              >
                <Users size={13} />
                Customer Schema
                <span className="text-[10px] text-[#3B82F6]/60 font-mono">
                  {CUSTOMER_SCHEMA_SPEC.length} cols
                </span>
              </button>
              <button
                onClick={() => setMlModal("transactions")}
                className="flex items-center gap-2 text-xs font-semibold border border-[#8B5CF6]/40 text-[#8B5CF6] bg-[#8B5CF6]/08 hover:bg-[#8B5CF6]/15 px-4 py-2.5 rounded-xl transition-all"
              >
                <Database size={13} />
                Transaction Schema
                <span className="text-[10px] text-[#8B5CF6]/60 font-mono">
                  {TRANSACTION_SCHEMA_SPEC.length} cols
                </span>
              </button>
            </div>
          </div>

          {/* Quick stat pills */}
          <div className="flex gap-3 mt-4 flex-wrap">
            {[
              { label: "Amount",      color: "#00FF87", note: "Top ML signal" },
              { label: "Channel",     color: "#3B82F6", note: "Top-5 predictor" },
              { label: "Device fingerprint", color: "#8B5CF6", note: "Top-3 predictor" },
              { label: "Geo coordinates",    color: "#F97316", note: "Impossible travel" },
              { label: "Timestamp",   color: "#EF4444", note: "Velocity windows" },
            ].map(({ label, color, note }) => (
              <span
                key={label}
                className="flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full font-medium"
                style={{ backgroundColor: `${color}12`, color, border: `1px solid ${color}30` }}
              >
                ★ {label}
                <span className="text-[9px] opacity-60">— {note}</span>
              </span>
            ))}
          </div>
        </div>

        {/* ML Schema Modals */}
        {mlModal === "customers" && (
          <MLSchemaModal
            title="Expected Customer Table Columns"
            subtitle="These are the columns FinShield reads from your customers table to build ML features. Missing columns degrade model accuracy."
            schema={CUSTOMER_SCHEMA_SPEC}
            onClose={() => setMlModal(null)}
          />
        )}
        {mlModal === "transactions" && (
          <MLSchemaModal
            title="Expected Transaction Table Columns"
            subtitle="These are the columns FinShield reads from your transactions table. Columns marked ★ are the top fraud predictors — ensure they are populated."
            schema={TRANSACTION_SCHEMA_SPEC}
            onClose={() => setMlModal(null)}
          />
        )}

        {/* Tabs: Schema / Field Map */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl overflow-hidden">
          <div className="flex border-b border-[#1E1E2E]">
            {(["schema", "fieldmap"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-all ${
                  activeTab === tab
                    ? "text-white border-b-2 border-[#00FF87]"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab === "schema" ? <><List size={14} /> Schema Explorer</> : <><Database size={14} /> Fraud Field Map</>}
              </button>
            ))}
            {activeTab === "schema" && (
              <div className="ml-auto pr-4 flex items-center">
                <input
                  value={schemaFilter}
                  onChange={(e) => setSchemaFilter(e.target.value)}
                  placeholder="Filter columns…"
                  className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/40 w-40"
                />
              </div>
            )}
          </div>

          <div className="p-4 overflow-x-auto">
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-8 bg-[#0A0A0F] rounded animate-pulse" />
                ))}
              </div>
            ) : activeTab === "schema" ? (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#1E1E2E]">
                    {["Table", "Column", "Type", "Nullable", "Description", "Sample Values"].map(h => (
                      <th key={h} className="text-left text-gray-500 font-medium pb-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredSchema.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-600">No columns found</td>
                    </tr>
                  ) : (
                    filteredSchema.map((col, i) => (
                      <tr key={i} className="border-b border-[#1E1E2E]/40 hover:bg-[#0A0A0F] transition-all">
                        <td className="py-2 pr-4 font-mono text-[#3B82F6]">{col.table}</td>
                        <td className="py-2 pr-4 font-mono text-white">{col.column}</td>
                        <td className="py-2 pr-4">
                          <span className="bg-[#8B5CF6]/10 text-[#8B5CF6] px-2 py-0.5 rounded font-mono">
                            {col.type}
                          </span>
                        </td>
                        <td className="py-2 pr-4">
                          {col.nullable ? (
                            <span className="text-[#F59E0B]">nullable</span>
                          ) : (
                            <CheckCircle2 size={12} className="text-[#00FF87]" />
                          )}
                        </td>
                        <td className="py-2 pr-4 text-gray-400 max-w-[180px] truncate">{col.description}</td>
                        <td className="py-2 pr-4">
                          <div className="flex gap-1 flex-wrap">
                            {(col.sample_values || []).slice(0, 3).map((v, j) => (
                              <span
                                key={j}
                                className="bg-[#1E1E2E] text-gray-300 px-1.5 py-0.5 rounded font-mono text-xs"
                              >
                                {v === null ? "NULL" : String(v).slice(0, 20)}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            ) : (
              /* Field Map tab */
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#1E1E2E]">
                    {["Column", "Fraud Relevance", "Values / Range", "Notes"].map(h => (
                      <th key={h} className="text-left text-gray-500 font-medium pb-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fieldMap.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-gray-600">No field map available</td>
                    </tr>
                  ) : (
                    fieldMap.map((f, i) => {
                      const { bg, text } = relevanceColor(f.fraud_relevance);
                      return (
                        <tr key={i} className="border-b border-[#1E1E2E]/40 hover:bg-[#0A0A0F] transition-all">
                          <td className="py-2 pr-4 font-mono text-white">{f.column}</td>
                          <td className="py-2 pr-4">
                            <span
                              className="px-2 py-0.5 rounded font-medium capitalize"
                              style={{ backgroundColor: `${bg}15`, color: text }}
                            >
                              {f.fraud_relevance}
                            </span>
                          </td>
                          <td className="py-2 pr-4 text-gray-400 max-w-[200px]">
                            {f.values
                              ? f.values.join(", ")
                              : f.range || "—"}
                          </td>
                          <td className="py-2 pr-4 text-gray-500">{f.notes}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
