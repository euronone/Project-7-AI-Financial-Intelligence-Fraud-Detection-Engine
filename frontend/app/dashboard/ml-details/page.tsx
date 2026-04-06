"use client";

import { useAuthStore, isAdmin, type AuthUser } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, RefreshCw, Brain,
  ChevronDown, ChevronUp, Cpu, BarChart2, GitBranch,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

// ── Types (matching actual backend response shapes) ──────────────────────────
interface MLModel {
  model_id: string;
  model_name: string;       // backend uses model_name not name
  model_type: string;       // backend uses model_type not type
  status: string;
  version: string;
  metrics: {                // backend nests all metrics under metrics{}
    precision: number | null;
    recall: number | null;
    f1_score: number | null;
    auc_roc: number | null;
    accuracy: number | null;
  };
  ensemble_weight: number | null;
  description: string;
  layer: string;
}
interface FeatureCategory {
  category: string;
  feature_count: number;       // backend uses feature_count not count
  importance_weight: number;   // backend uses importance_weight not importance
  features: string[];          // backend uses features not examples
  color: string;
  description: string;
}
interface SampleTransaction {
  transaction_id: string;    // backend uses transaction_id not id
  amount: number;
  channel: string;
  fraud_category: string;
  fraud_score: number | null;
  risk_level: string | null; // backend uses risk_level not fraud_risk_level
  merchant_name: string | null;
  timestamp: string;         // backend uses timestamp not transaction_timestamp
  label: string;
  color: string;
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
    { icon: Database,      label: "Data Sources",  href: "/dashboard/data-sources", active: false, adminOnly: false },
    { icon: Brain,         label: "ML Details",    href: "/dashboard/ml-details",   active: true,  adminOnly: false },
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

// ── Helpers ──────────────────────────────────────────────────────────────────
const RISK_COLORS: Record<string, string> = {
  legitimate: "#00FF87", suspicious: "#F59E0B", fraudulent: "#EF4444", unscored: "#6B7280",
};

const MODEL_COLORS: Record<string, string> = {
  logistic_regression: "#3B82F6",
  random_forest: "#00FF87",
  xgboost: "#F59E0B",
  isolation_forest: "#8B5CF6",
  dbscan: "#F97316",
  neural_network: "#EC4899",
  ensemble: "#00FF87",
};

function statusBadge(s: string) {
  if (s === "active") return "text-[#00FF87] bg-[#00FF87]/10";
  if (s === "training") return "text-[#F59E0B] bg-[#F59E0B]/10";
  if (s === "retired") return "text-gray-500 bg-gray-500/10";
  return "text-gray-400 bg-gray-400/10";
}

function metricBar(value: number | null, color: string) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-[#0A0A0F] rounded-full h-1.5 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-mono w-10 text-right" style={{ color }}>{pct}%</span>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function MlDetailsPage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();

  const [models, setModels] = useState<MLModel[]>([]);
  const [features, setFeatures] = useState<FeatureCategory[]>([]);
  const [samples, setSamples] = useState<SampleTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [samplesOpen, setSamplesOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  const fetchAll = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [md, ft, sa] = await Promise.all([
        apiClient.getMlModels(token),
        apiClient.getMlFeatures(token),
        apiClient.getMlSampleTransactions(token),
      ]);
      setModels((md as { models: MLModel[] }).models || []);
      // backend key is feature_categories, not categories
      setFeatures((ft as { feature_categories: FeatureCategory[] }).feature_categories || []);
      // backend key is samples, not transactions
      setSamples((sa as { samples: SampleTransaction[] }).samples || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  const maxImportance = features.reduce((m, f) => Math.max(m, f.importance_weight), 0.01);

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <Sidebar plan={user.plan} user={user} clearAuth={clearAuth} router={router} />

      <main className="ml-60 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black">ML Details</h1>
            <p className="text-gray-500 text-sm mt-1">Model registry, feature importance, and labeled sample transactions</p>
          </div>
          <button
            onClick={fetchAll}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-white border border-[#1E1E2E] px-3 py-1.5 rounded-lg hover:border-gray-500 transition-all"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Detection Architecture Banner */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-8 overflow-x-auto">
          <div className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-4">Detection Pipeline</div>
          <div className="flex items-center gap-2 min-w-max">
            {[
              { label: "Rules Engine", color: "#F59E0B", icon: "⚡", weight: "25%" },
              { label: "Isolation Forest", color: "#8B5CF6", icon: "🌲", weight: "10%" },
              { label: "DBSCAN", color: "#F97316", icon: "🔵", weight: "10%" },
              { label: "XGBoost", color: "#F59E0B", icon: "🚀", weight: "30%" },
              { label: "Random Forest", color: "#00FF87", icon: "🌿", weight: "15%" },
              { label: "Neural Network", color: "#EC4899", icon: "🧠", weight: "10%" },
            ].map((m, i, arr) => (
              <div key={m.label} className="flex items-center gap-2">
                <div
                  className="flex flex-col items-center gap-1 px-3 py-2 rounded-xl border"
                  style={{ backgroundColor: `${m.color}10`, borderColor: `${m.color}30` }}
                >
                  <span className="text-base">{m.icon}</span>
                  <span className="text-xs font-medium" style={{ color: m.color }}>{m.label}</span>
                  <span className="text-xs text-gray-500">{m.weight}</span>
                </div>
                {i < arr.length - 1 && <span className="text-gray-600 text-lg">→</span>}
              </div>
            ))}
            <span className="text-gray-600 text-lg">→</span>
            <div className="flex flex-col items-center gap-1 px-4 py-2 rounded-xl bg-[#00FF87]/10 border border-[#00FF87]/30">
              <BarChart2 size={18} className="text-[#00FF87]" />
              <span className="text-xs font-bold text-[#00FF87]">Ensemble Score</span>
              <span className="text-xs text-gray-500">0.0–1.0</span>
            </div>
          </div>
        </div>

        {/* Model Cards */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Cpu size={16} className="text-[#3B82F6]" /> Model Registry
          </h2>
          {loading ? (
            <div className="grid grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 animate-pulse">
                  <div className="h-4 w-32 bg-[#1E1E2E] rounded mb-3" />
                  <div className="h-3 w-20 bg-[#1E1E2E] rounded mb-4" />
                  <div className="space-y-2">
                    {[1,2,3,4].map(j => <div key={j} className="h-2 bg-[#1E1E2E] rounded" />)}
                  </div>
                </div>
              ))}
            </div>
          ) : models.length === 0 ? (
            <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-12 text-center text-gray-600">
              <Brain size={32} className="mx-auto mb-2 text-gray-700" />
              No models found — run <code className="text-xs">python scripts/train_models.py</code>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {models.map((m) => {
                const col = MODEL_COLORS[m.model_id] || "#6B7280";
                return (
                  <div
                    key={m.model_id}
                    className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 hover:border-[#2E2E3E] transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="font-semibold text-sm" style={{ color: col }}>{m.model_name}</div>
                        <div className="text-xs text-gray-500 mt-0.5 font-mono">{m.version}</div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${statusBadge(m.status)}`}>
                          {m.status}
                        </span>
                        {m.ensemble_weight != null && (
                          <span className="text-xs text-gray-600">{Math.round(m.ensemble_weight * 100)}% weight</span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mb-4 leading-relaxed">{m.description}</p>
                    <div className="space-y-2">
                      {[
                        { label: "Precision", val: m.metrics?.precision ?? null },
                        { label: "Recall",    val: m.metrics?.recall ?? null },
                        { label: "F1",        val: m.metrics?.f1_score ?? null },
                        { label: "AUC-ROC",   val: m.metrics?.auc_roc ?? null },
                      ].map(({ label, val }) => (
                        val != null ? (
                          <div key={label}>
                            <div className="text-xs text-gray-600 mb-0.5">{label}</div>
                            {metricBar(val, col)}
                          </div>
                        ) : null
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Feature Importance */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 mb-6">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <GitBranch size={16} className="text-[#8B5CF6]" /> Feature Importance by Category
          </h2>
          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 bg-[#0A0A0F] rounded animate-pulse" />
              ))}
            </div>
          ) : features.length === 0 ? (
            <div className="text-center text-gray-600 py-6">Feature data not available</div>
          ) : (
            <div className="space-y-5">
              {features.map((f) => {
                const pct = Math.round((f.importance_weight / maxImportance) * 100);
                return (
                  <div key={f.category}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white capitalize">{f.category}</span>
                        <span className="text-gray-600">{f.feature_count} features</span>
                      </div>
                      <span className="text-[#8B5CF6] font-mono font-semibold">
                        {(f.importance_weight * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-[#0A0A0F] rounded-full h-2.5 mb-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: f.color || "#8B5CF6" }}
                      />
                    </div>
                    <div className="flex gap-1.5 flex-wrap">
                      {(f.features || []).map((ex: string) => (
                        <span key={ex} className="text-xs bg-[#1E1E2E] text-gray-400 px-2 py-0.5 rounded font-mono">
                          {ex}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sample Transactions (collapsible) */}
        <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl overflow-hidden">
          <button
            onClick={() => setSamplesOpen((o) => !o)}
            className="w-full flex items-center justify-between p-5 hover:bg-[#0D0D15] transition-all"
          >
            <div className="flex items-center gap-2">
              <FlaskConical size={16} className="text-[#F59E0B]" />
              <span className="text-sm font-semibold">Sample Labeled Transactions</span>
              {samples.length > 0 && (
                <span className="text-xs text-gray-500 bg-[#1E1E2E] px-2 py-0.5 rounded-full">
                  {samples.length} records
                </span>
              )}
            </div>
            {samplesOpen ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
          </button>

          {samplesOpen && (
            <div className="border-t border-[#1E1E2E] overflow-x-auto">
              {loading ? (
                <div className="p-4 space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-8 bg-[#0A0A0F] rounded animate-pulse" />
                  ))}
                </div>
              ) : samples.length === 0 ? (
                <div className="p-8 text-center text-gray-600 text-sm">No sample transactions available</div>
              ) : (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#1E1E2E]">
                      {["ID", "Amount", "Channel", "Merchant", "Fraud Score", "Category", "Risk", "Test", "Timestamp"].map(h => (
                        <th key={h} className="text-left text-gray-500 font-medium py-3 px-4">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {samples.map((txn) => {
                      const cat = txn.fraud_category || "unscored";
                      const col = txn.color || RISK_COLORS[cat] || "#6B7280";
                      return (
                        <tr key={txn.transaction_id} className="border-b border-[#1E1E2E]/40 hover:bg-[#0A0A0F] transition-all">
                          <td className="py-2.5 px-4 font-mono text-gray-500">{txn.transaction_id.slice(0, 8)}…</td>
                          <td className="py-2.5 px-4 font-semibold">₹{Number(txn.amount).toLocaleString()}</td>
                          <td className="py-2.5 px-4 text-gray-400">{txn.channel}</td>
                          <td className="py-2.5 px-4 text-gray-300 max-w-[120px] truncate">{txn.merchant_name || "—"}</td>
                          <td className="py-2.5 px-4 font-mono" style={{ color: col }}>
                            {txn.fraud_score != null ? (txn.fraud_score * 100).toFixed(1) + "%" : "—"}
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="capitalize px-2 py-0.5 rounded-full" style={{ color: col, backgroundColor: `${col}15` }}>
                              {cat}
                            </span>
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="capitalize" style={{ color: col }}>
                              {txn.risk_level || "—"}
                            </span>
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="text-gray-600">{txn.label || "live"}</span>
                          </td>
                          <td className="py-2.5 px-4 text-gray-600">
                            {txn.timestamp ? new Date(txn.timestamp).toLocaleString() : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
