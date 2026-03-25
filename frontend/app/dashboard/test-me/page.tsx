"use client";

import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, Play, RefreshCw,
  CheckCircle2, XCircle, Info,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface TestForm {
  amount: string;
  currency: string;
  channel: string;
  transaction_type: string;
  merchant_name: string;
  merchant_category_code: string;
  country_code: string;
  device_type: string;
  city: string;
  customer_id: string;
}

interface ScoredTransaction {
  id: string;
  fraud_score: number | null;
  fraud_category: string;
  fraud_risk_level: string | null;
  is_flagged: boolean;
  is_blocked: boolean;
  status: string;
  triggered_rule_ids: string[] | null;
  shap_values: Record<string, number> | null;
  model_version: string | null;
  fraud_scored_at: string | null;
  amount: number;
  merchant_name: string | null;
  channel: string;
}

// ---------------------------------------------------------------------------
// Preset scenarios
// ---------------------------------------------------------------------------
const PRESETS: Record<string, Partial<TestForm>> = {
  normal: {
    amount: "1200",
    channel: "pos_physical",
    merchant_name: "Reliance Fresh",
    merchant_category_code: "5411",
    country_code: "IN",
    device_type: "pos_terminal",
    city: "Mumbai",
    transaction_type: "purchase",
  },
  velocity: {
    amount: "9500",
    channel: "online",
    merchant_name: "Amazon India",
    merchant_category_code: "5999",
    country_code: "IN",
    device_type: "mobile",
    city: "Delhi",
    transaction_type: "purchase",
  },
  foreign_large: {
    amount: "85000",
    channel: "online",
    merchant_name: "International Electronics",
    merchant_category_code: "5732",
    country_code: "US",
    device_type: "desktop",
    city: "New York",
    transaction_type: "purchase",
  },
  night_withdrawal: {
    amount: "45000",
    channel: "atm",
    merchant_name: "SBI ATM",
    merchant_category_code: "6011",
    country_code: "IN",
    device_type: "pos_terminal",
    city: "Mumbai",
    transaction_type: "withdrawal",
  },
  account_takeover: {
    amount: "120000",
    channel: "online",
    merchant_name: "Wire Transfer",
    merchant_category_code: "4829",
    country_code: "IN",
    device_type: "desktop",
    city: "Bangalore",
    transaction_type: "transfer",
  },
};

const PRESET_LABELS: Record<string, string> = {
  normal:          "Normal Purchase",
  velocity:        "Velocity Test",
  foreign_large:   "Foreign Large Txn",
  night_withdrawal: "Night Withdrawal",
  account_takeover: "Account Takeover",
};

const DECISION_COLOR: Record<string, string> = {
  PASS:  "#00FF87",
  FLAG:  "#F59E0B",
  ALERT: "#F97316",
  BLOCK: "#EF4444",
};

