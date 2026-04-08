"use client";

import { useAuthStore, isAdmin, type AuthUser } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, RefreshCw, Brain,
  UserCheck, UserX, AlertCircle, TrendingDown, Table,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

// ── Types (matching actual backend response shapes) ─────────────────────────
interface Stats {
  total_customers: number;
  fraud_customers: number;    // backend returns "fraud_customers" not "fraud_count"
  high_risk_customers: number; // backend returns "high_risk_customers"
  avg_risk_score: number;
}
// backend: { distribution: [{ band, min, max, count, color }] }
interface RiskBand { band: string; count: number; color: string; }
// backend: { breakdown: [{ tier, total, fraud, legitimate }] }
interface TierEntry { tier: string; fraud: number; legitimate: number; }
// backend: { period_days, activity: [{ date, total, fraud }] }
interface ActivityRow { date: string; total: number; fraud: number; }
interface Customer {
  customer_id: string;
  full_name: string;
  email: string;
  phone_number?: string;
  city: string;
  risk_score: number;
  account_type: string;
  kyc_status: string;
  fraud_flags: number;
  transaction_count: number;
  primary_payment_type?: string | null;
  primary_payment_label?: string | null;
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
    { icon: Users,         label: "Customers",     href: "/dashboard/customers",    active: true,  adminOnly: false },
    { icon: Database,      label: "Data Sources",  href: "/dashboard/data-sources", active: false, adminOnly: false },
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

// ── Risk color helpers ───────────────────────────────────────────────────────
function riskColor(score: number) {
  if (score >= 0.7) return "#EF4444";
  if (score >= 0.4) return "#F59E0B";
  return "#00FF87";
}

function riskLabel(score: number) {
  if (score >= 0.7) return "HIGH";
  if (score >= 0.4) return "MEDIUM";
  return "LOW";
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function CustomersPage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();

  const [stats, setStats] = useState<Stats | null>(null);
  const [riskDist, setRiskDist] = useState<RiskBand[]>([]);
  const [fraudLegit, setFraudLegit] = useState<TierEntry[]>([]);
  const [activityRows, setActivityRows] = useState<ActivityRow[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [minRisk, setMinRisk] = useState("");
  const [accountType, setAccountType] = useState("");
  const [kycStatus, setKycStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  const fetchSummary = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [st, rd, fl, ac] = await Promise.all([
        apiClient.getCustomerStats(token),
        apiClient.getCustomerRiskDist(token),
        apiClient.getCustomerFraudLegit(token),
        apiClient.getCustomerActivity(token, 14),
      ]);
      setStats(st as Stats);
      // backend: { distribution: [...] }
      setRiskDist(((rd as { distribution?: RiskBand[] }).distribution) || []);
      // backend: { breakdown: [...] }
      setFraudLegit(((fl as { breakdown?: TierEntry[] }).breakdown) || []);
      // backend: { activity: [{ date, total, fraud }] }
      setActivityRows(((ac as { activity?: ActivityRow[] }).activity) || []);
    } catch { /* backend may be down */ }
    finally { setLoading(false); }
  }, [token]);

