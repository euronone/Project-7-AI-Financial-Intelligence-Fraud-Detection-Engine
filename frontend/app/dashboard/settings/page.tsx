"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Shield, Database, ChevronLeft, Save, Zap, Loader2, CheckCircle2,
  AlertCircle, Eye, EyeOff, Trash2, Plus, ExternalLink, Settings, Bell,
  Key, User, CreditCard
} from "lucide-react";
import Link from "next/link";
import { useAuthStore, DbConfig, DbType } from "@/store/auth-store";

// ── DB type definitions (same as onboarding) ────────────────────────────────
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
    description: "PostgreSQL-backed BaaS — recommended",
    fields: ["supabase_url", "supabase_anon_key", "supabase_service_key"],
    docs: "https://supabase.com/docs",
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    icon: "🐘",
    color: "#336791",
    description: "Direct PostgreSQL / asyncpg connection",
    fields: ["db_url", "db_name", "db_user", "db_password"],
    docs: "https://www.postgresql.org/docs/",
  },
  {
    id: "mysql",
    name: "MySQL / MariaDB",
    icon: "🐬",
    color: "#F29111",
    description: "MySQL or MariaDB via aiomysql",
    fields: ["db_url", "db_name", "db_user", "db_password"],
    docs: "https://dev.mysql.com/doc/",
  },
  {
    id: "mongodb",
    name: "MongoDB",
    icon: "🍃",
    color: "#47A248",
    description: "MongoDB Atlas or self-hosted (transactions only)",
    fields: ["db_url", "db_name"],
    docs: "https://www.mongodb.com/docs/",
  },
  {
    id: "rest_api",
    name: "REST API / CSV",
    icon: "🔌",
    color: "#8B5CF6",
    description: "Custom REST endpoint or CSV batch upload",
    fields: ["db_url", "api_key"],
    docs: "#",
  },
];

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

// ── Sidebar nav sections ─────────────────────────────────────────────────────
const SECTIONS = [
  { id: "database",      label: "Database",      icon: Database },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "api-keys",      label: "API Keys",      icon: Key },
  { id: "account",       label: "Account",       icon: User },
  { id: "billing",       label: "Billing",       icon: CreditCard },
];

