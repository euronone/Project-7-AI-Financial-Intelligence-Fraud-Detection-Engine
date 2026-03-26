"use client";

import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, RefreshCw, Brain,
  CheckCircle2, XCircle, Clock, Table2, List,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

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
  user: { avatar_initials: string; full_name: string; email: string; plan: string };
  clearAuth: () => void;
  router: ReturnType<typeof useRouter>;
}) {
  const planColor = plan === "advanced" ? "#8B5CF6" : plan === "pro" ? "#3B82F6" : "#00FF87";
  const navItems = [
    { icon: Activity,      label: "Dashboard",    href: "/dashboard",             active: false },
    { icon: TrendingUp,    label: "Transactions",  href: "/dashboard/transactions", active: false },
    { icon: AlertTriangle, label: "Fraud Alerts",  href: "/dashboard/alerts",       active: false },
    { icon: FlaskConical,  label: "Test Me",       href: "/dashboard/test-me",      active: false },
    { icon: Users,         label: "Customers",     href: "/dashboard/customers",    active: false },
    { icon: Database,      label: "Data Sources",  href: "/dashboard/data-sources", active: true  },
    { icon: Brain,         label: "ML Details",    href: "/dashboard/ml-details",   active: false },
    { icon: Settings,      label: "Settings",      href: "/dashboard/settings",     active: false },
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
        {navItems.map(({ icon: Icon, label, href, active }) => (
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
      setSource(src as SourceInfo);
      setSchema((sch as { columns: SchemaColumn[] }).columns || []);
      setFieldMap((fm as { fields: FieldMapEntry[] }).fields || []);
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
