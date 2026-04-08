"use client";

import { useAuthStore, isAdmin } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Search, RefreshCw, Loader2,
  ChevronLeft, ChevronRight, Brain, Table,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

interface Transaction {
  id: string;
  amount: number;
  currency: string;
  merchant_name: string | null;
  channel: string;
  transaction_type: string;
  fraud_score: number | null;
  fraud_category: string;
  fraud_risk_level: string | null;
  is_flagged: boolean;
  is_blocked: boolean;
  is_test: boolean;
  status: string;
  transaction_timestamp: string;
  customer_id: string | null;
  triggered_rule_ids: string[] | null;
}

const CATEGORY_COLOR: Record<string, string> = {
  legitimate: "#00FF87",
  suspicious:  "#F59E0B",
  fraudulent:  "#EF4444",
  unscored:    "#6B7280",
};

const CATEGORY_BG: Record<string, string> = {
  legitimate: "#00FF8718",
  suspicious:  "#F59E0B18",
  fraudulent:  "#EF444418",
  unscored:    "#6B728018",
};

export default function TransactionsPage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [showTestOnly, setShowTestOnly] = useState<boolean | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  const fetchTransactions = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(page),
        per_page: String(perPage),
      };
      if (filterCategory !== "all") params.fraud_category = filterCategory;
      if (showTestOnly !== null) params.is_test = String(showTestOnly);

      const data = await apiClient.getTransactions(token, params);
      setTransactions(data.items as Transaction[]);
      setTotal(data.total);
    } catch {
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [token, page, perPage, filterCategory, showTestOnly]);

  useEffect(() => { fetchTransactions(); }, [fetchTransactions]);

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  const planColor =
    user.plan === "advanced" ? "#8B5CF6" : user.plan === "pro" ? "#3B82F6" : "#00FF87";

  const totalPages = Math.ceil(total / perPage);

  // Client-side filter by search term (merchant name or ID)
  const displayed = search.trim()
    ? transactions.filter(
        (t) =>
          t.merchant_name?.toLowerCase().includes(search.toLowerCase()) ||
          t.id.toLowerCase().includes(search.toLowerCase())
      )
    : transactions;

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
            { icon: TrendingUp,     label: "Transactions", href: "/dashboard/transactions", active: true,  adminOnly: false },
            { icon: AlertTriangle,  label: "Fraud Alerts", href: "/dashboard/alerts",       active: false, adminOnly: false },
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
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Transactions</h1>
            <p className="text-gray-500 text-sm mt-1">{total.toLocaleString()} total records</p>
          </div>
          <button onClick={fetchTransactions}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all">
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6">
          <div className="relative flex-1 max-w-sm">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search merchant or transaction ID…"
              className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/40"
            />
          </div>
          <select
            value={filterCategory}
            onChange={(e) => { setFilterCategory(e.target.value); setPage(1); }}
            className="bg-[#111118] border border-[#1E1E2E] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-[#00FF87]/40"
          >
            <option value="all">All Categories</option>
            <option value="fraudulent">Fraudulent</option>
            <option value="suspicious">Suspicious</option>
            <option value="legitimate">Legitimate</option>
            <option value="unscored">Unscored</option>
          </select>
          <select
            value={showTestOnly === null ? "all" : showTestOnly ? "test" : "live"}
            onChange={(e) => {
              const v = e.target.value;
              setShowTestOnly(v === "all" ? null : v === "test");
              setPage(1);
            }}
            className="bg-[#111118] border border-[#1E1E2E] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-[#00FF87]/40"
          >
            <option value="all">Live + Test</option>
            <option value="live">Live only</option>
            <option value="test">Test only</option>
          </select>
        </div>

        {/* Table */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1E1E2E] text-xs text-gray-500 uppercase tracking-wide">
                <th className="text-left px-5 py-3 font-medium">Merchant</th>
                <th className="text-left px-5 py-3 font-medium">Channel</th>
                <th className="text-right px-5 py-3 font-medium">Amount</th>
                <th className="text-center px-5 py-3 font-medium">Score</th>
                <th className="text-center px-5 py-3 font-medium">Category</th>
                <th className="text-center px-5 py-3 font-medium">Status</th>
                <th className="text-left px-5 py-3 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-gray-600">
                    <Loader2 size={24} className="animate-spin mx-auto" />
                  </td>
                </tr>
              ) : displayed.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-gray-600 text-sm">
                    No transactions found. Submit one via{" "}
                    <Link href="/dashboard/test-me" className="text-[#00FF87] hover:underline">
                      Test Me
                    </Link>
                    .
                  </td>
                </tr>
              ) : (
                displayed.map((txn) => {
                  const cat = txn.fraud_category || "unscored";
                  const col = CATEGORY_COLOR[cat] || "#6B7280";
                  const bg  = CATEGORY_BG[cat]   || "#6B728018";
                  return (
                    <tr key={txn.id} className="border-b border-[#1E1E2E]/50 hover:bg-[#0D0D15] transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="font-medium truncate max-w-[160px]">
                          {txn.merchant_name || <span className="text-gray-600">—</span>}
                        </div>
                        <div className="text-xs text-gray-600 font-mono">{txn.id.slice(0, 8)}…</div>
                        {txn.is_test && (
                          <span className="text-xs bg-[#8B5CF6]/20 text-[#8B5CF6] px-1.5 py-0.5 rounded-full">
                            test
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-gray-400 text-xs capitalize">{txn.channel}</td>
                      <td className="px-5 py-3.5 text-right font-semibold">
                        ₹{Number(txn.amount).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        {txn.fraud_score != null ? (
                          <span
                            className="font-mono text-xs font-bold"
                            style={{ color: col }}
                          >
                            {(txn.fraud_score * 100).toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-gray-600 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <span
                          className="text-xs px-2 py-0.5 rounded-full font-medium capitalize"
                          style={{ color: col, backgroundColor: bg }}
                        >
                          {cat}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        {txn.is_blocked ? (
                          <span className="text-xs text-[#EF4444] bg-[#EF444418] px-2 py-0.5 rounded-full">blocked</span>
                        ) : txn.is_flagged ? (
                          <span className="text-xs text-[#F59E0B] bg-[#F59E0B18] px-2 py-0.5 rounded-full">flagged</span>
                        ) : (
                          <span className="text-xs text-[#00FF87] bg-[#00FF8718] px-2 py-0.5 rounded-full capitalize">{txn.status}</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-gray-500">
                        {new Date(txn.transaction_timestamp).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#1E1E2E] hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span className="px-3 py-1.5 text-xs">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#1E1E2E] hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