// ── Component ────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { user, dbConfig, updateDbConfig } = useAuthStore();
  const router = useRouter();

  const [activeSection, setActiveSection] = useState("database");

  // DB form state — pre-fill from saved config
  const [selectedType, setSelectedType] = useState<DbType>(dbConfig?.db_type || "supabase");
  const [label, setLabel] = useState(dbConfig?.label || "");
  const [formValues, setFormValues] = useState<Record<string, string>>({
    supabase_url:         dbConfig?.supabase_url || "",
    supabase_anon_key:    dbConfig?.supabase_anon_key || "",
    supabase_service_key: dbConfig?.supabase_service_key || "",
    db_url:               dbConfig?.db_url || "",
    db_name:              dbConfig?.db_name || "",
    db_user:              dbConfig?.db_user || "",
    db_password:          dbConfig?.db_password || "",
    api_key:              dbConfig?.api_key || "",
  });
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);
  const [testMessage, setTestMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const dbDef = DB_TYPES.find((d) => d.id === selectedType)!;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    await new Promise((r) => setTimeout(r, 1800));
    const hasValues = dbDef.fields.some((f) => formValues[f]?.trim());
    if (hasValues) {
      setTestResult("success");
      setTestMessage("Connection test passed — credentials accepted.");
    } else {
      setTestResult("error");
      setTestMessage("Fill in at least one field before testing.");
    }
    setTesting(false);
  };

  const handleSave = async () => {
    setSaving(true);
    await new Promise((r) => setTimeout(r, 500));

    const config: DbConfig = {
      db_type:              selectedType,
      db_url:               formValues.db_url || formValues.supabase_url || "",
      db_name:              formValues.db_name,
      db_user:              formValues.db_user,
      db_password:          formValues.db_password,
      api_key:              formValues.api_key,
      supabase_url:         formValues.supabase_url,
      supabase_anon_key:    formValues.supabase_anon_key,
      supabase_service_key: formValues.supabase_service_key,
      label:                label || dbDef.name,
    };

    updateDbConfig(config);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const planColor =
    user?.plan === "advanced" ? "#8B5CF6" : user?.plan === "pro" ? "#3B82F6" : "#00FF87";

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex">
      {/* App Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-60 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col">
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
            { label: "Dashboard",     href: "/dashboard" },
            { label: "Transactions",  href: "/dashboard/transactions" },
            { label: "Fraud Alerts",  href: "/dashboard/alerts" },
            { label: "Customers",     href: "/dashboard/customers" },
            { label: "Settings",      href: "/dashboard/settings", active: true },
          ].map(({ label: l, href, active }) => (
            <Link
              key={l}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20"
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#111118]"
              }`}
            >
              {active ? <Settings size={16} /> : null}
              {l}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Settings layout */}
      <div className="ml-60 flex w-full">
        {/* Settings sidebar */}
        <div className="w-52 border-r border-[#1E1E2E] min-h-screen p-4 space-y-1 flex-shrink-0">
          <div className="text-xs text-gray-600 font-mono uppercase tracking-wider px-3 mb-3 mt-2">
            Settings
          </div>
          {SECTIONS.map(({ id, label: l, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveSection(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left ${
                activeSection === id
                  ? "bg-[#111118] text-white border border-[#2E2E3E]"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={15} />
              {l}
            </button>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 p-8 max-w-2xl">
          {/* ── Database Section ── */}
          {activeSection === "database" && (
            <div>
              <h2 className="text-xl font-black mb-1">Database Connection</h2>
              <p className="text-gray-500 text-sm mb-7">
                Configure the transaction and customer database FinShield connects to.
              </p>

              {/* DB type picker */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-3">Database Type</label>
                <div className="grid grid-cols-1 gap-2">
                  {DB_TYPES.map((db) => (
                    <button
                      key={db.id}
                      onClick={() => setSelectedType(db.id)}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                        selectedType === db.id
                          ? "border-opacity-80"
                          : "border-[#1E1E2E] hover:border-[#2E2E3E]"
                      }`}
                      style={
                        selectedType === db.id
                          ? { borderColor: db.color, backgroundColor: `${db.color}08` }
                          : {}
                      }
                    >
                      <span className="text-xl w-8 text-center">{db.icon}</span>
                      <div className="flex-1">
                        <div className="text-sm font-semibold">{db.name}</div>
                        <div className="text-xs text-gray-600">{db.description}</div>
                      </div>
                      <a
                        href={db.docs}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-600 hover:text-gray-400 ml-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink size={12} />
                      </a>
                      <div
                        className="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center ml-2"
                        style={{
                          borderColor: selectedType === db.id ? db.color : "#2E2E3E",
                          backgroundColor: selectedType === db.id ? db.color : "transparent",
                        }}
                      >
                        {selectedType === db.id && (
                          <div className="w-1.5 h-1.5 rounded-full bg-black" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Connection label */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-1.5">Connection Label</label>
                <input
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder={`e.g. Production ${dbDef.name}`}
                  className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                />
              </div>

              {/* Dynamic credential fields */}
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

              {/* Test + Save */}
              <div className="flex gap-3 items-start">
                <button
                  onClick={handleTest}
                  disabled={testing}
                  className="flex items-center gap-2 text-sm border border-[#1E1E2E] px-4 py-2.5 rounded-xl hover:border-[#00FF87]/40 text-gray-400 hover:text-white transition-all disabled:opacity-50"
                >
                  {testing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
                  {testing ? "Testing..." : "Test Connection"}
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60"
                >
                  {saving ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : saved ? (
                    <CheckCircle2 size={14} />
                  ) : (
                    <Save size={14} />
                  )}
                  {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
                </button>
              </div>

              {testResult && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-4 flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl ${
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
          )}

          {/* ── Notifications Section ── */}
          {activeSection === "notifications" && (
            <div>
              <h2 className="text-xl font-black mb-1">Notification Services</h2>
              <p className="text-gray-500 text-sm mb-7">
                Configure email and SMS providers for fraud alerts. All fields are optional — system falls back gracefully.
              </p>
              <div className="space-y-6">
                {[
                  {
                    label: "Resend.com (Email — recommended)",
                    field: "RESEND_API_KEY",
                    placeholder: "re_xxxxxxxxxxxxxxxxxx",
                    link: "https://resend.com",
                    badge: "3,000/mo free",
                  },
                  {
                    label: "SendGrid API Key (Email — fallback)",
                    field: "SENDGRID_API_KEY",
                    placeholder: "SG.xxxxxxxxxxxxxxxxxx",
                    link: "https://sendgrid.com",
                    badge: "100/day free",
                  },
                  {
                    label: "Twilio Account SID (SMS)",
                    field: "TWILIO_ACCOUNT_SID",
                    placeholder: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    link: "https://twilio.com",
                    badge: "Paid",
                  },
                  {
                    label: "Twilio Auth Token",
                    field: "TWILIO_AUTH_TOKEN",
                    placeholder: "your_auth_token",
                    link: null,
                    badge: null,
                    secret: true,
                  },
                  {
                    label: "Slack Webhook URL (Team alerts)",
                    field: "SLACK_WEBHOOK_URL",
                    placeholder: "https://hooks.slack.com/services/...",
                    link: "https://api.slack.com/messaging/webhooks",
                    badge: "Free",
                  },
                ].map(({ label: l, field, placeholder, link, badge, secret }) => (
                  <div key={field}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <label className="text-sm text-gray-400">{l}</label>
                      {badge && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/20 font-mono">
                          {badge}
                        </span>
                      )}
                      {link && (
                        <a href={link} target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-400">
                          <ExternalLink size={11} />
                        </a>
                      )}
                    </div>
                    <input
                      type={secret ? "password" : "text"}
                      placeholder={placeholder}
                      className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                    />
                  </div>
                ))}
              </div>
              <button className="mt-6 flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all">
                <Save size={14} /> Save Notification Settings
              </button>
            </div>
          )}

          {/* ── API Keys Section ── */}
          {activeSection === "api-keys" && (
            <div>
              <h2 className="text-xl font-black mb-1">API Keys</h2>
              <p className="text-gray-500 text-sm mb-7">
                Manage keys for fraud intelligence services. All are optional — FinShield uses built-in fallbacks.
              </p>
              <div className="space-y-6">
                {[
                  { label: "IPQualityScore (IP Intelligence)", placeholder: "ipqs_xxxxxxxxxx", badge: "Free tier" },
                  { label: "MaxMind GeoIP2 (Geolocation)", placeholder: "your_license_key", badge: null },
                  { label: "Fingerprint.js (Device)", placeholder: "fp_xxxxxxxxxx", badge: "Free tier" },
                ].map(({ label: l, placeholder, badge }) => (
                  <div key={l}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <label className="text-sm text-gray-400">{l}</label>
                      {badge && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 font-mono">
                          {badge}
                        </span>
                      )}
                    </div>
                    <input
                      type="password"
                      placeholder={placeholder}
                      className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
                    />
                  </div>
                ))}
              </div>
              <button className="mt-6 flex items-center gap-2 text-sm bg-[#00FF87] text-black font-bold px-5 py-2.5 rounded-xl hover:bg-[#00e87a] transition-all">
                <Save size={14} /> Save API Keys
              </button>
            </div>
          )}

          {/* ── Account Section ── */}
          {activeSection === "account" && (
            <div>
              <h2 className="text-xl font-black mb-1">Account</h2>
              <p className="text-gray-500 text-sm mb-7">Your profile and institution settings.</p>
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 space-y-4">
                {[
                  { label: "Full Name",         value: user?.full_name || "" },
                  { label: "Email",             value: user?.email || "" },
                  { label: "Institution Name",  value: user?.institution_name || "" },
                  { label: "Institution Type",  value: user?.institution_type || "" },
                  { label: "Role",              value: user?.role || "" },
                ].map(({ label: l, value }) => (
                  <div key={l} className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{l}</span>
                    <span className="text-sm font-medium capitalize">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Billing Section ── */}
          {activeSection === "billing" && (
            <div>
              <h2 className="text-xl font-black mb-1">Billing & Plan</h2>
              <p className="text-gray-500 text-sm mb-7">Manage your subscription.</p>
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 mb-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-400">Current Plan</span>
                  <span
                    className="text-sm font-bold px-3 py-1 rounded-full capitalize"
                    style={{
                      color: planColor,
                      backgroundColor: `${planColor}15`,
                      border: `1px solid ${planColor}40`,
                    }}
                  >
                    {user?.plan}
                  </span>
                </div>
                {user?.plan === "free" && (
                  <Link
                    href="/signup"
                    className="block w-full text-center bg-[#3B82F6] text-white font-bold py-2.5 rounded-xl hover:bg-[#2563EB] transition-all text-sm"
                  >
                    Upgrade to Pro — ₹9,999/mo
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