// ---------------------------------------------------------------------------
// Sidebar nav (reused across pages)
// ---------------------------------------------------------------------------
function Sidebar({ plan, user, clearAuth, router }: {
  plan: string;
  user: { avatar_initials: string; full_name: string; email: string; plan: string };
  clearAuth: () => void;
  router: ReturnType<typeof useRouter>;
}) {
  const planColor = plan === "advanced" ? "#8B5CF6" : plan === "pro" ? "#3B82F6" : "#00FF87";
  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col z-10">
      <div className="p-5 border-b border-[#1E1E2E]">
        <div className="flex items-center gap-2.5">
          <Shield size={22} className="text-[#00FF87]" />
          <span className="font-black text-base">Fin<span className="text-[#00FF87]">Shield</span> AI</span>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {[
          { icon: Activity,       label: "Dashboard",    href: "/dashboard",              active: false },
          { icon: TrendingUp,     label: "Transactions", href: "/dashboard/transactions",  active: false },
          { icon: AlertTriangle,  label: "Fraud Alerts", href: "/dashboard/alerts",        active: false },
          { icon: FlaskConical,   label: "Test Me",      href: "/dashboard/test-me",       active: true  },
          { icon: Users,          label: "Customers",    href: "/dashboard/customers",     active: false },
          { icon: Database,       label: "Data Sources", href: "/dashboard/data-sources",  active: false },
          { icon: Settings,       label: "Settings",     href: "/dashboard/settings",      active: false },
        ].map(({ icon: Icon, label, href, active }) => (
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
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
const BLANK_FORM: TestForm = {
  amount: "",
  currency: "INR",
  channel: "online",
  transaction_type: "purchase",
  merchant_name: "",
  merchant_category_code: "5999",
  country_code: "IN",
  device_type: "mobile",
  city: "Mumbai",
  customer_id: "",
};

export default function TestMePage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  const [form, setForm] = useState<TestForm>(BLANK_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScoredTransaction | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  function applyPreset(key: string) {
    setForm((f) => ({ ...f, ...PRESETS[key] }));
    setResult(null);
    setError(null);
  }

  function resetForm() {
    setForm(BLANK_FORM);
    setResult(null);
    setError(null);
  }

  async function runTest() {
    if (!token || !form.amount) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        amount: parseFloat(form.amount),
        currency: form.currency,
        channel: form.channel,
        transaction_type: form.transaction_type,
        merchant_name: form.merchant_name || null,
        merchant_category_code: form.merchant_category_code || null,
        country_code: form.country_code || null,
        device_type: form.device_type || null,
        city: form.city || null,
        customer_id: form.customer_id || null,
        is_test: true,
      };
      const txn = await apiClient.createTransaction(payload, token);
      setResult(txn as ScoredTransaction);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to run test transaction");
    } finally {
      setLoading(false);
    }
  }

  // Derive decision from result
  const decision = result
    ? result.fraud_score == null
      ? "UNSCORED"
      : result.fraud_score >= 0.80
        ? "BLOCK"
        : result.fraud_score >= 0.60
          ? "ALERT"
          : result.fraud_score >= 0.30
            ? "FLAG"
            : "PASS"
    : null;

  const decisionColor = decision ? (DECISION_COLOR[decision] || "#6B7280") : "#6B7280";

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <Sidebar plan={user.plan} user={user} clearAuth={clearAuth} router={router} />

      <main className="ml-60 p-8">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">Test Me</h1>
            <p className="text-gray-500 text-sm mt-1">
              Submit a test transaction through the full ML fraud detection pipeline
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#00FF87] bg-[#00FF87]/10 border border-[#00FF87]/20 px-3 py-1.5 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00FF87] animate-pulse" />
            is_test = true (won&apos;t affect live metrics)
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8">
          {/* LEFT: Form */}
          <div>
            {/* Preset Scenarios */}
            <div className="mb-5">
              <div className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Quick Scenarios</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(PRESET_LABELS).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className="text-xs border border-[#1E1E2E] hover:border-[#00FF87]/40 text-gray-400 hover:text-white px-3 py-1.5 rounded-xl transition-all"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Form */}
            <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Amount (INR) *</label>
                  <input
                    type="number"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    placeholder="e.g. 5000"
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Country Code</label>
                  <input
                    value={form.country_code}
                    onChange={(e) => setForm({ ...form, country_code: e.target.value.toUpperCase() })}
                    placeholder="IN"
                    maxLength={2}
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1.5 block">Merchant Name</label>
                <input
                  value={form.merchant_name}
                  onChange={(e) => setForm({ ...form, merchant_name: e.target.value })}
                  placeholder="e.g. Amazon India"
                  className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Channel</label>
                  <select
                    value={form.channel}
                    onChange={(e) => setForm({ ...form, channel: e.target.value })}
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
                  >
                    <option value="online">Online</option>
                    <option value="pos_physical">POS Physical</option>
                    <option value="atm">ATM</option>
                    <option value="mobile">Mobile</option>
                    <option value="wire">Wire</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Transaction Type</label>
                  <select
                    value={form.transaction_type}
                    onChange={(e) => setForm({ ...form, transaction_type: e.target.value })}
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
                  >
                    <option value="purchase">Purchase</option>
                    <option value="withdrawal">Withdrawal</option>
                    <option value="transfer">Transfer</option>
                    <option value="refund">Refund</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Device Type</label>
                  <select
                    value={form.device_type}
                    onChange={(e) => setForm({ ...form, device_type: e.target.value })}
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
                  >
                    <option value="mobile">Mobile</option>
                    <option value="desktop">Desktop</option>
                    <option value="tablet">Tablet</option>
                    <option value="pos_terminal">POS Terminal</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">City</label>
                  <input
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    placeholder="Mumbai"
                    className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1.5 block">Customer ID (optional)</label>
                <input
                  value={form.customer_id}
                  onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                  placeholder="uuid of existing customer"
                  className="w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 font-mono focus:outline-none"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={runTest}
                  disabled={loading || !form.amount}
                  className="flex-1 flex items-center justify-center gap-2 bg-[#00FF87] text-black font-bold text-sm px-4 py-3 rounded-xl hover:bg-[#00FF87]/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <><Loader2 size={16} className="animate-spin" /> Running…</>
                  ) : (
                    <><Play size={16} /> Run Fraud Detection</>
                  )}
                </button>
                <button
                  onClick={resetForm}
                  className="flex items-center gap-2 text-sm text-gray-500 hover:text-white border border-[#1E1E2E] px-4 py-3 rounded-xl hover:border-gray-500 transition-all"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT: Results */}
          <div>
            {error && (
              <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-2xl p-4 mb-4 flex items-start gap-3">
                <XCircle size={16} className="text-[#EF4444] mt-0.5 shrink-0" />
                <div className="text-sm text-[#EF4444]">{error}</div>
              </div>
            )}

            {!result && !loading && !error && (
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-12 flex flex-col items-center justify-center h-full min-h-[400px]">
                <FlaskConical size={40} className="text-gray-700 mb-4" />
                <div className="text-gray-600 text-sm">
                  Fill in the form and click Run Fraud Detection
                </div>
                <div className="text-gray-700 text-xs mt-1">
                  Or choose a preset scenario to auto-fill
                </div>
              </div>
            )}

            {loading && (
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-12 flex flex-col items-center justify-center h-full min-h-[400px]">
                <Loader2 size={40} className="text-[#00FF87] animate-spin mb-4" />
                <div className="text-gray-400 text-sm">Running fraud detection pipeline…</div>
                <div className="text-gray-600 text-xs mt-1">Feature engineering → ML inference → Ensemble scoring</div>
              </div>
            )}

            {result && decision && (
              <div className="space-y-4">
                {/* Decision Banner */}
                <div
                  className="rounded-2xl p-5 border"
                  style={{
                    backgroundColor: `${decisionColor}12`,
                    borderColor: `${decisionColor}40`,
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-xs text-gray-400 uppercase tracking-widest font-medium">Decision</div>
                    <span
                      className="text-2xl font-black tracking-wider"
                      style={{ color: decisionColor }}
                    >
                      {decision}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-xs text-gray-500">Fraud Score</div>
                      <div className="text-3xl font-black" style={{ color: decisionColor }}>
                        {result.fraud_score != null ? `${(result.fraud_score * 100).toFixed(1)}%` : "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Category</div>
                      <div className="text-sm font-semibold capitalize text-white">
                        {result.fraud_category}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Risk Level</div>
                      <div className="text-sm font-semibold capitalize" style={{ color: decisionColor }}>
                        {result.fraud_risk_level || "—"}
                      </div>
                    </div>
                    <div className="ml-auto">
                      {result.is_blocked ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#EF4444]">
                          <XCircle size={14} /> Transaction Blocked
                        </div>
                      ) : result.is_flagged ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#F59E0B]">
                          <AlertTriangle size={14} /> Flagged for Review
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-[#00FF87]">
                          <CheckCircle2 size={14} /> Passed
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Triggered Rules */}
                {result.triggered_rule_ids && result.triggered_rule_ids.length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                      Triggered Rules
                    </div>
                    <div className="space-y-1.5">
                      {result.triggered_rule_ids.map((rule) => (
                        <div key={rule} className="flex items-center gap-2 text-sm">
                          <AlertTriangle size={13} className="text-[#F59E0B] shrink-0" />
                          <span className="text-gray-300 capitalize">{rule.replace(/_/g, " ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SHAP / Feature Contributions */}
                {result.shap_values && Object.keys(result.shap_values).length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                        Top Fraud Contributors (SHAP)
                      </div>
                      <Info size={12} className="text-gray-600" />
                    </div>
                    <div className="space-y-2">
                      {Object.entries(result.shap_values)
                        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                        .slice(0, 8)
                        .map(([feat, val]) => {
                          const isPositive = val > 0;
                          const barWidth = Math.min(100, Math.abs(val) * 100);
                          return (
                            <div key={feat} className="flex items-center gap-3">
                              <div className="w-36 text-xs text-gray-500 truncate shrink-0 capitalize">
                                {feat.replace(/^feat_/, "").replace(/_/g, " ")}
                              </div>
                              <div className="flex-1 bg-[#0A0A0F] rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all"
                                  style={{
                                    width: `${barWidth}%`,
                                    backgroundColor: isPositive ? "#EF4444" : "#00FF87",
                                  }}
                                />
                              </div>
                              <div
                                className="text-xs font-mono w-16 text-right shrink-0"
                                style={{ color: isPositive ? "#EF4444" : "#00FF87" }}
                              >
                                {isPositive ? "+" : ""}{val.toFixed(3)}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* Transaction Summary */}
                <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                  <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                    Transaction Written to DB
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      ["Transaction ID", result.id.slice(0, 16) + "…"],
                      ["Amount", `₹${Number(result.amount).toLocaleString()}`],
                      ["Channel", result.channel],
                      ["Merchant", result.merchant_name || "—"],
                      ["Model Version", result.model_version || "—"],
                      ["Scored At", result.fraud_scored_at ? new Date(result.fraud_scored_at).toLocaleTimeString() : "—"],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <div className="text-gray-600">{k}</div>
                        <div className="text-gray-300 font-mono">{v}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Link
                      href="/dashboard/alerts"
                      className="text-xs text-[#F59E0B] hover:underline"
                    >
                      View Alerts →
                    </Link>
                    <span className="text-gray-600">·</span>
                    <Link
                      href="/dashboard/transactions"
                      className="text-xs text-[#3B82F6] hover:underline"
                    >
                      View in Transactions →
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
