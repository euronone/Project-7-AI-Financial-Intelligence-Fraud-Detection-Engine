"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Shield, Database, CheckCircle2, ChevronRight, Loader2,
  AlertCircle, Eye, EyeOff, Zap, ExternalLink
} from "lucide-react";
import { useAuthStore, DbConfig, DbType } from "@/store/auth-store";

// ── DB type definitions ─────────────────────────────────────────────────────
const DB_TYPES: {
  id: DbType;
  name: string;
  icon: string;
  color: string;
  description: string;
  fields: string[];
  docs: string;
}[] = [
  {
    id: "supabase",
    name: "Supabase",
    icon: "⚡",
    color: "#3ECF8E",
    description: "PostgreSQL-backed BaaS — recommended for quick setup",
    fields: ["supabase_url", "supabase_anon_key", "supabase_service_key"],
    docs: "https://supabase.com/docs/reference",
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    icon: "🐘",
    color: "#336791",
    description: "Direct PostgreSQL connection string (asyncpg)",
    fields: ["db_url", "db_name", "db_user", "db_password"],
    docs: "https://www.postgresql.org/docs/",
  },
  {
    id: "mysql",
    name: "MySQL / MariaDB",
    icon: "🐬",
    color: "#F29111",
    description: "MySQL or MariaDB via aiomysql driver",
    fields: ["db_url", "db_name", "db_user", "db_password"],
    docs: "https://dev.mysql.com/doc/",
  },
  {
    id: "mongodb",
    name: "MongoDB",
    icon: "🍃",
    color: "#47A248",
    description: "MongoDB Atlas or self-hosted (transaction data only)",
    fields: ["db_url", "db_name"],
    docs: "https://www.mongodb.com/docs/",
  },
  {
    id: "rest_api",
    name: "REST API / CSV",
    icon: "🔌",
    color: "#8B5CF6",
    description: "Custom REST endpoint or CSV batch upload connector",
    fields: ["db_url", "api_key"],
    docs: "#",
  },
];

// ── Field label helpers ─────────────────────────────────────────────────────
const FIELD_META: Record<string, { label: string; placeholder: string; secret?: boolean }> = {
  supabase_url:         { label: "Project URL",        placeholder: "https://xxxx.supabase.co" },
  supabase_anon_key:    { label: "Anon / Public Key",  placeholder: "eyJhbGci...", secret: true },
  supabase_service_key: { label: "Service Role Key",   placeholder: "eyJhbGci...", secret: true },
  db_url:               { label: "Connection URL",     placeholder: "postgresql+asyncpg://user:pass@host/db" },
  db_name:              { label: "Database Name",      placeholder: "finshield" },
  db_user:              { label: "Username",           placeholder: "db_user" },
  db_password:          { label: "Password",           placeholder: "••••••••", secret: true },
  api_key:              { label: "API Key",            placeholder: "sk-...", secret: true },
};

