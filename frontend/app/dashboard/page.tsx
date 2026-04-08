"use client";

import { useAuthStore, isAdmin } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { Shield, LogOut, Loader2, Database, Settings, AlertTriangle,
         TrendingUp, Activity, Users, FlaskConical, RefreshCw, Brain, Table } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

const DB_ICONS: Record<string, string> = {
  supabase: "⚡",
  postgresql: "🐘",
  mysql: "🐬",
  mongodb: "🍃",
  rest_api: "🔌",
};

interface Overview {
  transactions_today: number;
  total_transactions: number;
  fraud_count: number;
  fraud_rate_percent: number;
  open_alerts: number;
  critical_alerts: number;
}

interface RecentTxn {
  id: string;
  amount: number;
  currency: string;
  merchant_name: string | null;
  channel: string;
  fraud_score: number | null;
  fraud_category: string;
  fraud_risk_level: string | null;
  transaction_timestamp: string;
  is_flagged: boolean;
  is_blocked: boolean;
}

const RISK_COLORS: Record<string, string> = {
  legitimate: "#00FF87",
  suspicious:  "#F59E0B",
  fraudulent:  "#EF4444",
  unscored:    "#6B7280",
};

const RISK_BG: Record<string, string> = {
  legitimate: "#00FF8715",
  suspicious:  "#F59E0B15",
  fraudulent:  "#EF444415",
  unscored:    "#6B728015",
};

