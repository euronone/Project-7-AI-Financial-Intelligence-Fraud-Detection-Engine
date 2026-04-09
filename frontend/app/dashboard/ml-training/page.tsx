"use client";

/**
 * ML Training page (/dashboard/ml-training)
 *
 * Two-phase UI:
 *   Phase 1 — Config: algorithm picker, data window, options, pickle upload
 *   Phase 2 — Job:    live progress feed, metrics results, promote / re-optimize
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield, Activity, TrendingUp, Users, AlertTriangle,
  FlaskConical, Table, Settings, LogOut, Brain,
  Play, RefreshCw, CheckCircle2, XCircle, Upload,
  ChevronDown, ChevronUp, Cpu, BarChart2, Layers,
  ArrowUpCircle, Clock, Database,
} from "lucide-react";

import { useAuthStore, isAdmin } from "@/store/auth-store";
import {
  apiClient,
  type AlgorithmInfo,
  type TrainingJobStatus,
  type TrainingJobSummary,
} from "@/lib/api-client";

// ── Sidebar nav ───────────────────────────────────────────────────────────────
const NAV = [
  { href: "/dashboard",               icon: Activity,      label: "Overview",      active: false, adminOnly: false },
  { href: "/dashboard/transactions",  icon: TrendingUp,    label: "Transactions",  active: false, adminOnly: false },
  { href: "/dashboard/alerts",        icon: AlertTriangle, label: "Fraud Alerts",  active: false, adminOnly: false },
  { href: "/dashboard/test-me",       icon: FlaskConical,  label: "Test Me",       active: false, adminOnly: true },
  { href: "/dashboard/customers",     icon: Users,         label: "Customers",     active: false, adminOnly: false },
  { href: "/dashboard/data-sources",  icon: Database,      label: "Data Sources",  active: false, adminOnly: false },
  { href: "/dashboard/data-schema",   icon: Table,         label: "Data Schema",   active: false, adminOnly: false },
  { href: "/dashboard/ml-training",   icon: Brain,         label: "ML Training",   active: true,  adminOnly: false },
  { href: "/dashboard/settings",      icon: Settings,      label: "Settings",      active: false, adminOnly: false },
];

// ── Constants ─────────────────────────────────────────────────────────────────
const WINDOW_OPTIONS = [
  { label: "30 days",  value: 30 },
  { label: "60 days",  value: 60 },
  { label: "90 days",  value: 90 },
  { label: "180 days", value: 180 },
  { label: "365 days", value: 365 },
  { label: "All time", value: 0 },
];

const SPLIT_OPTIONS = [
  { label: "80 / 20", value: 0.20, hint: "Train 80% · Test 20% (default)" },
  { label: "90 / 10", value: 0.10, hint: "Train 90% · Test 10% (more data)" },
  { label: "70 / 30", value: 0.30, hint: "Train 70% · Test 30% (safer estimate)" },
];

const RE_WINDOW_OPTIONS = [
  { label: "90 days",  value: 90 },
  { label: "180 days", value: 180 },
  { label: "365 days", value: 365 },
  { label: "All time", value: 0 },
];

const STATUS_COLOR: Record<string, string> = {
  queued:     "text-gray-400",
  running:    "text-[#3B82F6]",
  optimizing: "text-[#F59E0B]",
  evaluating: "text-[#8B5CF6]",
  completed:  "text-[#00FF87]",
  failed:     "text-red-400",
  cancelled:  "text-gray-500",
};

const METRIC_COLOR = (v: number) =>
  v >= 0.9 ? "text-[#00FF87]" : v >= 0.75 ? "text-[#F59E0B]" : "text-red-400";

// ── Small components ──────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? "text-gray-400";
  const icon =
    status === "completed" ? <CheckCircle2 size={12} /> :
    status === "failed"    ? <XCircle size={12} /> :
    status === "queued"    ? <Clock size={12} /> :
    <RefreshCw size={12} className="animate-spin" />;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold ${color}`}>
      {icon} {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function MetricCell({ label, value }: { label: string; value?: number }) {
  if (value === undefined || value === null) {
    return (
      <div className="text-center">
        <div className="text-xs text-gray-600">—</div>
        <div className="text-[10px] text-gray-600">{label}</div>
      </div>
    );
  }
  return (
    <div className="text-center">
      <div className={`text-sm font-bold font-mono ${METRIC_COLOR(value)}`}>
        {(value * 100).toFixed(1)}%
      </div>
      <div className="text-[10px] text-gray-500">{label}</div>
    </div>
  );
}

function AlgoCard({
  algo,
  selected,
  onToggle,
}: {
  algo: AlgorithmInfo;
  selected: boolean;
  onToggle: () => void;
}) {
  const unavailable = algo.available === false;
  return (
    <button
      onClick={() => !unavailable && onToggle()}
      disabled={unavailable}
      className={`relative text-left w-full p-3.5 rounded-xl border transition-all ${
        unavailable
          ? "border-[#1E1E2E] opacity-40 cursor-not-allowed"
          : selected
          ? "border-[#3B82F6]/50 bg-[#3B82F6]/10"
          : "border-[#2E2E3E] hover:border-[#3B82F6]/30 hover:bg-[#111118]"
      }`}
    >
      {/* Selection indicator */}
      <span
        className={`absolute top-3 right-3 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all ${
          selected ? "border-[#3B82F6] bg-[#3B82F6]" : "border-[#2E2E3E]"
        }`}
      >
        {selected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
      </span>

      <div className="pr-6">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-sm font-semibold text-white">{algo.name}</span>
          {algo.recommended && (
            <span className="text-[9px] font-bold bg-[#00FF87]/10 text-[#00FF87] px-1.5 py-0.5 rounded">
              REC
            </span>
          )}
          {algo.tunable && (
            <span className="text-[9px] text-[#8B5CF6] border border-[#8B5CF6]/30 px-1.5 py-0.5 rounded">
              tunable
            </span>
          )}
        </div>
        <p className="text-[11px] text-gray-500 leading-snug">{algo.description}</p>
        <div className="text-[10px] text-gray-600 mt-1.5 font-mono">{algo.library}</div>
      </div>
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function MLTrainingPage() {
  const { isAuthenticated, token, user, clearAuth } = useAuthStore();
  const router = useRouter();

  // Auth guard
  useEffect(() => {
    if (!isAuthenticated) router.replace("/login");
  }, [isAuthenticated, router]);

  // ── Algorithm catalogue ──────────────────────────────────────────────────
  const [catalogue, setCatalogue] = useState<{
    clustering: AlgorithmInfo[];
    supervised: AlgorithmInfo[];
  }>({ clustering: [], supervised: [] });

  useEffect(() => {
    if (!token) return;
    apiClient.getTrainingAlgorithms(token).then(setCatalogue).catch(() => {});
  }, [token]);

  // ── Config state (Phase 1) ───────────────────────────────────────────────
  const [selectedAlgos, setSelectedAlgos] = useState<Set<string>>(
    new Set(["xgboost", "random_forest", "isolation_forest"])
  );
  const [windowDays, setWindowDays] = useState(90);
  const [testSize, setTestSize] = useState(0.20);
  const [autoOptimize, setAutoOptimize] = useState(true);
  const [useCustomCols, setUseCustomCols] = useState(true);

  function toggleAlgo(id: string) {
    setSelectedAlgos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // ── Pickle upload ────────────────────────────────────────────────────────
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handlePickleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true);
    setUploadResult(null);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("model_name", file.name.replace(".pkl", ""));
      const res = await apiClient.uploadPickleModel(form, token);
      setUploadResult(res.message);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  // ── Job state (Phase 2) ──────────────────────────────────────────────────
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<TrainingJobStatus | null>(null);
  const [pastJobs, setPastJobs] = useState<TrainingJobSummary[]>([]);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load past jobs on mount
  useEffect(() => {
    if (!token) return;
    apiClient.listTrainingJobs(token).then((r) => setPastJobs(r.jobs)).catch(() => {});
  }, [token]);

  // Poll active job
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!activeJobId || !token) return;
    stopPolling();

    async function poll() {
      if (!token || !activeJobId) return;
      try {
        const s = await apiClient.getTrainingJobStatus(activeJobId, token);
        setJobStatus(s);
        if (s.status === "completed" || s.status === "failed") {
          stopPolling();
          // Refresh past jobs list
          apiClient.listTrainingJobs(token).then((r) => setPastJobs(r.jobs)).catch(() => {});
        }
      } catch {
        stopPolling();
      }
    }

    poll(); // immediate first call
    pollingRef.current = setInterval(poll, 2000);
    return stopPolling;
  }, [activeJobId, token, stopPolling]);

  async function handleStart() {
    if (!token || selectedAlgos.size === 0) return;
    setStarting(true);
    setStartError(null);
    try {
      const res = await apiClient.startTrainingJob(
        {
          algorithms: Array.from(selectedAlgos),
          data_window_days: windowDays,
          auto_optimize: autoOptimize,
          use_custom_columns: useCustomCols,
          test_size: testSize,
        },
        token
      );
      setActiveJobId(res.job_id);
      setJobStatus(null);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : "Failed to start");
    } finally {
      setStarting(false);
    }
  }

  // ── Re-optimize modal ────────────────────────────────────────────────────
  const [reOptOpen, setReOptOpen] = useState(false);
  const [reOptWindow, setReOptWindow] = useState(180);
  const [reOpting, setReOpting] = useState(false);

  async function handleReOptimize() {
    if (!token || !activeJobId) return;
    setReOpting(true);
    try {
      const res = await apiClient.reoptimizeJob(activeJobId, reOptWindow, token);
      setActiveJobId(res.job_id);
      setJobStatus(null);
      setReOptOpen(false);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : "Re-optimize failed");
    } finally {
      setReOpting(false);
    }
  }

  // ── Promote ──────────────────────────────────────────────────────────────
  const [promoting, setPromoting] = useState(false);
  const [promoteMsg, setPromoteMsg] = useState<string | null>(null);

  async function handlePromote() {
    if (!token || !activeJobId) return;
    setPromoting(true);
    setPromoteMsg(null);
    try {
      const res = await apiClient.promoteTrainingJob(activeJobId, token);
      setPromoteMsg(res.message);
    } catch (err) {
      setPromoteMsg(`Error: ${err instanceof Error ? err.message : "Promote failed"}`);
    } finally {
      setPromoting(false);
    }
  }

  function handleLogout() {
    clearAuth();
    router.replace("/login");
  }

  const isJobRunning = jobStatus && !["completed", "failed", "cancelled"].includes(jobStatus.status);
  const metrics = jobStatus?.metrics ?? {};
  const algoKeys = Object.keys(metrics).filter((k) => k !== "ensemble");

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex">

      {/* Sidebar */}
      <aside className="w-64 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col">
        <div className="p-6 border-b border-[#1E1E2E]">
          <div className="flex items-center gap-2">
            <Shield size={22} className="text-[#00FF87]" />
            <span className="font-bold text-lg">FinShield AI</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">{user?.institution_name || "Dashboard"}</div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {NAV.filter(({ adminOnly }) => !adminOnly || isAdmin(user))
            .map(({ href, icon: Icon, label, active }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                active
                  ? "bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20"
                  : "text-gray-400 hover:text-white hover:bg-[#1E1E2E]"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-[#1E1E2E]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-red-400 hover:bg-red-900/10 rounded-xl text-sm transition-all"
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-auto">

        {/* Header */}
        <header className="px-8 py-5 border-b border-[#1E1E2E] flex items-center justify-between sticky top-0 bg-[#0A0A0F] z-10">
          <div className="flex items-center gap-2">
            <Brain size={18} className="text-[#8B5CF6]" />
            <h1 className="text-xl font-bold">Custom ML Model Training</h1>
          </div>
          {activeJobId && jobStatus && (
            <div className="flex items-center gap-3">
              <StatusBadge status={jobStatus.status} />
              <button
                onClick={() => { setActiveJobId(null); setJobStatus(null); }}
                className="text-xs text-gray-500 hover:text-white border border-[#2E2E3E] hover:border-[#3B82F6]/30 px-3 py-1.5 rounded-lg transition-all"
              >
                ← New Training Run
              </button>
            </div>
          )}
        </header>

        <div className="flex-1 px-8 py-6 space-y-6">

          {/* ═══════════════════════════════════════════════════════════════
              PHASE 1 — Configuration (shown when no active job)
          ════════════════════════════════════════════════════════════════ */}
          {!activeJobId && (
            <>
              {/* ── Algorithm selection ── */}
              <div className="grid grid-cols-2 gap-6">

                {/* Clustering */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Layers size={15} className="text-[#8B5CF6]" />
                    <h2 className="text-sm font-bold text-[#8B5CF6] uppercase tracking-wide">
                      Clustering / Anomaly Detection
                    </h2>
                    <span className="text-[10px] text-gray-600 ml-auto">No labels required</span>
                  </div>
                  <div className="space-y-2">
                    {catalogue.clustering.map((a) => (
                      <AlgoCard
                        key={a.id}
                        algo={a}
                        selected={selectedAlgos.has(a.id)}
                        onToggle={() => toggleAlgo(a.id)}
                      />
                    ))}
                    {catalogue.clustering.length === 0 && (
                      <div className="text-xs text-gray-600 text-center py-4">
                        <RefreshCw size={14} className="animate-spin inline mr-1" />
                        Loading…
                      </div>
                    )}
                  </div>
                </div>

                {/* Supervised */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Cpu size={15} className="text-[#3B82F6]" />
                    <h2 className="text-sm font-bold text-[#3B82F6] uppercase tracking-wide">
                      Supervised Classification
                    </h2>
                    <span className="text-[10px] text-gray-600 ml-auto">Needs fraud labels</span>
                  </div>
                  <div className="space-y-2">
                    {catalogue.supervised.map((a) => (
                      <AlgoCard
                        key={a.id}
                        algo={a}
                        selected={selectedAlgos.has(a.id)}
                        onToggle={() => toggleAlgo(a.id)}
                      />
                    ))}
                    {catalogue.supervised.length === 0 && (
                      <div className="text-xs text-gray-600 text-center py-4">
                        <RefreshCw size={14} className="animate-spin inline mr-1" />
                        Loading…
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* ── Training options row ── */}
              <div className="grid grid-cols-4 gap-4">

                {/* Data window */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Database size={14} className="text-[#F59E0B]" />
                    <span className="text-sm font-bold text-[#F59E0B]">Data Window</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {WINDOW_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setWindowDays(opt.value)}
                        className={`px-2 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                          windowDays === opt.value
                            ? "border-[#F59E0B]/50 bg-[#F59E0B]/10 text-[#F59E0B]"
                            : "border-[#2E2E3E] text-gray-500 hover:border-[#F59E0B]/20 hover:text-gray-300"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-gray-600 mt-2">
                    {windowDays === 0
                      ? "Training on all available transaction history."
                      : `Training on the last ${windowDays} days of transactions.`}
                  </p>
                </div>

                {/* Train / Test split */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart2 size={14} className="text-[#00FF87]" />
                    <span className="text-sm font-bold text-[#00FF87]">Train / Test Split</span>
                  </div>
                  <div className="space-y-2">
                    {SPLIT_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setTestSize(opt.value)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                          testSize === opt.value
                            ? "border-[#00FF87]/50 bg-[#00FF87]/10 text-[#00FF87]"
                            : "border-[#2E2E3E] text-gray-500 hover:border-[#00FF87]/20 hover:text-gray-300"
                        }`}
                      >
                        <span>{opt.label}</span>
                        {testSize === opt.value && (
                          <span className="text-[9px] font-bold bg-[#00FF87]/20 px-1.5 py-0.5 rounded">
                            SELECTED
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-gray-600 mt-2">
                    {SPLIT_OPTIONS.find((o) => o.value === testSize)?.hint ?? ""}
                  </p>
                </div>

                {/* Toggles */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5 space-y-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Settings size={14} className="text-gray-400" />
                    <span className="text-sm font-bold text-gray-300">Training Options</span>
                  </div>

                  {[
                    {
                      label: "Auto-Optimize Hyperparameters",
                      hint: "Runs a grid search for each supervised algorithm after initial training.",
                      value: autoOptimize,
                      set: setAutoOptimize,
                    },
                    {
                      label: "Respect Schema Column Mapping",
                      hint: "Skip columns marked as denied in the Data Schema page.",
                      value: useCustomCols,
                      set: setUseCustomCols,
                    },
                  ].map(({ label, hint, value, set }) => (
                    <div key={label} className="flex items-start gap-3">
                      <button
                        onClick={() => set(!value)}
                        className={`relative mt-0.5 flex-shrink-0 w-9 h-5 rounded-full border-2 transition-colors ${
                          value ? "border-[#00FF87] bg-[#00FF87]/20" : "border-[#2E2E3E] bg-[#1E1E2E]"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-3.5 w-3.5 rounded-full transition-transform ${
                            value ? "translate-x-4 bg-[#00FF87]" : "translate-x-0 bg-[#4E4E5E]"
                          }`}
                        />
                      </button>
                      <div>
                        <div className="text-xs font-semibold text-white">{label}</div>
                        <div className="text-[11px] text-gray-600">{hint}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pickle upload */}
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Upload size={14} className="text-[#F97316]" />
                    <span className="text-sm font-bold text-[#F97316]">Upload Pre-trained Model</span>
                  </div>
                  <p className="text-[11px] text-gray-500 mb-3 leading-snug">
                    Upload a <code className="text-[#F97316]">.pkl</code> file containing one or more
                    sklearn-compatible models. It will be registered as the active model immediately
                    (no training required).
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pkl"
                    onChange={handlePickleUpload}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-[#F97316]/30 hover:border-[#F97316]/60 rounded-xl py-3 text-xs text-[#F97316] hover:bg-[#F97316]/5 transition-all disabled:opacity-50"
                  >
                    {uploading
                      ? <><RefreshCw size={13} className="animate-spin" /> Uploading…</>
                      : <><Upload size={13} /> Choose .pkl file</>
                    }
                  </button>
                  {uploadResult && (
                    <div className="mt-2 text-[11px] text-[#00FF87] flex gap-1">
                      <CheckCircle2 size={12} className="mt-0.5 flex-shrink-0" />
                      {uploadResult}
                    </div>
                  )}
                  {uploadError && (
                    <div className="mt-2 text-[11px] text-red-400">{uploadError}</div>
                  )}
                </div>
              </div>

              {/* ── Start button ── */}
              <div className="flex items-center gap-4">
                <button
                  onClick={handleStart}
                  disabled={starting || selectedAlgos.size === 0}
                  className="flex items-center gap-2 bg-[#8B5CF6] hover:bg-[#7C3AED] disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold px-8 py-3 rounded-xl transition-all text-sm"
                >
                  {starting
                    ? <><RefreshCw size={15} className="animate-spin" /> Starting…</>
                    : <><Play size={15} /> Start Training</>
                  }
                </button>
                <div className="text-sm text-gray-500">
                  {selectedAlgos.size === 0
                    ? "Select at least one algorithm"
                    : `${selectedAlgos.size} algorithm(s) · ${windowDays === 0 ? "all-time" : windowDays + "d"} window · ${Math.round((1 - testSize) * 100)}/${Math.round(testSize * 100)} split`}
                </div>
                {startError && (
                  <div className="text-sm text-red-400 flex gap-1">
                    <XCircle size={14} className="mt-0.5" /> {startError}
                  </div>
                )}
              </div>

              {/* ── Past jobs table ── */}
              {pastJobs.length > 0 && (
                <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-[#1E1E2E] flex items-center gap-2">
                    <BarChart2 size={14} className="text-gray-400" />
                    <span className="text-sm font-semibold text-gray-300">Previous Training Runs</span>
                  </div>
                  <div className="divide-y divide-[#1E1E2E]">
                    {pastJobs.map((j) => (
                      <div
                        key={j.job_id}
                        className="flex items-center gap-4 px-5 py-3 hover:bg-[#111118] transition-colors cursor-pointer"
                        onClick={() => {
                          setActiveJobId(j.job_id);
                          setJobStatus(null);
                        }}
                      >
                        <StatusBadge status={j.status} />
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-mono text-gray-400 truncate">
                            {j.algorithms.join(", ")}
                          </div>
                          <div className="text-[10px] text-gray-600">
                            {j.data_window_days ? `${j.data_window_days}d window` : "all-time"} ·{" "}
                            {j.training_samples ? `${j.training_samples.toLocaleString()} samples` : "—"}
                            {j.parent_job_id && " · re-optimize"}
                          </div>
                        </div>
                        {j.best_algorithm && (
                          <span className="text-[10px] text-[#8B5CF6] border border-[#8B5CF6]/20 px-2 py-0.5 rounded">
                            best: {j.best_algorithm}
                          </span>
                        )}
                        <div className="text-[10px] text-gray-600">
                          {j.created_at ? new Date(j.created_at).toLocaleString() : "—"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* ═══════════════════════════════════════════════════════════════
              PHASE 2 — Job progress + results
          ════════════════════════════════════════════════════════════════ */}
          {activeJobId && (
            <div className="space-y-5">

              {/* Progress bar */}
              <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Brain size={16} className="text-[#8B5CF6]" />
                    <span className="text-sm font-bold text-white">
                      {jobStatus?.current_stage ?? "Initializing…"}
                    </span>
                  </div>
                  <StatusBadge status={jobStatus?.status ?? "queued"} />
                </div>

                {/* Progress bar */}
                <div className="h-2 bg-[#1E1E2E] rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] rounded-full transition-all duration-500"
                    style={{ width: `${jobStatus?.progress_pct ?? 0}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>
                    {jobStatus?.training_samples
                      ? `${jobStatus.training_samples.toLocaleString()} samples`
                      : "Fetching data…"}
                  </span>
                  <span>{jobStatus?.progress_pct ?? 0}%</span>
                </div>

                {/* Stage timeline */}
                <div className="mt-4 flex items-center gap-1 overflow-x-auto">
                  {["Fetching Data", "Feature Engineering", "Training", "Optimizing", "Evaluating", "Completed"].map(
                    (stage, i) => {
                      const pct = jobStatus?.progress_pct ?? 0;
                      const stagePct = [8, 30, 68, 88, 96, 100][i];
                      const done = pct >= stagePct;
                      const active = pct >= (i === 0 ? 0 : [0, 8, 30, 68, 88, 96][i]) && !done;
                      return (
                        <div key={stage} className="flex items-center gap-1 flex-shrink-0">
                          <div
                            className={`text-[10px] font-semibold px-2 py-1 rounded-full whitespace-nowrap ${
                              done
                                ? "bg-[#00FF87]/10 text-[#00FF87]"
                                : active
                                ? "bg-[#3B82F6]/10 text-[#3B82F6] animate-pulse"
                                : "text-gray-700"
                            }`}
                          >
                            {stage}
                          </div>
                          {i < 5 && <div className="w-3 h-px bg-[#2E2E3E]" />}
                        </div>
                      );
                    }
                  )}
                </div>
              </div>

              {/* Live log */}
              <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl overflow-hidden">
                <div className="px-5 py-3 border-b border-[#1E1E2E] text-xs font-bold text-gray-500 uppercase tracking-wide flex items-center gap-2">
                  <Activity size={12} />
                  Training Log
                  {isJobRunning && (
                    <span className="ml-auto flex items-center gap-1 text-[#3B82F6]">
                      <RefreshCw size={10} className="animate-spin" /> Live
                    </span>
                  )}
                </div>
                <div className="h-56 overflow-y-auto p-4 font-mono text-[11px] space-y-0.5">
                  {(jobStatus?.log_lines ?? []).length === 0 ? (
                    <div className="text-gray-700 text-center pt-8">Waiting for log output…</div>
                  ) : (
                    [...(jobStatus?.log_lines ?? [])].reverse().map((line, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-gray-700 flex-shrink-0">
                          {new Date(line.ts).toLocaleTimeString()}
                        </span>
                        <span
                          className={
                            line.msg.startsWith("✓")
                              ? "text-[#00FF87]"
                              : line.msg.startsWith("✗")
                              ? "text-red-400"
                              : line.msg.includes("FAILED")
                              ? "text-red-400"
                              : line.msg.includes("improved")
                              ? "text-[#00FF87]"
                              : "text-gray-400"
                          }
                        >
                          {line.msg}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Error */}
              {jobStatus?.status === "failed" && jobStatus.error_message && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-4 text-sm text-red-400 flex gap-2">
                  <XCircle size={16} className="flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold mb-1">Training failed</div>
                    {jobStatus.error_message}
                  </div>
                </div>
              )}

              {/* ── Results (completed only) ── */}
              {jobStatus?.status === "completed" && (
                <>
                  {/* Summary banner */}
                  <div className="bg-[#00FF87]/5 border border-[#00FF87]/20 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-4">
                      <CheckCircle2 size={20} className="text-[#00FF87]" />
                      <div>
                        <div className="font-bold text-white">Training Complete</div>
                        <div className="text-xs text-gray-400">
                          {jobStatus.training_samples?.toLocaleString()} samples ·{" "}
                          {jobStatus.feature_count} features ·{" "}
                          {jobStatus.optimization_rounds} optimization rounds
                          {jobStatus.best_algorithm && (
                            <> · Best: <span className="text-[#00FF87]">{jobStatus.best_algorithm}</span></>
                          )}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="ml-auto flex items-center gap-2">
                        <button
                          onClick={() => setReOptOpen(!reOptOpen)}
                          className="flex items-center gap-2 border border-[#F59E0B]/30 text-[#F59E0B] hover:bg-[#F59E0B]/10 text-xs font-semibold px-3 py-2 rounded-xl transition-all"
                        >
                          <RefreshCw size={13} /> Re-Optimize
                          {reOptOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                        </button>

                        <button
                          onClick={handlePromote}
                          disabled={promoting || !!jobStatus.result_model_id}
                          className="flex items-center gap-2 bg-[#00FF87] hover:bg-[#00DD77] disabled:opacity-50 text-black font-bold text-xs px-4 py-2 rounded-xl transition-all"
                        >
                          {promoting
                            ? <><RefreshCw size={13} className="animate-spin" /> Promoting…</>
                            : <><ArrowUpCircle size={13} /> {jobStatus.result_model_id ? "Promoted ✓" : "Promote to Production"}</>
                          }
                        </button>
                      </div>
                    </div>

                    {promoteMsg && (
                      <div className={`text-xs mt-2 ${promoteMsg.startsWith("Error") ? "text-red-400" : "text-[#00FF87]"}`}>
                        {promoteMsg}
                      </div>
                    )}

                    {/* Re-optimize panel */}
                    {reOptOpen && (
                      <div className="mt-4 pt-4 border-t border-[#00FF87]/10 flex items-center gap-4">
                        <div className="text-sm text-gray-400">Expand data window to:</div>
                        <div className="flex gap-1.5">
                          {RE_WINDOW_OPTIONS.map((opt) => (
                            <button
                              key={opt.value}
                              onClick={() => setReOptWindow(opt.value)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                                reOptWindow === opt.value
                                  ? "border-[#F59E0B]/50 bg-[#F59E0B]/10 text-[#F59E0B]"
                                  : "border-[#2E2E3E] text-gray-500 hover:text-gray-300"
                              }`}
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                        <button
                          onClick={handleReOptimize}
                          disabled={reOpting}
                          className="flex items-center gap-2 bg-[#F59E0B] hover:bg-[#D97706] text-black font-bold text-xs px-4 py-2 rounded-xl transition-all disabled:opacity-50"
                        >
                          {reOpting
                            ? <><RefreshCw size={13} className="animate-spin" /> Starting…</>
                            : <><Play size={13} /> Run Re-Optimization</>
                          }
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Per-algorithm metrics table */}
                  {algoKeys.length > 0 && (
                    <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl overflow-hidden">
                      <div className="px-5 py-3.5 border-b border-[#1E1E2E] text-xs font-bold text-gray-400 uppercase tracking-wide">
                        Algorithm Results
                      </div>
                      <div className="divide-y divide-[#1E1E2E]">
                        {/* Ensemble first */}
                        {metrics.ensemble && Object.keys(metrics.ensemble).length > 0 && (
                          <MetricRow
                            name="Ensemble (Final)"
                            metrics={metrics.ensemble as Record<string, number>}
                            isBest
                            highlight
                          />
                        )}
                        {algoKeys.map((k) => (
                          <MetricRow
                            key={k}
                            name={k}
                            metrics={metrics[k] as Record<string, number>}
                            isBest={k === jobStatus.best_algorithm}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ── Metric row component ──────────────────────────────────────────────────────
function MetricRow({
  name,
  metrics,
  isBest = false,
  highlight = false,
}: {
  name: string;
  metrics: Record<string, number | string | Record<string, number>>;
  isBest?: boolean;
  highlight?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const numMetrics = Object.entries(metrics).filter(
    ([k, v]) => ["precision", "recall", "f1_score", "auc_roc"].includes(k) && typeof v === "number"
  );
  const hasExtra = Object.keys(metrics).some((k) =>
    !["precision", "recall", "f1_score", "auc_roc"].includes(k)
  );

  return (
    <div className={`px-5 py-4 ${highlight ? "bg-[#00FF87]/3" : ""}`}>
      <div className="flex items-center gap-4">
        <div className="w-44 flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold text-white font-mono">
              {name.replace(/_/g, " ")}
            </span>
            {isBest && !highlight && (
              <span className="text-[9px] bg-[#8B5CF6]/10 text-[#8B5CF6] px-1.5 py-0.5 rounded font-bold">
                BEST
              </span>
            )}
          </div>
          {(metrics.error as string) && (
            <div className="text-[10px] text-red-400">{metrics.error as string}</div>
          )}
        </div>

        {numMetrics.length > 0 ? (
          <div className="flex-1 grid grid-cols-4 gap-2">
            {["precision", "recall", "f1_score", "auc_roc"].map((key) => (
              <MetricCell
                key={key}
                label={key === "f1_score" ? "F1" : key === "auc_roc" ? "AUC-ROC" : key}
                value={typeof metrics[key] === "number" ? (metrics[key] as number) : undefined}
              />
            ))}
          </div>
        ) : (
          <div className="flex-1 text-xs text-gray-600 italic">
            {metrics.error ? "Training error" : "No label data — unsupervised score only"}
          </div>
        )}

        {hasExtra && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-600 hover:text-gray-300 transition-colors"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 ml-44 grid grid-cols-4 gap-2 text-xs">
          {Object.entries(metrics)
            .filter(([k]) => !["precision", "recall", "f1_score", "auc_roc", "error"].includes(k))
            .map(([k, v]) => (
              <div key={k} className="bg-[#0A0A0F] rounded-lg p-2">
                <div className="text-gray-600 text-[10px] capitalize">{k.replace(/_/g, " ")}</div>
                <div className="text-gray-300 font-mono text-xs mt-0.5">
                  {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