  const fetchTable = useCallback(async () => {
    if (!token) return;
    setTableLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(page),
        per_page: String(pageSize),
      };
      if (search) params.search = search;
      if (minRisk) params.min_risk = minRisk;
      if (accountType) params.account_type = accountType;
      if (kycStatus) params.kyc_status = kycStatus;
      const res = await apiClient.getTopRiskyCustomers(token, params);
      setCustomers((res.items as Customer[]) || []);
      setTotalCustomers(res.total || 0);
    } catch { setCustomers([]); }
    finally { setTableLoading(false); }
  }, [token, page, search, minRisk, accountType, kycStatus]);

  useEffect(() => { fetchSummary(); }, [fetchSummary]);
  useEffect(() => { fetchTable(); }, [fetchTable]);

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  const maxActivity = activityRows.length > 0 ? Math.max(...activityRows.map(r => r.total), 1) : 1;
  const maxRisk = riskDist.reduce((m, b) => Math.max(m, b.count), 1);
  const totalPages = Math.ceil(totalCustomers / pageSize);

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <Sidebar plan={user.plan} user={user} clearAuth={clearAuth} router={router} />

      <main className="ml-60 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Customers</h1>
            <p className="text-gray-500 text-sm mt-1">Risk profiles, fraud patterns, and KYC status</p>
          </div>
          <button
            onClick={() => { fetchSummary(); fetchTable(); }}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 animate-pulse">
                <div className="h-8 w-20 bg-[#1E1E2E] rounded mb-2" />
                <div className="h-4 w-24 bg-[#1E1E2E] rounded" />
              </div>
            ))
          ) : (
            [
              { icon: Users, label: "Total Customers", value: stats?.total_customers?.toLocaleString() ?? "—", color: "#3B82F6" },
              { icon: UserX, label: "Fraud Involved", value: stats?.fraud_customers?.toLocaleString() ?? "—", color: "#EF4444" },
              { icon: AlertCircle, label: "High Risk", value: stats?.high_risk_customers?.toLocaleString() ?? "—", color: "#F59E0B" },
              { icon: TrendingDown, label: "Avg Risk Score", value: stats ? (stats.avg_risk_score * 100).toFixed(1) + "%" : "—", color: "#8B5CF6" },
            ].map(({ icon: Icon, label, value, color }) => (
              <div key={label} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
                <div className="flex items-center justify-between mb-2">
                  <Icon size={18} style={{ color }} />
                </div>
                <div className="text-3xl font-black mb-1" style={{ color }}>{value}</div>
                <div className="text-sm text-gray-400 font-medium">{label}</div>
              </div>
            ))
          )}
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          {/* Risk Distribution Bar Chart */}
          <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
            <h3 className="text-sm font-semibold mb-4">Risk Distribution</h3>
            {loading ? (
              <div className="h-32 bg-[#0A0A0F] rounded-xl animate-pulse" />
            ) : riskDist.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-xs text-gray-600">No data</div>
            ) : (
              <div className="space-y-3">
                {riskDist.map((band) => (
                  <div key={band.band}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-400 capitalize">{band.band}</span>
                      <span className="text-gray-300 font-mono">{band.count}</span>
                    </div>
                    <div className="w-full bg-[#0A0A0F] rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.round((band.count / maxRisk) * 100)}%`,
                          backgroundColor: band.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Fraud vs Legit by Tier */}
          <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
            <h3 className="text-sm font-semibold mb-4">Fraud vs Legit by Tier</h3>
            {loading ? (
              <div className="h-32 bg-[#0A0A0F] rounded-xl animate-pulse" />
            ) : fraudLegit.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-xs text-gray-600">No data</div>
            ) : (
              <div className="space-y-3">
                {fraudLegit.map((t) => {
                  const total = t.fraud + t.legitimate || 1;
                  const fraudPct = (t.fraud / total) * 100;
                  return (
                    <div key={t.tier}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400 capitalize">{t.tier}</span>
                        <span className="text-[#EF4444] font-mono">{t.fraud} fraud</span>
                      </div>
                      <div className="w-full bg-[#00FF87]/20 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-[#EF4444] transition-all duration-500"
                          style={{ width: `${fraudPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Activity Sparkline */}
          <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
            <h3 className="text-sm font-semibold mb-4">Transaction Activity (14d)</h3>
            {loading ? (
              <div className="h-32 bg-[#0A0A0F] rounded-xl animate-pulse" />
            ) : activityRows.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-xs text-gray-600">No data yet</div>
            ) : (
              <>
                <div className="flex items-end gap-1 h-28">
                  {activityRows.map((row, i) => {
                    const height = maxActivity > 0 ? Math.max(4, (row.total / maxActivity) * 100) : 4;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div
                          className="w-full rounded-sm transition-all duration-300 hover:opacity-80"
                          style={{ height: `${height}%`, backgroundColor: "#3B82F6", minHeight: "4px" }}
                        />
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#1E1E2E] text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                          {row.total} ({row.fraud} fraud)
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-xs text-gray-600 mt-1">
                  <span>{activityRows[0]?.date}</span>
                  <span>{activityRows[activityRows.length - 1]?.date}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Table: Top Risky Customers */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Top Risky Customers</h3>
            <div className="flex items-center gap-2">
              <input
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                placeholder="Search name / email…"
                className="bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none w-44"
              />
              <select
                value={accountType}
                onChange={(e) => { setAccountType(e.target.value); setPage(1); }}
                className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="">All Types</option>
                <option value="personal">Personal</option>
                <option value="business">Business</option>
                <option value="merchant">Merchant</option>
              </select>
              <select
                value={kycStatus}
                onChange={(e) => { setKycStatus(e.target.value); setPage(1); }}
                className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="">All KYC</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
                <option value="rejected">Rejected</option>
              </select>
              <select
                value={minRisk}
                onChange={(e) => { setMinRisk(e.target.value); setPage(1); }}
                className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="">Min Risk</option>
                <option value="0.3">30%+</option>
                <option value="0.5">50%+</option>
                <option value="0.7">70%+</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#1E1E2E]">
                  {["Name", "Email", "City", "Payment Method", "Type", "KYC", "Risk Score", "Fraud Flags", "Transactions"].map(h => (
                    <th key={h} className="text-left text-gray-500 font-medium pb-2 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 9 }).map((__, j) => (
                        <td key={j} className="py-3 pr-4">
                          <div className="h-3 bg-[#1E1E2E] rounded animate-pulse" style={{ width: `${40 + j * 10}%` }} />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-gray-600">
                      <UserCheck size={32} className="mx-auto mb-2 text-gray-700" />
                      No customers found
                    </td>
                  </tr>
                ) : (
                  customers.map((c) => {
                    const rc = riskColor(c.risk_score);
                    const rl = riskLabel(c.risk_score);
                    return (
                      <tr key={c.customer_id} className="border-b border-[#1E1E2E]/50 hover:bg-[#0A0A0F] transition-all">
                        <td className="py-3 pr-4 font-medium text-white">{c.full_name || "—"}</td>
                        <td className="py-3 pr-4 text-gray-400 font-mono text-xs">{c.email}</td>
                        <td className="py-3 pr-4 text-gray-400">{c.city || "—"}</td>
                        {/* Payment Method column */}
                        <td className="py-3 pr-4">
                          {c.primary_payment_type ? (
                            <div className="flex flex-col gap-0.5">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full w-fit ${
                                c.primary_payment_type === "upi"
                                  ? "bg-[#00FF87]/10 text-[#00FF87]"
                                  : c.primary_payment_type === "credit_card"
                                  ? "bg-[#8B5CF6]/10 text-[#8B5CF6]"
                                  : "bg-[#3B82F6]/10 text-[#3B82F6]"
                              }`}>
                                {c.primary_payment_type === "upi" ? "UPI" : c.primary_payment_type === "credit_card" ? "Credit Card" : "Debit Card"}
                              </span>
                              {c.primary_payment_label && (
                                <span className="text-[9px] text-gray-500 font-mono truncate max-w-[120px]" title={c.primary_payment_label}>
                                  {c.primary_payment_label}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-600 text-xs">—</span>
                          )}
                        </td>
                        <td className="py-3 pr-4">
                          <span className="capitalize bg-[#3B82F6]/10 text-[#3B82F6] px-2 py-0.5 rounded-full text-xs">
                            {c.account_type}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`capitalize px-2 py-0.5 rounded-full ${
                            c.kyc_status === "verified"
                              ? "bg-[#00FF87]/10 text-[#00FF87]"
                              : c.kyc_status === "rejected"
                              ? "bg-[#EF4444]/10 text-[#EF4444]"
                              : "bg-[#F59E0B]/10 text-[#F59E0B]"
                          }`}>
                            {c.kyc_status}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-[#0A0A0F] rounded-full h-1.5 overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{ width: `${c.risk_score * 100}%`, backgroundColor: rc }}
                              />
                            </div>
                            <span className="font-mono" style={{ color: rc }}>
                              {(c.risk_score * 100).toFixed(0)}%
                            </span>
                            <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ color: rc, backgroundColor: `${rc}15` }}>
                              {rl}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          <span className={c.fraud_flags > 0 ? "text-[#EF4444] font-bold" : "text-gray-500"}>
                            {c.fraud_flags}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-gray-400">{c.transaction_count}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <span className="text-xs text-gray-500">
                {totalCustomers} total · page {page} of {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="text-xs border border-[#1E1E2E] px-3 py-1.5 rounded-lg text-gray-400 hover:text-white disabled:opacity-40 transition-all"
                >
                  ← Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="text-xs border border-[#1E1E2E] px-3 py-1.5 rounded-lg text-gray-400 hover:text-white disabled:opacity-40 transition-all"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