export default function DashboardPage() {
  const { user, token, isAuthenticated, hasCompletedOnboarding, dbConfig, clearAuth } = useAuthStore();
  const router = useRouter();

  const [overview, setOverview] = useState<Overview | null>(null);
  const [recentTxns, setRecentTxns] = useState<RecentTxn[]>([]);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); return; }
    if (!hasCompletedOnboarding) { router.replace("/onboarding"); }
  }, [isAuthenticated, hasCompletedOnboarding, router]);

  const fetchData = useCallback(async () => {
    if (!token) return;
    setLoadingOverview(true);
    try {
      const [ov, txns] = await Promise.all([
        apiClient.getOverview(token),
        apiClient.getTransactions(token, { per_page: "10", is_test: "false" }),
      ]);
      setOverview(ov);
      setRecentTxns((txns.items as RecentTxn[]).slice(0, 10));
      setLastRefresh(new Date());
    } catch {
      // Backend may not be running — leave placeholders
    } finally {
      setLoadingOverview(false);
    }
  }, [token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (!user) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
        <Loader2 className="animate-spin text-[#00FF87]" size={32} />
      </div>
    );
  }

  const planColor =
    user.plan === "advanced" ? "#8B5CF6" : user.plan === "pro" ? "#3B82F6" : "#00FF87";

  const kpiCards = [
    {
      label: "Transactions Today",
      value: loadingOverview ? "…" : (overview?.transactions_today?.toLocaleString() ?? "—"),
      sub: overview ? "Live count" : "Connecting…",
      color: "#00FF87",
    },
    {
      label: "Fraud Rate",
      value: loadingOverview ? "…" : (overview ? `${overview.fraud_rate_percent}%` : "—"),
      sub: overview ? `${overview.fraud_count.toLocaleString()} flagged total` : "No data yet",
      color: "#EF4444",
    },
    {
      label: "Open Alerts",
      value: loadingOverview ? "…" : (overview?.open_alerts?.toLocaleString() ?? "—"),
      sub: overview ? `${overview.critical_alerts} critical` : "No alerts",
      color: "#F59E0B",
    },
    {
      label: "Total Transactions",
      value: loadingOverview ? "…" : (overview?.total_transactions?.toLocaleString() ?? "—"),
      sub: overview ? "All time" : "No baseline",
      color: "#3B82F6",
    },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      {/* Sidebar */}
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
            { icon: Activity,       label: "Dashboard",    href: "/dashboard",              active: true,  adminOnly: false },
            { icon: TrendingUp,     label: "Transactions", href: "/dashboard/transactions",  active: false, adminOnly: false },
            { icon: AlertTriangle,  label: "Fraud Alerts", href: "/dashboard/alerts",        active: false, adminOnly: false },
            // Test Me is ADMIN-ONLY — hidden for analyst/viewer roles
            { icon: FlaskConical,   label: "Test Me",      href: "/dashboard/test-me",       active: false, adminOnly: true  },
            { icon: Users,          label: "Customers",    href: "/dashboard/customers",     active: false, adminOnly: false },
            { icon: Database,       label: "Data Sources", href: "/dashboard/data-sources",  active: false, adminOnly: false },
            { icon: Table,          label: "Data Schema",  href: "/dashboard/data-schema",   active: false, adminOnly: false },
            { icon: Brain,          label: "ML Training",  href: "/dashboard/ml-training",   active: false, adminOnly: false },
            { icon: Settings,       label: "Settings",     href: "/dashboard/settings",      active: false, adminOnly: false },
          ]
            .filter(({ adminOnly }) => !adminOnly || isAdmin(user))
            .map(({ icon: Icon, label, href, active }) => (
            <Link
              key={label}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20"
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#111118]"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-[#1E1E2E]">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black"
              style={{ backgroundColor: `${planColor}20`, color: planColor }}
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
      </aside>

      {/* Main content */}
      <main className="ml-60 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Welcome back, {user.full_name.split(" ")[0]}!</h1>
            <p className="text-gray-500 text-sm mt-1">
              {user.institution_name} · <span className="capitalize">{user.institution_type}</span>
            </p>
          </div>
          <div className="flex items-center gap-3 mt-1">
            <button
              onClick={fetchData}
              className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
            >
              <RefreshCw size={12} /> Refresh
            </button>
            <span
              className="text-xs font-mono px-3 py-1.5 rounded-full capitalize"
              style={{
                color: planColor,
                backgroundColor: `${planColor}15`,
                border: `1px solid ${planColor}40`,
              }}
            >
              {user.plan} plan
            </span>
          </div>
        </div>

        {/* DB Connection Status */}
        {dbConfig && (
          <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4 mb-6 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-[#00FF87]/10 border border-[#00FF87]/20 flex items-center justify-center text-lg">
              {DB_ICONS[dbConfig.db_type] || "🗄️"}
            </div>
            <div>
              <div className="text-sm font-semibold">{dbConfig.label || dbConfig.db_type}</div>
              <div className="text-xs text-gray-500">
                {dbConfig.db_url
                  ? dbConfig.db_url.replace(/:[^:@]+@/, ":***@").slice(0, 60) + "…"
                  : dbConfig.supabase_url || "Connected"}
              </div>
            </div>
            <div className="ml-auto flex items-center gap-2 text-xs text-[#00FF87]">
              <div className="w-2 h-2 rounded-full bg-[#00FF87] animate-pulse" />
              Connected
            </div>
            <Link
              href="/dashboard/settings"
              className="text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
            >
              Edit
            </Link>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
          {kpiCards.map(({ label, value, sub, color }) => (
            <div key={label} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
              {loadingOverview ? (
                <div className="h-8 w-20 bg-[#1E1E2E] rounded animate-pulse mb-2" />
              ) : (
                <div className="text-3xl font-black mb-1" style={{ color }}>{value}</div>
              )}
              <div className="text-sm text-gray-300 font-medium">{label}</div>
              <div className="text-xs text-gray-600 mt-0.5">{sub}</div>
            </div>
          ))}
        </div>

        {/* Recent Transactions + Quick Links */}
        <div className="grid grid-cols-3 gap-6">
          {/* Recent Transactions (2/3 width) */}
          <div className="col-span-2 bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm">Recent Transactions</h3>
              <Link
                href="/dashboard/transactions"
                className="text-xs text-[#00FF87] hover:underline"
              >
                View all →
              </Link>
            </div>

            {recentTxns.length === 0 ? (
              <div className="h-40 flex items-center justify-center text-xs text-gray-600">
                {loadingOverview ? (
                  <Loader2 size={20} className="animate-spin text-gray-600" />
                ) : (
                  "No transactions yet — submit one via Test Me"
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {recentTxns.map((txn) => {
                  const cat = txn.fraud_category || "unscored";
                  const col = RISK_COLORS[cat] || "#6B7280";
                  const bg  = RISK_BG[cat]    || "#6B728015";
                  return (
                    <div
                      key={txn.id}
                      className="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-[#0A0A0F] transition-all"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                          style={{ color: col, backgroundColor: bg }}
                        >
                          {cat === "fraudulent" ? "!" : cat === "suspicious" ? "?" : "✓"}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-medium truncate">
                            {txn.merchant_name || "Unknown Merchant"}
                          </div>
                          <div className="text-xs text-gray-600 truncate">
                            {txn.channel} · {new Date(txn.transaction_timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-sm font-semibold">
                          ₹{Number(txn.amount).toLocaleString()}
                        </span>
                        <span
                          className="text-xs px-2 py-0.5 rounded-full font-medium capitalize"
                          style={{ color: col, backgroundColor: bg }}
                        >
                          {cat}
                        </span>
                        {txn.fraud_score != null && (
                          <span className="text-xs text-gray-500 font-mono w-10 text-right">
                            {(txn.fraud_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick Actions (1/3 width) */}
          <div className="space-y-4">
            <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
              <h3 className="font-semibold text-sm mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <Link
                  href="/dashboard/test-me"
                  className="flex items-center gap-2.5 w-full text-xs text-white bg-[#00FF87]/10 border border-[#00FF87]/30 hover:border-[#00FF87]/60 px-3 py-2.5 rounded-xl transition-all"
                >
                  <FlaskConical size={13} className="text-[#00FF87]" />
                  Test Transaction
                </Link>
                <Link
                  href="/dashboard/alerts"
                  className="flex items-center gap-2.5 w-full text-xs text-white bg-[#F59E0B]/10 border border-[#F59E0B]/30 hover:border-[#F59E0B]/60 px-3 py-2.5 rounded-xl transition-all"
                >
                  <AlertTriangle size={13} className="text-[#F59E0B]" />
                  Review Alerts
                  {overview && overview.open_alerts > 0 && (
                    <span className="ml-auto bg-[#F59E0B] text-black text-xs font-bold px-1.5 py-0.5 rounded-full">
                      {overview.open_alerts}
                    </span>
                  )}
                </Link>
                <Link
                  href="/dashboard/transactions"
                  className="flex items-center gap-2.5 w-full text-xs text-white bg-[#3B82F6]/10 border border-[#3B82F6]/30 hover:border-[#3B82F6]/60 px-3 py-2.5 rounded-xl transition-all"
                >
                  <TrendingUp size={13} className="text-[#3B82F6]" />
                  All Transactions
                </Link>
              </div>
            </div>

            {/* Last refresh */}
            <div className="text-xs text-gray-600 text-center">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
