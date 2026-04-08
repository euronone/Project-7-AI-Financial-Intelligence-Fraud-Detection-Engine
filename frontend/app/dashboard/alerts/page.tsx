"use client";

import { useAuthStore, isAdmin } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, RefreshCw,
  CheckCircle2, XCircle, Eye, Brain, Table,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

interface Alert {
  id: string;
  transaction_id: string;
  customer_id: string | null;
  alert_type: string;
  severity: string;
  status: string;
  is_confirmed: boolean;
  resolution_notes: string | null;
  created_at: string;
  resolved_at: string | null;
}

const SEV_COLOR: Record<string, string> = {
  critical: "#EF4444",
  high:     "#F97316",
  medium:   "#F59E0B",
  low:      "#22C55E",
};

const SEV_BG: Record<string, string> = {
  critical: "#EF444418",
  high:     "#F9731618",
  medium:   "#F59E0B18",
  low:      "#22C55E18",
};

const STATUS_LABEL: Record<string, string> = {
  open:            "Open",
  under_review:    "Under Review",
  confirmed_fraud: "Confirmed Fraud",
  false_positive:  "False Positive",
  closed:          "Closed",
};

export default function AlertsPage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("open");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  const fetchAlerts = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params: Record<string, string> = { per_page: "50" };
      if (filterStatus !== "all") params.status = filterStatus;
      if (filterSeverity !== "all") params.severity = filterSeverity;

      const data = await apiClient.getAlerts(token, params);
      setAlerts(data.items as Alert[]);
      setTotal(data.total);
    } catch {
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [token, filterStatus, filterSeverity]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  async function updateAlertStatus(alertId: string, status: string, notes?: string) {
    if (!token) return;
    setActionLoading(alertId);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003/api/v1"}/alerts/${alertId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status, resolution_notes: notes }),
        }
      );
      await fetchAlerts();
    } catch {
      // Ignore
    } finally {
      setActionLoading(null);
    }
  }

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  const planColor =
    user.plan === "advanced" ? "#8B5CF6" : user.plan === "pro" ? "#3B82F6" : "#00FF87";

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-60 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col z-10">
        <div className="p-5 border-b border-[#1E1E2E]">
          <div className="flex items-center gap-2.5">
            <Shield size={22} className="text-[#00FF87]" />
            <span className="font-black text-base">Fin<span className="text-[#00FF87]">Shield</span> AI</span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {[
            { icon: Activity,       label: "Dashboard",    href: "/dashboard",             active: false, adminOnly: false },
            { icon: TrendingUp,     label: "Transactions", href: "/dashboard/transactions", active: false, adminOnly: false },
            { icon: AlertTriangle,  label: "Fraud Alerts", href: "/dashboard/alerts",       active: true,  adminOnly: false },
            { icon: FlaskConical,   label: "Test Me",      href: "/dashboard/test-me",      active: false, adminOnly: true  },
            { icon: Users,          label: "Customers",    href: "/dashboard/customers",    active: false, adminOnly: false },
            { icon: Database,       label: "Data Sources", href: "/dashboard/data-sources", active: false, adminOnly: false },
            { icon: Table,          label: "Data Schema",  href: "/dashboard/data-schema",  active: false, adminOnly: false },
            { icon: Brain,          label: "ML Training",  href: "/dashboard/ml-training",  active: false, adminOnly: false },
            { icon: Settings,       label: "Settings",     href: "/dashboard/settings",     active: false, adminOnly: false },
          ]
            .filter(({ adminOnly }) => !adminOnly || isAdmin(user))
            .map(({ icon: Icon, label, href, active }) => (
            <Link key={label} href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20"
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#111118]"
              }`}
            >
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

      {/* Main */}
      <main className="ml-60 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Fraud Alerts</h1>
            <p className="text-gray-500 text-sm mt-1">{total} alerts matching filter</p>
          </div>
          <button onClick={fetchAlerts}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all">
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-[#111118] border border-[#1E1E2E] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-[#00FF87]/40"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="under_review">Under Review</option>
            <option value="confirmed_fraud">Confirmed Fraud</option>
            <option value="false_positive">False Positive</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-[#111118] border border-[#1E1E2E] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-[#00FF87]/40"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Alert Cards */}
        {loading ? (
          <div className="flex justify-center py-24">
            <Loader2 size={32} className="animate-spin text-gray-600" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-16 text-center">
            <CheckCircle2 size={40} className="text-[#00FF87] mx-auto mb-3" />
            <div className="text-gray-300 font-semibold">No alerts found</div>
            <div className="text-gray-600 text-sm mt-1">
              {filterStatus === "open"
                ? "Great — your inbox is clear!"
                : "No alerts match the selected filters."}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => {
              const sev = alert.severity;
              const col = SEV_COLOR[sev] || "#6B7280";
              const bg  = SEV_BG[sev]  || "#6B728018";
              const isExpanded = expandedId === alert.id;
              const isPending = actionLoading === alert.id;

              return (
                <div
                  key={alert.id}
                  className="bg-[#111118] border border-[#1E1E2E] rounded-2xl overflow-hidden"
                >
                  {/* Main row */}
                  <div className="flex items-center gap-4 px-5 py-4">
                    {/* Severity dot */}
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black shrink-0"
                      style={{ color: col, backgroundColor: bg }}
                    >
                      {sev === "critical" ? "!!" : sev === "high" ? "!" : "?"}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className="text-xs font-bold uppercase px-2 py-0.5 rounded-full"
                          style={{ color: col, backgroundColor: bg }}
                        >
                          {sev}
                        </span>
                        <span className="text-xs text-gray-500 capitalize">{alert.alert_type.replace("_", " ")}</span>
                        <span className="text-xs text-gray-600 font-mono">{alert.id.slice(0, 12)}…</span>
                      </div>
                      <div className="text-sm font-medium mt-0.5 truncate">
                        Transaction: <span className="font-mono text-gray-400">{alert.transaction_id.slice(0, 16)}…</span>
                      </div>
                      <div className="text-xs text-gray-600">
                        {new Date(alert.created_at).toLocaleString()} ·{" "}
                        <span className="capitalize">{STATUS_LABEL[alert.status] || alert.status}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      {alert.status === "open" || alert.status === "under_review" ? (
                        <>
                          <button
                            onClick={() => updateAlertStatus(alert.id, "confirmed_fraud", "Confirmed via dashboard")}
                            disabled={isPending}
                            className="flex items-center gap-1.5 text-xs text-[#EF4444] border border-[#EF4444]/30 hover:border-[#EF4444]/60 px-3 py-1.5 rounded-lg transition-all disabled:opacity-40"
                          >
                            {isPending ? <Loader2 size={12} className="animate-spin" /> : <XCircle size={13} />}
                            Confirm Fraud
                          </button>
                          <button
                            onClick={() => updateAlertStatus(alert.id, "false_positive", "Marked false positive via dashboard")}
                            disabled={isPending}
                            className="flex items-center gap-1.5 text-xs text-[#00FF87] border border-[#00FF87]/30 hover:border-[#00FF87]/60 px-3 py-1.5 rounded-lg transition-all disabled:opacity-40"
                          >
                            <CheckCircle2 size={13} />
                            False Positive
                          </button>
                        </>
                      ) : (
                        <span className="text-xs text-gray-600">
                          {STATUS_LABEL[alert.status]}
                        </span>
                      )}
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : alert.id)}
                        className="flex items-center gap-1 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-2 py-1.5 rounded-lg transition-all"
                      >
                        <Eye size={13} />
                      </button>
                    </div>
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="border-t border-[#1E1E2E] px-5 py-4 bg-[#0D0D15]">
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div>
                          <div className="text-gray-500 mb-1">Alert ID</div>
                          <div className="font-mono text-gray-300">{alert.id}</div>
                        </div>
                        <div>
                          <div className="text-gray-500 mb-1">Transaction ID</div>
                          <div className="font-mono text-gray-300">{alert.transaction_id}</div>
                        </div>
                        <div>
                          <div className="text-gray-500 mb-1">Customer ID</div>
                          <div className="font-mono text-gray-300">{alert.customer_id || "—"}</div>
                        </div>
                        {alert.resolution_notes && (
                          <div className="col-span-3">
                            <div className="text-gray-500 mb-1">Resolution Notes</div>
                            <div className="text-gray-300">{alert.resolution_notes}</div>
                          </div>
                        )}
                        {alert.resolved_at && (
                          <div>
                            <div className="text-gray-500 mb-1">Resolved At</div>
                            <div className="text-gray-300">{new Date(alert.resolved_at).toLocaleString()}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