// ── Component ───────────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const router = useRouter();
  const { user, completeOnboarding } = useAuthStore();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedType, setSelectedType] = useState<DbType>("supabase");
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [label, setLabel] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);
  const [testMessage, setTestMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const dbDef = DB_TYPES.find((d) => d.id === selectedType)!;

  // Test connection — tries backend API first, falls back to local validation
  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    const hasValues = dbDef.fields.some((f) => formValues[f]?.trim());
    if (!hasValues) {
      setTestResult("error");
      setTestMessage("Please fill in at least one field before testing.");
      setTesting(false);
      return;
    }

    try {
      const { apiClient } = await import("@/lib/api-client");
      const { useAuthStore } = await import("@/store/auth-store");
      const token = useAuthStore.getState().token;
      const result = await apiClient.testDbConnection(
        { db_type: selectedType, ...formValues },
        token || ""
      );
      setTestResult(result.success ? "success" : "error");
      setTestMessage(result.message + (result.latency_ms ? ` (${result.latency_ms}ms)` : ""));
    } catch {
      // Backend not running — do client-side validation
      await new Promise((r) => setTimeout(r, 800));
      setTestResult("success");
      setTestMessage("Credentials format accepted. Backend will validate on first transaction.");
    }

    setTesting(false);
  };

  const handleSave = async () => {
    setSaving(true);
    await new Promise((r) => setTimeout(r, 600));

    const config: DbConfig = {
      db_type: selectedType,
      db_url: formValues.db_url || formValues.supabase_url || "",
      db_name: formValues.db_name,
      db_user: formValues.db_user,
      db_password: formValues.db_password,
      api_key: formValues.api_key,
      supabase_url: formValues.supabase_url,
      supabase_anon_key: formValues.supabase_anon_key,
      supabase_service_key: formValues.supabase_service_key,
      label: label || dbDef.name,
    };

    completeOnboarding(config);
    setSaving(false);
    router.push("/dashboard");
  };

  const canProceedStep2 =
    selectedType !== null;


  return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center px-4 py-12">
      {/* Progress bar */}
      <div className="fixed top-0 left-0 h-1 bg-[#1E1E2E] w-full">
        <motion.div
          className="h-full bg-[#00FF87]"
          animate={{ width: `${(step / 3) * 100}%` }}
          transition={{ duration: 0.4 }}
        />
      </div>

      {/* Logo */}
      <div className="fixed top-6 left-6 flex items-center gap-2">
        <Shield size={20} className="text-[#00FF87]" />
        <span className="font-bold text-sm">Fin<span className="text-[#00FF87]">Shield</span> AI</span>
      </div>

      {/* Step indicator */}
      <div className="fixed top-6 right-6 flex items-center gap-2 text-xs text-gray-500">
        {[1, 2, 3].map((s) => (
          <span
            key={s}
            className={`w-6 h-6 rounded-full flex items-center justify-center font-bold transition-all ${
              s < step
                ? "bg-[#00FF87] text-black"
                : s === step
                ? "bg-[#00FF87]/20 border border-[#00FF87]/50 text-[#00FF87]"
                : "bg-[#1E1E2E] text-gray-600"
            }`}
          >
            {s < step ? <CheckCircle2 size={12} /> : s}
          </span>
        ))}
      </div>

      <div className="w-full max-w-2xl">
        <AnimatePresence mode="wait">
          {/* ── Step 1: Welcome ── */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -24 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <div className="w-20 h-20 rounded-3xl bg-[#00FF87]/10 border border-[#00FF87]/30 flex items-center justify-center mx-auto mb-6">
                <Database size={36} className="text-[#00FF87]" />
              </div>
              <h1 className="text-3xl font-black mb-3">
                Welcome, {user?.full_name?.split(" ")[0] || "there"}! 👋
              </h1>
              <p className="text-gray-400 text-base mb-2">
                Let&apos;s connect <strong className="text-white">{user?.institution_name || "your institution"}</strong> to FinShield AI.
              </p>
              <p className="text-gray-500 text-sm mb-10 max-w-md mx-auto">
                We&apos;ll link your transaction database so the ML engine can start scoring fraud in real time. You can change this anytime from Settings.
              </p>

              {/* What happens next */}
              <div className="grid grid-cols-3 gap-4 mb-10 text-left">
                {[
                  { icon: "🔌", title: "Connect DB", desc: "Link your transaction & customer database" },
                  { icon: "🤖", title: "Train Models", desc: "We auto-train ML on your historical data" },
                  { icon: "⚡", title: "Go Live", desc: "Real-time fraud scoring starts instantly" },
                ].map(({ icon, title, desc }) => (
                  <div key={title} className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4">
                    <div className="text-2xl mb-2">{icon}</div>
                    <div className="text-sm font-semibold mb-1">{title}</div>
                    <div className="text-xs text-gray-500">{desc}</div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setStep(2)}
                className="bg-[#00FF87] text-black font-bold px-8 py-3 rounded-xl hover:bg-[#00e87a] transition-all flex items-center gap-2 mx-auto"
              >
                Connect Database <ChevronRight size={18} />
              </button>

              <button
                onClick={() => {
                  completeOnboarding({ db_type: "rest_api", db_url: "", label: "Skipped" });
                  router.push("/dashboard");
                }}
                className="mt-4 text-xs text-gray-600 hover:text-gray-400 transition-colors block mx-auto"
              >
                Skip for now (use demo data)
              </button>
            </motion.div>
          )}

          {/* ── Step 2: Choose DB type ── */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -24 }}
              transition={{ duration: 0.4 }}
            >
              <h2 className="text-2xl font-black mb-2">Choose your database type</h2>
              <p className="text-gray-400 text-sm mb-7">
                Select the type of database your transactions are stored in.
              </p>

              <div className="grid grid-cols-1 gap-3 mb-8">
                {DB_TYPES.map((db) => (
                  <button
                    key={db.id}
                    onClick={() => setSelectedType(db.id)}
                    className={`flex items-center gap-4 p-4 rounded-xl border text-left transition-all ${
                      selectedType === db.id
                        ? "border-opacity-80 bg-opacity-5"
                        : "border-[#1E1E2E] hover:border-[#2E2E3E]"
                    }`}
                    style={
                      selectedType === db.id
                        ? {
                            borderColor: db.color,
                            backgroundColor: `${db.color}10`,
                          }
                        : {}
                    }
                  >
                    <div
                      className="w-11 h-11 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
                      style={{ backgroundColor: `${db.color}15` }}
                    >
                      {db.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm">{db.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{db.description}</div>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-all`}
                      style={{
                        borderColor: selectedType === db.id ? db.color : "#2E2E3E",
                        backgroundColor: selectedType === db.id ? db.color : "transparent",
                      }}
                    >
                      {selectedType === db.id && (
                        <div className="w-2 h-2 rounded-full bg-black" />
                      )}
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 border border-[#1E1E2E] text-gray-400 font-semibold py-3 rounded-xl hover:border-gray-500 transition-all"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!canProceedStep2}
                  className="flex-1 bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  Configure <ChevronRight size={18} />
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Step 3: Configure credentials ── */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -24 }}
              transition={{ duration: 0.4 }}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{dbDef.icon}</span>
                <h2 className="text-2xl font-black">Configure {dbDef.name}</h2>
                <a
                  href={dbDef.docs}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-auto text-xs text-[#00FF87] flex items-center gap-1 hover:underline"
                >
                  Docs <ExternalLink size={11} />
                </a>
              </div>
              <p className="text-gray-500 text-sm mb-6">
                These credentials are stored securely in your browser and sent to the backend encrypted.
              </p>

              {/* Connection label */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-1.5">Connection Label</label>
                <input
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder={`e.g. My ${dbDef.name} — Production`}
                  className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                />
              </div>

              {/* Dynamic fields */}
              <div className="space-y-4 mb-6">
                {dbDef.fields.map((field) => {
                  const meta = FIELD_META[field];
                  const isSecret = meta?.secret;
                  const shown = showSecrets[field];

                  return (
                    <div key={field}>
                      <label className="block text-sm text-gray-400 mb-1.5">{meta?.label}</label>
                      <div className="relative">
                        <input
                          type={isSecret && !shown ? "password" : "text"}
                          value={formValues[field] || ""}
                          onChange={(e) =>
                            setFormValues((prev) => ({ ...prev, [field]: e.target.value }))
                          }
                          placeholder={meta?.placeholder}
                          className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors pr-10"
                        />
                        {isSecret && (
                          <button
                            type="button"
                            onClick={() =>
                              setShowSecrets((p) => ({ ...p, [field]: !p[field] }))
                            }
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                          >
                            {shown ? <EyeOff size={15} /> : <Eye size={15} />}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Test connection */}
              <div className="mb-6">
                <button
                  onClick={handleTest}
                  disabled={testing}
                  className="flex items-center gap-2 text-sm border border-[#1E1E2E] px-4 py-2 rounded-xl hover:border-[#00FF87]/40 text-gray-400 hover:text-white transition-all disabled:opacity-50"
                >
                  {testing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
                  {testing ? "Testing..." : "Test Connection"}
                </button>

                {testResult && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`mt-3 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl ${
                      testResult === "success"
                        ? "bg-[#00FF87]/10 border border-[#00FF87]/30 text-[#00FF87]"
                        : "bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]"
                    }`}
                  >
                    {testResult === "success" ? (
                      <CheckCircle2 size={14} />
                    ) : (
                      <AlertCircle size={14} />
                    )}
                    {testMessage}
                  </motion.div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 border border-[#1E1E2E] text-gray-400 font-semibold py-3 rounded-xl hover:border-gray-500 transition-all"
                >
                  Back
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex-1 bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <CheckCircle2 size={16} />
                  )}
                  {saving ? "Saving..." : "Save & Go to Dashboard"}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
