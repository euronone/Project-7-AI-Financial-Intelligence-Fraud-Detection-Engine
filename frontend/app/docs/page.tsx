"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Shield, ChevronRight, Code2, Zap, Database, Bell,
  Users, Lock, Brain, GitBranch, AlertTriangle, CheckCircle2,
  BookOpen, Layers, Globe, CreditCard, BarChart3,
  MessageSquare, Webhook, RefreshCw, Menu, X, ExternalLink,
  Activity, Server, Cpu, Mail, Phone,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

interface DocSection {
  id: string;
  label: string;
  icon: React.ReactNode;
  subsections?: { id: string; label: string }[];
}

// ── Sidebar navigation ───────────────────────────────────────────────────────

const SECTIONS: DocSection[] = [
  { id: "introduction",    label: "Introduction",          icon: <BookOpen size={14} /> },
  { id: "who-is-it-for",  label: "Who Is It For?",        icon: <Users size={14} /> },
  { id: "quickstart",     label: "Quick Start",           icon: <Zap size={14} />,
    subsections: [
      { id: "step-signup",    label: "1. Sign Up" },
      { id: "step-connect",   label: "2. Connect Data" },
      { id: "step-train",     label: "3. Train Models" },
      { id: "step-score",     label: "4. Real-Time Scoring" },
      { id: "step-alerts",    label: "5. Alerts" },
    ],
  },
  { id: "features",        label: "Platform Features",    icon: <Layers size={14} /> },
  { id: "service-flow",    label: "Service Flow",         icon: <GitBranch size={14} /> },
  { id: "fraud-detection", label: "Fraud Detection",      icon: <Brain size={14} />,
    subsections: [
      { id: "fd-rules",    label: "Rules Engine" },
      { id: "fd-ml",       label: "ML Models" },
      { id: "fd-scoring",  label: "Scoring & Decisions" },
      { id: "fd-shap",     label: "Explainability (SHAP)" },
    ],
  },
  { id: "api-reference",   label: "API Reference",        icon: <Code2 size={14} />,
    subsections: [
      { id: "api-auth",          label: "Authentication" },
      { id: "api-transactions",  label: "Transactions" },
      { id: "api-alerts",        label: "Fraud Alerts" },
      { id: "api-customers",     label: "Customers" },
      { id: "api-analytics",     label: "Analytics" },
      { id: "api-settings",      label: "Settings" },
      { id: "api-models",        label: "ML Models" },
      { id: "api-rules",         label: "Rules" },
      { id: "api-websocket",     label: "WebSocket Events" },
    ],
  },
  { id: "integrations",    label: "Data Connectors",      icon: <Database size={14} /> },
  { id: "notifications",   label: "Notifications",        icon: <Bell size={14} /> },
  { id: "plans",           label: "Subscription Plans",   icon: <CreditCard size={14} /> },
  { id: "security",        label: "Security & Compliance",icon: <Lock size={14} /> },
];

// ── Reusable components ───────────────────────────────────────────────────────

function SectionAnchor({ id }: { id: string }) {
  return <span id={id} className="block" style={{ scrollMarginTop: "80px" }} />;
}

function SectionTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-black text-white">{children}</h2>
      {sub && <p className="text-gray-400 text-sm mt-1">{sub}</p>}
    </div>
  );
}

function SubTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-bold text-white mt-8 mb-3">{children}</h3>;
}

function InfoBox({ children, type = "info" }: { children: React.ReactNode; type?: "info" | "warn" | "tip" }) {
  const styles = {
    info: "bg-[#3B82F6]/08 border-[#3B82F6]/30 text-[#3B82F6]",
    warn: "bg-[#F59E0B]/08 border-[#F59E0B]/30 text-[#F59E0B]",
    tip:  "bg-[#00FF87]/08 border-[#00FF87]/30 text-[#00FF87]",
  };
  const icons = { info: <AlertTriangle size={14} />, warn: <AlertTriangle size={14} />, tip: <CheckCircle2 size={14} /> };
  return (
    <div className={`border rounded-xl px-4 py-3 my-4 flex gap-3 text-sm ${styles[type]}`}>
      <span className="mt-0.5 shrink-0">{icons[type]}</span>
      <div className="text-gray-300">{children}</div>
    </div>
  );
}

function CodeBlock({ code, lang = "bash" }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="relative my-4 rounded-xl overflow-hidden border border-[#1E1E2E]">
      <div className="flex items-center justify-between bg-[#0D0D15] px-4 py-2 border-b border-[#1E1E2E]">
        <span className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">{lang}</span>
        <button
          onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
          className="text-[11px] text-gray-500 hover:text-white transition-colors"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="bg-[#07070D] p-4 overflow-x-auto text-sm text-gray-300 font-mono leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function EndpointBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET:    "bg-[#3B82F6]/15 text-[#3B82F6] border-[#3B82F6]/30",
    POST:   "bg-[#00FF87]/15 text-[#00FF87] border-[#00FF87]/30",
    PUT:    "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30",
    DELETE: "bg-[#EF4444]/15 text-[#EF4444] border-[#EF4444]/30",
    WS:     "bg-[#8B5CF6]/15 text-[#8B5CF6] border-[#8B5CF6]/30",
  };
  return (
    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${colors[method] ?? "bg-gray-800 text-gray-400 border-gray-600"}`}>
      {method}
    </span>
  );
}

function Endpoint({ method, path, description, auth = true }: { method: string; path: string; description: string; auth?: boolean }) {
  return (
    <div className="border border-[#1E1E2E] rounded-xl px-4 py-3 mb-2 hover:border-[#2E2E3E] transition-colors">
      <div className="flex items-center gap-3 mb-1">
        <EndpointBadge method={method} />
        <code className="text-sm text-gray-200 font-mono">{path}</code>
        {auth && <span className="text-[10px] text-gray-600 ml-auto flex items-center gap-1"><Lock size={9} /> JWT</span>}
      </div>
      <p className="text-xs text-gray-500 ml-1">{description}</p>
    </div>
  );
}

function PlanBadge({ plan }: { plan: "free" | "pro" | "advanced" }) {
  const styles = {
    free:     "bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/20",
    pro:      "bg-[#3B82F6]/10 text-[#3B82F6] border-[#3B82F6]/20",
    advanced: "bg-[#8B5CF6]/10 text-[#8B5CF6] border-[#8B5CF6]/20",
  };
  return (
    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border capitalize ${styles[plan]}`}>
      {plan}
    </span>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DocsPage() {
  const [activeId, setActiveId] = useState("introduction");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // Highlight active section on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveId(entry.target.id);
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    document.querySelectorAll("[id]").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      {/* ── Top bar ── */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0A0A0F]/95 backdrop-blur border-b border-[#1E1E2E] flex items-center justify-between px-6 h-14">
        <div className="flex items-center gap-4">
          <button className="md:hidden text-gray-400 hover:text-white" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <Link href="/" className="flex items-center gap-2">
            <Shield size={18} className="text-[#00FF87]" />
            <span className="font-bold text-sm">Fin<span className="text-[#00FF87]">Shield</span> AI</span>
          </Link>
          <span className="text-gray-600 text-xs hidden sm:block">/ Documentation</span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") ?? "http://localhost:8003"}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors border border-[#1E1E2E] px-3 py-1.5 rounded-lg"
          >
            <Code2 size={12} /> Swagger UI <ExternalLink size={10} />
          </a>
          <Link href="/signup" className="text-xs bg-[#00FF87] text-black font-bold px-4 py-1.5 rounded-lg hover:bg-[#00e87a] transition-colors">
            Get Started Free
          </Link>
        </div>
      </header>

      <div className="flex pt-14">
        {/* ── Left sidebar ── */}
        <aside className={`fixed md:sticky top-14 left-0 z-40 h-[calc(100vh-56px)] w-64 bg-[#0A0A0F] border-r border-[#1E1E2E] overflow-y-auto transition-transform duration-200 ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
          <nav className="px-4 py-6 space-y-0.5">
            {SECTIONS.map((sec) => (
              <div key={sec.id}>
                <button
                  onClick={() => scrollTo(sec.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors text-left ${
                    activeId === sec.id
                      ? "bg-[#00FF87]/10 text-[#00FF87] font-semibold"
                      : "text-gray-400 hover:text-white hover:bg-[#111118]"
                  }`}
                >
                  {sec.icon}
                  {sec.label}
                </button>
                {sec.subsections?.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => scrollTo(sub.id)}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 ml-5 rounded-lg text-xs transition-colors text-left ${
                      activeId === sub.id
                        ? "text-[#00FF87] font-semibold"
                        : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    <ChevronRight size={10} />
                    {sub.label}
                  </button>
                ))}
              </div>
            ))}
          </nav>
        </aside>

        {/* Mobile overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* ── Main content ── */}
        <main ref={contentRef} className="flex-1 min-w-0 px-6 md:px-12 lg:px-16 py-10 max-w-4xl">

          {/* ═══════════════════════════════════════════════════════ INTRODUCTION */}
          <SectionAnchor id="introduction" />
          <SectionTitle sub="Complete developer reference for FinShield AI">
            FinShield AI — Documentation
          </SectionTitle>

          <p className="text-gray-400 leading-relaxed mb-4">
            <strong className="text-white">FinShield AI</strong> is an end-to-end, multi-tenant fraud detection platform for financial institutions. It connects to your existing customer and transaction databases, trains ML models on your historical data, and provides real-time fraud scoring, multi-channel alerting, and a full investigation dashboard — all without building ML infrastructure.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-6">
            {[
              { label: "Avg Inference", value: "<18ms",   color: "#00FF87" },
              { label: "Accuracy",      value: "96.4%",   color: "#3B82F6" },
              { label: "ML Models",     value: "5-layer", color: "#8B5CF6" },
              { label: "Connectors",    value: "20+",     color: "#F59E0B" },
            ].map((m) => (
              <div key={m.label} className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4 text-center">
                <div className="text-xl font-black" style={{ color: m.color }}>{m.value}</div>
                <div className="text-xs text-gray-500 mt-1">{m.label}</div>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ WHO IS IT FOR */}
          <SectionAnchor id="who-is-it-for" />
          <SectionTitle sub="FinShield AI is purpose-built for financial institutions of all sizes">
            Who Is It For?
          </SectionTitle>

          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {[
              {
                icon: "🏦", title: "Banks & Credit Unions",
                uses: ["Card-not-present fraud", "Account takeover detection", "Impossible travel alerts", "AML pattern detection"],
                color: "#3B82F6",
              },
              {
                icon: "🚀", title: "Fintech Startups",
                uses: ["Add fraud detection without building ML infra", "Real-time scoring via REST API", "Plug into existing payment flows", "Get production-ready in hours"],
                color: "#00FF87",
              },
              {
                icon: "🏥", title: "Insurance Companies",
                uses: ["Claim fraud from spending pattern changes", "Identity fraud detection", "Velocity pattern analysis", "Behavioral anomaly scoring"],
                color: "#8B5CF6",
              },
              {
                icon: "💳", title: "Payment Processors",
                uses: ["Screen every transaction before settlement", "Block fraud pre-authorization", "Webhook integration with existing gateway", "Sub-100ms scoring"],
                color: "#F59E0B",
              },
            ].map((card) => (
              <div key={card.title} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">{card.icon}</span>
                  <h3 className="font-bold text-white">{card.title}</h3>
                </div>
                <ul className="space-y-1.5">
                  {card.uses.map((u) => (
                    <li key={u} className="flex items-start gap-2 text-sm text-gray-400">
                      <CheckCircle2 size={13} className="mt-0.5 shrink-0" style={{ color: card.color }} />
                      {u}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ QUICK START */}
          <SectionAnchor id="quickstart" />
          <SectionTitle sub="From zero to live fraud detection in under 30 minutes">
            Quick Start
          </SectionTitle>

          <SectionAnchor id="step-signup" />
          <SubTitle>Step 1 — Sign Up & Choose a Plan</SubTitle>
          <p className="text-sm text-gray-400 mb-3">Create your institution account and select a subscription plan. The Free plan lets you start immediately with no credit card required.</p>
          <CodeBlock lang="http" code={`POST https://your-api/api/v1/auth/signup

{
  "organization_name": "Acme Bank",
  "institution_type": "bank",
  "email": "admin@acmebank.com",
  "password": "SecurePass123!",
  "subscription_plan": "free"   // "free" | "pro" | "advanced"
}`} />

          <SectionAnchor id="step-connect" />
          <SubTitle>Step 2 — Connect Your Database</SubTitle>
          <p className="text-sm text-gray-400 mb-3">Provide credentials for your customer and transaction databases. FinShield supports Supabase, PostgreSQL, MySQL, MongoDB, and 15+ more.</p>
          <CodeBlock lang="http" code={`PUT https://your-api/api/v1/settings/database

Authorization: Bearer <access_token>

{
  "db_type": "supabase",
  "supabase_url": "https://xyzabc.supabase.co",
  "supabase_anon_key": "eyJhbGci...",
  "supabase_service_key": "eyJhbGci..."
}`} />
          <InfoBox type="tip">You can test your connection before saving: <code className="font-mono text-xs">POST /api/v1/settings/test-connection</code></InfoBox>

          <SectionAnchor id="step-train" />
          <SubTitle>Step 3 — First-Run Model Training</SubTitle>
          <p className="text-sm text-gray-400 mb-3">FinShield pulls up to 90 days of historical transactions, trains 5 ML models, and writes <code className="font-mono text-xs text-gray-300">fraud_score</code>, <code className="font-mono text-xs text-gray-300">fraud_category</code>, and <code className="font-mono text-xs text-gray-300">fraud_risk_level</code> columns back into your transactions table.</p>
          <CodeBlock lang="bash" code={`# Columns automatically added to your transactions table:
fraud_score          DECIMAL(5,4)   -- 0.0 to 1.0 probability
fraud_category       VARCHAR(20)    -- legitimate | suspicious | fraudulent | unscored
fraud_risk_level     VARCHAR(10)    -- low | medium | high | critical
fraud_model_version  VARCHAR(50)    -- e.g. "ensemble_v1"
fraud_triggered_rules JSONB         -- which rules fired
fraud_scored_at      TIMESTAMPTZ`} />

          <SectionAnchor id="step-score" />
          <SubTitle>Step 4 — Submit Transactions for Real-Time Scoring</SubTitle>
          <p className="text-sm text-gray-400 mb-3">POST any transaction to the scoring endpoint. The response includes the fraud score, decision, and SHAP explanation in under 100ms.</p>
          <CodeBlock lang="http" code={`POST /api/v1/transactions

{
  "customer_id": "cust-uuid-here",
  "amount": 45000.00,
  "currency": "INR",
  "transaction_type": "purchase",
  "channel": "online",
  "merchant_name": "Amazon",
  "merchant_category_code": "5999",
  "transaction_location_lat": 28.6139,
  "transaction_location_lng": 77.2090,
  "device_fingerprint": "fp_abc123",
  "device_type": "mobile",
  "transaction_timestamp": "2026-04-14T21:30:00Z"
}

// Response:
{
  "transaction_id": "txn-uuid",
  "fraud_score": 0.91,
  "fraud_category": "fraudulent",
  "fraud_risk_level": "critical",
  "decision": "BLOCK",
  "triggered_rules": ["impossible_travel", "new_device_high_amount"],
  "processing_time_ms": 18
}`} />

          <SectionAnchor id="step-alerts" />
          <SubTitle>Step 5 — Alerts Fire Automatically</SubTitle>
          <p className="text-sm text-gray-400 mb-3">When a transaction scores above threshold, FinShield creates a fraud alert and fires configured notification channels — no extra work required.</p>
          <div className="grid grid-cols-2 gap-3 my-4">
            {[
              { score: "≥ 0.80", decision: "BLOCK",  color: "#EF4444", channels: "Email + SMS + In-app + Optional call" },
              { score: "0.60–0.79", decision: "ALERT",  color: "#F97316", channels: "Email + SMS + In-app" },
              { score: "0.30–0.59", decision: "FLAG",   color: "#F59E0B", channels: "Email + In-app" },
              { score: "< 0.30",   decision: "PASS",   color: "#00FF87", channels: "Silent log only" },
            ].map((row) => (
              <div key={row.decision} className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold" style={{ color: row.color }}>{row.decision}</span>
                  <span className="text-xs text-gray-500 font-mono">{row.score}</span>
                </div>
                <p className="text-xs text-gray-500">{row.channels}</p>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ FEATURES */}
          <SectionAnchor id="features" />
          <SectionTitle sub="Everything included out of the box">
            Platform Features
          </SectionTitle>

          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {[
              { icon: <Brain size={18} />, color: "#8B5CF6", title: "Multi-Layer ML Detection",
                desc: "5-model ensemble: Isolation Forest + DBSCAN + XGBoost + Random Forest + Neural Network. Each layer catches different fraud patterns for maximum coverage." },
              { icon: <Zap size={18} />, color: "#00FF87", title: "Real-Time Scoring <18ms",
                desc: "Neural network exported to ONNX format for 5× faster inference. Redis feature caching means repeat customers are scored even faster." },
              { icon: <Database size={18} />, color: "#3B82F6", title: "20+ Data Connectors",
                desc: "Native connectors for Supabase, PostgreSQL, MySQL, MongoDB, Snowflake, Stripe, Razorpay, Kafka, and more. Schema normalization happens automatically." },
              { icon: <Bell size={18} />, color: "#F59E0B", title: "Multi-Channel Alerts",
                desc: "Email (Resend / Brevo), SMS (Twilio), Push (Firebase), In-app WebSocket, Webhook, and Slack. Each channel is optional and gracefully degraded." },
              { icon: <BarChart3 size={18} />, color: "#EC4899", title: "Live Analytics Dashboard",
                desc: "Real-time KPI cards, fraud trend charts, model performance panels, geographic heatmaps, and SHAP feature importance — all updating via WebSocket." },
              { icon: <RefreshCw size={18} />, color: "#06B6D4", title: "Automated Model Retraining",
                desc: "Drift detection via Kolmogorov-Smirnov test. Models auto-retrain when accuracy drops. Free: monthly. Pro: weekly. Advanced: on-demand + drift-triggered." },
              { icon: <Lock size={18} />, color: "#EF4444", title: "Multi-Tenant Isolation",
                desc: "Row-level security in PostgreSQL. Each institution only ever sees its own data. Credentials encrypted with AES-256 before being written to disk." },
              { icon: <Code2 size={18} />, color: "#F97316", title: "Full REST API + WebSocket",
                desc: "Every feature is API-first. JWT auth, RBAC (admin/analyst/viewer), Pydantic-validated schemas, OpenAPI docs, rate limiting per plan." },
            ].map((f) => (
              <div key={f.title} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-2" style={{ color: f.color }}>{f.icon}<span className="font-bold text-white text-sm">{f.title}</span></div>
                <p className="text-xs text-gray-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ SERVICE FLOW */}
          <SectionAnchor id="service-flow" />
          <SectionTitle sub="How a transaction flows through the platform end-to-end">
            Service Flow
          </SectionTitle>

          <div className="space-y-3 mb-6">
            {[
              { step: "01", icon: <Globe size={16} />, color: "#3B82F6",   title: "Data Ingestion",       desc: "Transaction arrives via REST POST, webhook, Kafka consumer, or direct DB polling. Schema is normalized to FinShield standard format regardless of source." },
              { step: "02", icon: <Database size={16} />, color: "#00FF87", title: "Customer History Load", desc: "Last 30 days of transactions fetched for the customer. Cached in Redis for <5ms lookup on repeat customers." },
              { step: "03", icon: <Cpu size={16} />, color: "#8B5CF6",     title: "Feature Engineering",   desc: "200+ features generated: velocity counts, z-scores, geographic distances, device age, behavioral patterns, network proximity scores." },
              { step: "04", icon: <AlertTriangle size={16} />, color: "#F59E0B", title: "Rules Engine",    desc: "20+ deterministic rules evaluated in <5ms. Impossible travel, velocity spike, new device + high amount, account takeover indicators, and more." },
              { step: "05", icon: <Brain size={16} />, color: "#EC4899",    title: "ML Inference",          desc: "Feature vector scored in parallel by Isolation Forest, XGBoost, Random Forest, and Neural Network (ONNX). Total ML inference <18ms." },
              { step: "06", icon: <Activity size={16} />, color: "#F97316", title: "Ensemble Scoring",     desc: "Weighted combination: Rules (25%) + Isolation Forest (10%) + DBSCAN (10%) + XGBoost (30%) + Random Forest (15%) + Neural Network (10%) = final fraud_score." },
              { step: "07", icon: <Server size={16} />, color: "#06B6D4",   title: "Write-Back",           desc: "fraud_score, fraud_category, fraud_risk_level, triggered_rules, and fraud_scored_at written back to the transaction row in your database." },
              { step: "08", icon: <Bell size={16} />, color: "#EF4444",     title: "Alert & Notify",       desc: "If score ≥ 0.30, fraud alert created. Notification channels fire based on severity: PASS → silent / FLAG → email / ALERT → email+SMS / BLOCK → all channels." },
            ].map((s, i) => (
              <div key={s.step} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border-2" style={{ borderColor: s.color, color: s.color, backgroundColor: `${s.color}15` }}>
                    {s.icon}
                  </div>
                  {i < 7 && <div className="w-px flex-1 bg-[#1E1E2E] my-1" />}
                </div>
                <div className="pb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-gray-600">{s.step}</span>
                    <span className="font-bold text-sm text-white">{s.title}</span>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ FRAUD DETECTION */}
          <SectionAnchor id="fraud-detection" />
          <SectionTitle sub="How FinShield detects fraud — rules, models, and decisions">
            Fraud Detection Engine
          </SectionTitle>

          <SectionAnchor id="fd-rules" />
          <SubTitle>Rules Engine</SubTitle>
          <p className="text-sm text-gray-400 mb-3">Deterministic rules fire before ML models. They are fast (&lt;5ms), explainable, and produce high-confidence signals for well-known fraud patterns.</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#1E1E2E] text-left">
                  <th className="py-2 pr-4 text-xs text-gray-500 font-mono uppercase">Rule</th>
                  <th className="py-2 pr-4 text-xs text-gray-500 font-mono uppercase">Condition</th>
                  <th className="py-2 text-xs text-gray-500 font-mono uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E1E2E]">
                {[
                  ["Impossible Travel",     ">900 km/h between consecutive transactions",       "BLOCK / Critical"],
                  ["Velocity Spike",        ">5× customer baseline in 1 hour",                  "FLAG / High"],
                  ["New Device + High Amt", "First-seen device + amount > 3× customer average", "FLAG / High"],
                  ["Account Takeover",      "Password reset + new device + amount > ₹10,000 within 30 min", "BLOCK / Critical"],
                  ["Rapid Succession",      "5+ transactions in <10 minutes",                   "FLAG / Medium"],
                  ["Cross-Border",          "First transaction in this country",                 "FLAG / Medium"],
                  ["Structuring",           "Multiple transactions just under reporting threshold", "BLOCK / Critical"],
                  ["Tor/VPN Detected",      "IP flagged as Tor exit node or known proxy",       "ALERT / High"],
                ].map(([rule, cond, action]) => (
                  <tr key={rule} className="hover:bg-[#111118] transition-colors">
                    <td className="py-2.5 pr-4 text-xs font-mono text-gray-200">{rule}</td>
                    <td className="py-2.5 pr-4 text-xs text-gray-400">{cond}</td>
                    <td className="py-2.5 text-xs text-[#F59E0B]">{action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <SectionAnchor id="fd-ml" />
          <SubTitle>ML Models (5-Layer Ensemble)</SubTitle>
          <div className="space-y-3 my-4">
            {[
              { name: "Isolation Forest",  type: "Unsupervised",  weight: "10%", desc: "Detects statistical outliers in the 200-feature space. No labels needed — trained on legitimate transactions only." },
              { name: "DBSCAN Clustering", type: "Unsupervised",  weight: "10%", desc: "Groups normal transaction patterns into clusters. Transactions that don't fit any cluster are scored as anomalies." },
              { name: "XGBoost Classifier",type: "Supervised",    weight: "30%", desc: "Primary fraud classifier. Handles class imbalance via scale_pos_weight. Trained on labeled 10K+ sample dataset." },
              { name: "Random Forest",     type: "Supervised",    weight: "15%", desc: "Ensemble robustness — reduces XGBoost variance. Provides feature importance scores." },
              { name: "Neural Network",    type: "Deep Learning", weight: "10%", desc: "PyTorch 3-layer network (256→128→64→1), exported to ONNX for <5ms inference in production." },
            ].map((m) => (
              <div key={m.name} className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4 flex items-start gap-4">
                <div className="text-center shrink-0 w-14">
                  <div className="text-lg font-black text-[#8B5CF6]">{m.weight}</div>
                  <div className="text-[9px] text-gray-600">weight</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-sm text-white">{m.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#111118] border border-[#2E2E3E] text-gray-500">{m.type}</span>
                  </div>
                  <p className="text-xs text-gray-400">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <InfoBox type="info">Rules engine contributes an additional <strong className="text-white">25%</strong> to the ensemble score, bringing total weights to 100%.</InfoBox>

          <SectionAnchor id="fd-scoring" />
          <SubTitle>Scoring & Decision Thresholds</SubTitle>
          <CodeBlock lang="python" code={`# Ensemble formula (simplified):
fraud_score = (
  rules_engine_score   * 0.25 +
  isolation_forest     * 0.10 +
  dbscan_outlier       * 0.10 +
  xgboost_proba        * 0.30 +
  random_forest_proba  * 0.15 +
  neural_network_proba * 0.10
)

# Decision thresholds:
if fraud_score < 0.30:   decision = "PASS"    # Allow silently
elif fraud_score < 0.60: decision = "FLAG"    # Allow + alert medium
elif fraud_score < 0.80: decision = "ALERT"   # Allow + alert high + SMS
else:                    decision = "BLOCK"   # Block + alert critical + all channels`} />

          <SectionAnchor id="fd-shap" />
          <SubTitle>Model Explainability (SHAP)</SubTitle>
          <p className="text-sm text-gray-400 mb-3">Every fraud score includes SHAP (SHapley Additive exPlanations) values showing which features contributed most to the decision. This is available on Pro and Advanced plans.</p>
          <CodeBlock lang="json" code={`// GET /api/v1/transactions/{id}/score
{
  "fraud_score": 0.91,
  "decision": "BLOCK",
  "shap_values": [
    { "feature": "distance_from_last_txn", "contribution": 0.38 },
    { "feature": "amount_zscore",          "contribution": 0.24 },
    { "feature": "is_new_device",          "contribution": 0.19 },
    { "feature": "hour_of_day",            "contribution": 0.08 },
    { "feature": "customer_risk_score",    "contribution": 0.02 }
  ]
}`} />

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ API REFERENCE */}
          <SectionAnchor id="api-reference" />
          <SectionTitle sub="Complete REST API and WebSocket reference">
            API Reference
          </SectionTitle>

          <InfoBox type="info">
            Base URL: <code className="font-mono text-xs">http://localhost:8003/api/v1</code> (dev) &nbsp;|&nbsp; All protected routes require <code className="font-mono text-xs">Authorization: Bearer &lt;access_token&gt;</code>
          </InfoBox>

          <SectionAnchor id="api-auth" />
          <SubTitle>Authentication</SubTitle>
          <p className="text-sm text-gray-400 mb-3">JWT-based authentication. Access tokens expire in 15 minutes; use the refresh endpoint to get a new one.</p>
          <Endpoint method="POST" path="/auth/signup"  description="Create institution account. Returns access + refresh tokens." auth={false} />
          <Endpoint method="POST" path="/auth/login"   description="Email + password login. Returns JWT access_token (15min) and refresh_token (7 days)." auth={false} />
          <Endpoint method="POST" path="/auth/refresh" description="Exchange refresh_token for a new access_token." auth={false} />
          <Endpoint method="GET"  path="/auth/me"      description="Return current user profile, role, tenant, and plan info." />
          <Endpoint method="POST" path="/auth/logout"  description="Invalidate refresh token server-side." />
          <CodeBlock lang="http" code={`// Login request
POST /api/v1/auth/login
{ "email": "admin@yourbank.com", "password": "YourPass123!" }

// Response
{
  "access_token":  "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type":    "bearer",
  "expires_in":    900
}`} />

          <SectionAnchor id="api-transactions" />
          <SubTitle>Transactions</SubTitle>
          <Endpoint method="POST" path="/transactions"          description="Ingest + score a transaction. Writes fraud fields back to your DB. Returns fraud_score, decision, and SHAP." />
          <Endpoint method="GET"  path="/transactions"          description="List transactions with filters: fraud_score, fraud_category, date range, channel, status. Paginated." />
          <Endpoint method="GET"  path="/transactions/{id}"     description="Full transaction detail with fraud breakdown and triggered rules." />
          <Endpoint method="GET"  path="/transactions/{id}/score" description="Re-score or fetch fraud analysis with full SHAP values for a transaction." />
          <Endpoint method="POST" path="/transactions/test"     description="Submit a test transaction (is_test=true). Full pipeline runs but transaction is filterable from live data." />
          <Endpoint method="POST" path="/transactions/batch"    description="Bulk ingest up to 1,000 transactions as JSON array or CSV. Scored in background." />

          <SectionAnchor id="api-alerts" />
          <SubTitle>Fraud Alerts</SubTitle>
          <Endpoint method="GET"  path="/alerts"          description="List alerts. Filter by: severity (low/medium/high/critical), status (open/confirmed/false_positive), date." />
          <Endpoint method="GET"  path="/alerts/{id}"     description="Alert detail with full transaction context, customer info, triggered rules, and notification history." />
          <Endpoint method="PUT"  path="/alerts/{id}/status" description="Update alert status: confirm_fraud | false_positive | under_review | closed. Triggers model feedback loop." />
          <Endpoint method="POST" path="/cases"           description="Create an investigation case from an alert. Assigns to analyst, sets SLA timer." />
          <Endpoint method="GET"  path="/cases/{id}"      description="Case details with full audit history of analyst actions." />

          <SectionAnchor id="api-customers" />
          <SubTitle>Customers</SubTitle>
          <Endpoint method="POST" path="/customers"                   description="Create a customer record." />
          <Endpoint method="GET"  path="/customers"                   description="List customers. Filter by risk_score, kyc_status, account_type." />
          <Endpoint method="GET"  path="/customers/{id}"              description="Customer 360 view: profile, risk score, account info, KYC status." />
          <Endpoint method="GET"  path="/customers/{id}/transactions" description="Transaction history for customer. Includes fraud scores per transaction." />
          <Endpoint method="GET"  path="/customers/{id}/fraud-alerts" description="All fraud alerts linked to this customer." />
          <Endpoint method="PUT"  path="/customers/{id}/risk-score"   description="Manually update customer risk score. Logged in audit trail." />
          <Endpoint method="PUT"  path="/customers/{id}/watchlist"    description="Add or remove customer from internal watchlist or sanctions list." />

          <SectionAnchor id="api-analytics" />
          <SubTitle>Analytics</SubTitle>
          <Endpoint method="GET" path="/analytics/overview"         description="KPI dashboard data: total transactions, fraud rate, blocked count, model accuracy." />
          <Endpoint method="GET" path="/analytics/fraud-rate"       description="Fraud rate over time. Params: range (7d/30d/90d), granularity (hour/day/week)." />
          <Endpoint method="GET" path="/analytics/fraud-trends"     description="Fraud breakdown by type, channel, merchant category, and device type." />
          <Endpoint method="GET" path="/analytics/model-performance" description="Precision, recall, F1, AUC-ROC trend history. Per-model and ensemble." />
          <Endpoint method="GET" path="/analytics/geographic"       description="Fraud events by location (lat/lng clusters). Used for heatmap visualization." />
          <Endpoint method="GET" path="/analytics/export"           description="Export analytics data as CSV or JSON. Supports date range and category filters." />

          <SectionAnchor id="api-settings" />
          <SubTitle>Settings & Credentials</SubTitle>
          <Endpoint method="GET"  path="/settings/database"           description="Get current DB connection config (secrets masked)." />
          <Endpoint method="PUT"  path="/settings/database"           description="Save database connection. Secrets encrypted with AES-256 before storage." />
          <Endpoint method="POST" path="/settings/test-connection"    description="Live test the configured database connection. Returns latency and table counts." />
          <Endpoint method="GET"  path="/credentials"                 description="List all stored API keys (values always masked — last 4 chars only)." />
          <Endpoint method="POST" path="/credentials"                 description="Save an API key (Resend, Brevo, Twilio, Stripe, etc.). Encrypted before storage." />
          <Endpoint method="POST" path="/credentials/{id}/test"       description="Live-test a stored credential against its provider API." />
          <Endpoint method="DELETE" path="/credentials/{id}"          description="Delete a stored credential." />

          <SectionAnchor id="api-models" />
          <SubTitle>ML Models</SubTitle>
          <Endpoint method="GET"  path="/models"           description="List all ML models with version, status, and performance metrics." />
          <Endpoint method="GET"  path="/models/{id}"      description="Model detail: precision, recall, F1, AUC-ROC, training samples, artifact path." />
          <Endpoint method="POST" path="/models/{id}/promote" description="Promote a model version to production (replaces current active model)." />
          <Endpoint method="POST" path="/models/retrain"   description="Trigger a manual retraining job. Returns job_id for status polling." />
          <Endpoint method="GET"  path="/models/active"    description="Get current production model with full metrics summary." />

          <SectionAnchor id="api-rules" />
          <SubTitle>Fraud Rules</SubTitle>
          <Endpoint method="GET"    path="/rules"         description="List all rules (built-in + custom). Filter by category, is_active." />
          <Endpoint method="POST"   path="/rules"         description="Create a custom rule using YAML DSL conditions. Pro/Advanced plan." />
          <Endpoint method="PUT"    path="/rules/{id}"    description="Update rule conditions, threshold, action, or active status." />
          <Endpoint method="DELETE" path="/rules/{id}"    description="Delete a custom rule." />
          <Endpoint method="POST"   path="/rules/{id}/test" description="Test a rule against a sample transaction and see if it would have fired." />

          <SectionAnchor id="api-websocket" />
          <SubTitle>WebSocket Events (Real-Time)</SubTitle>
          <p className="text-sm text-gray-400 mb-3">Connect to WebSocket endpoints for real-time dashboard updates. Authenticate by passing the JWT in the query string on connect.</p>
          <Endpoint method="WS" path="/ws/transactions" description="Live transaction stream — emits every scored transaction as a JSON event." auth={false} />
          <Endpoint method="WS" path="/ws/alerts"       description="Live fraud alert stream — emits when an alert is created or status changes." auth={false} />
          <Endpoint method="WS" path="/ws/metrics"      description="Real-time dashboard metrics — emits KPI updates every 5 seconds." auth={false} />
          <CodeBlock lang="javascript" code={`// Connect from the browser:
const ws = new WebSocket(
  \`ws://localhost:8003/ws/alerts?token=\${accessToken}\`
);

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log("New fraud alert:", alert.alert_id, alert.severity);
};`} />

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ INTEGRATIONS */}
          <SectionAnchor id="integrations" />
          <SectionTitle sub="20+ pre-built connectors with automatic schema normalization">
            Data Connectors
          </SectionTitle>

          <p className="text-sm text-gray-400 mb-4">All connectors normalize external schemas to FinShield&apos;s standard format automatically. You never rewrite your pipeline — FinShield adapts to your data.</p>

          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#1E1E2E]">
                  {["Category", "Connector", "Auth Method"].map(h => (
                    <th key={h} className="py-2 pr-6 text-left text-xs text-gray-500 font-mono uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E1E2E] text-xs">
                {[
                  ["Database",        "Supabase (PostgreSQL)",    "URL + Anon Key + Service Key"],
                  ["Database",        "PostgreSQL (generic)",     "Host / Port / User / Password"],
                  ["Database",        "MySQL / MariaDB",          "Host / Port / User / Password"],
                  ["Database",        "MongoDB Atlas",            "Connection String"],
                  ["Database",        "MS SQL Server",            "Host / User / Password"],
                  ["Database",        "Oracle DB",                "Host / Service Name / User / Password"],
                  ["Database",        "Snowflake",                "Account / Warehouse / User / Password"],
                  ["Database",        "CockroachDB",              "Host / Port / User / Password (PostgreSQL-compatible)"],
                  ["Database",        "Neon Serverless Postgres", "Connection String"],
                  ["Database",        "PlanetScale",              "Host / Username / Password"],
                  ["Payment Gateway", "Stripe",                   "Webhooks + API Key"],
                  ["Payment Gateway", "Razorpay",                 "Webhooks + API Key (India)"],
                  ["Payment Gateway", "PayPal",                   "Webhooks + OAuth2"],
                  ["Payment Network", "Visa Transaction Data",    "Real-time Feed + OAuth2"],
                  ["Payment Network", "Mastercard API",           "Real-time Feed + OAuth2"],
                  ["Payment Network", "RuPay / NPCI",             "API Key (India)"],
                  ["Streaming",       "Apache Kafka",             "SASL/mTLS Consumer Group"],
                  ["Streaming",       "Azure Event Hubs",         "AMQP Connection String"],
                  ["Batch/File",      "CSV / SFTP Upload",        "Key-based SFTP or direct upload"],
                  ["Legacy",          "Custom REST API",          "Configurable (API Key / OAuth2 / Basic)"],
                ].map(([cat, name, auth], i) => (
                  <tr key={i} className="hover:bg-[#111118] transition-colors">
                    <td className="py-2.5 pr-6 text-gray-500">{cat}</td>
                    <td className="py-2.5 pr-6 text-gray-200 font-mono">{name}</td>
                    <td className="py-2.5 text-gray-400">{auth}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ NOTIFICATIONS */}
          <SectionAnchor id="notifications" />
          <SectionTitle sub="Multi-channel fraud alert delivery — all channels gracefully degrade">
            Notifications
          </SectionTitle>

          <p className="text-sm text-gray-400 mb-4">FinShield fires notifications only when a fraud event occurs above the configured threshold. Every channel is optional — the platform works even with zero API keys configured (in-app alerts always fire).</p>

          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {[
              { icon: <Mail size={16} />, color: "#3B82F6",    title: "Email — Resend",       badge: "3,000/month free", desc: "Primary email provider. Set your Resend API key in Settings → Integrations. Supports verified sender domains.", plans: ["free","pro","advanced"] },
              { icon: <Mail size={16} />, color: "#0092CC",    title: "Email — Brevo",        badge: "300/day free",    desc: "Fallback email provider. Fires automatically when Resend is not configured. 9,000 emails/month free.", plans: ["free","pro","advanced"] },
              { icon: <Phone size={16} />, color: "#8B5CF6",   title: "SMS — Twilio",         badge: "Paid (~₹0.10/SMS)", desc: "SMS to customer phone on HIGH/CRITICAL alerts. Requires Twilio Account SID, Auth Token, and From Number.", plans: ["pro","advanced"] },
              { icon: <Bell size={16} />, color: "#F59E0B",    title: "Push — Firebase FCM",  badge: "Free unlimited",  desc: "Mobile push notifications. Configure Firebase service account JSON in Settings.", plans: ["pro","advanced"] },
              { icon: <MessageSquare size={16} />, color: "#00FF87", title: "In-App (WebSocket)", badge: "Always on",  desc: "Real-time dashboard alert feed over WebSocket. No API key needed — fires for all alert severities.", plans: ["free","pro","advanced"] },
              { icon: <Webhook size={16} />, color: "#EC4899", title: "Outbound Webhook",     badge: "Pro+",           desc: "POST fraud alert JSON to your own endpoint on alert creation. HMAC-signed for security verification.", plans: ["pro","advanced"] },
            ].map((n) => (
              <div key={n.title} className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span style={{ color: n.color }}>{n.icon}</span>
                  <span className="font-bold text-sm text-white">{n.title}</span>
                  <span className="text-[10px] text-gray-500 bg-[#1E1E2E] px-2 py-0.5 rounded-full ml-auto">{n.badge}</span>
                </div>
                <p className="text-xs text-gray-400 mb-2">{n.desc}</p>
                <div className="flex gap-1">
                  {(n.plans as Array<"free"|"pro"|"advanced">).map(p => <PlanBadge key={p} plan={p} />)}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ PLANS */}
          <SectionAnchor id="plans" />
          <SectionTitle sub="Choose the plan that fits your transaction volume and feature needs">
            Subscription Plans
          </SectionTitle>

          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#1E1E2E]">
                  <th className="py-3 pr-6 text-left text-xs text-gray-500 font-mono uppercase">Feature</th>
                  <th className="py-3 pr-6 text-center text-xs text-[#22C55E] font-mono uppercase">Free</th>
                  <th className="py-3 pr-6 text-center text-xs text-[#3B82F6] font-mono uppercase">Pro</th>
                  <th className="py-3     text-center text-xs text-[#8B5CF6] font-mono uppercase">Advanced</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E1E2E] text-xs">
                {[
                  ["Price",                 "₹0/month",     "₹9,999/month",    "₹24,999/month"],
                  ["Transactions/month",    "10,000",        "500,000",          "Unlimited"],
                  ["Data Schema",           "Standard",      "Standard",         "Custom columns"],
                  ["ML Models",             "Shared global", "Shared global",    "Dedicated + personalized"],
                  ["Fraud Rules",           "5 built-in",    "25 (custom OK)",   "Unlimited custom"],
                  ["Email Alerts",          "✅",            "✅",               "✅"],
                  ["SMS Alerts (Twilio)",   "❌",            "✅",               "✅"],
                  ["Phone Call Alerts",     "❌",            "❌",               "✅"],
                  ["Webhook",               "❌",            "✅",               "✅"],
                  ["Model Retraining",      "Monthly auto",  "Weekly auto",      "On-demand + drift-triggered"],
                  ["SHAP Explainability",   "❌",            "Summaries",        "Full SHAP + audit trail"],
                  ["API Access",            "Read-only",     "Full REST API",    "Full API + WebSocket"],
                  ["Data Isolation",        "Shared schema", "Dedicated schema", "Dedicated schema + VPC"],
                  ["Support",               "Community",     "Email (48h)",      "Dedicated SLA"],
                ].map(([feat, free, pro, adv]) => (
                  <tr key={feat} className="hover:bg-[#111118] transition-colors">
                    <td className="py-2.5 pr-6 text-gray-300">{feat}</td>
                    <td className="py-2.5 pr-6 text-center text-gray-400">{free}</td>
                    <td className="py-2.5 pr-6 text-center text-gray-200">{pro}</td>
                    <td className="py-2.5     text-center text-[#8B5CF6] font-semibold">{adv}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-t border-[#1E1E2E] my-8" />

          {/* ═══════════════════════════════════════════════════════ SECURITY */}
          <SectionAnchor id="security" />
          <SectionTitle sub="Enterprise-grade security built into every layer">
            Security & Compliance
          </SectionTitle>

          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {[
              { badge: "AES-256",    desc: "All credentials and sensitive config encrypted at rest using AES-256 before being written to the database." },
              { badge: "TLS 1.3",   desc: "All API traffic encrypted in transit. HTTPS enforced; plain HTTP connections are rejected." },
              { badge: "JWT Auth",   desc: "Stateless JWT tokens. Access tokens expire in 15 minutes. Refresh tokens scoped to 7 days and invalidatable." },
              { badge: "RLS",       desc: "PostgreSQL Row-Level Security ensures each tenant only queries their own rows — even if application logic has a bug." },
              { badge: "RBAC",      desc: "Three roles: Admin (full access), Analyst (alerts + cases + read-only settings), Viewer (read-only dashboard)." },
              { badge: "PCI-DSS",   desc: "Card numbers never stored. Only tokenized references. All PCI-DSS relevant controls applied to card data handling." },
            ].map((s) => (
              <div key={s.badge} className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4">
                <div className="text-sm font-black text-[#00FF87] mb-2 font-mono">{s.badge}</div>
                <p className="text-xs text-gray-400">{s.desc}</p>
              </div>
            ))}
          </div>

          <InfoBox type="tip">
            All audit-sensitive actions (alert status changes, model promotions, credential saves) are logged to the <code className="font-mono text-xs">audit_logs</code> table with actor, timestamp, old value, and new value. Access via <code className="font-mono text-xs">GET /api/v1/audit</code> (Admin only).
          </InfoBox>

          {/* ── Footer ── */}
          <div className="border-t border-[#1E1E2E] mt-12 pt-8 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield size={16} className="text-[#00FF87]" />
              <span className="text-sm text-gray-500">FinShield AI Documentation</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <Link href="/" className="hover:text-white transition-colors">Home</Link>
              <Link href="/signup" className="hover:text-white transition-colors">Sign Up</Link>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") ?? "http://localhost:8003"}/docs`}
                target="_blank" rel="noopener noreferrer"
                className="hover:text-white transition-colors flex items-center gap-1"
              >
                Swagger <ExternalLink size={10} />
              </a>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
