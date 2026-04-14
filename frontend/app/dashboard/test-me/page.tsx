"use client";

import { useAuthStore, isAdmin, type AuthUser } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, Play, RefreshCw,
  CheckCircle2, XCircle, Info, Brain, CreditCard, User,
  MessageSquare, Search, MapPin, Table, Mail,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { TransactionDetailsPanel } from "@/components/transaction-details-panel";

// ── Country list ─────────────────────────────────────────────────────────────
const COUNTRIES = [
  { code: "IN", name: "India" },
  { code: "US", name: "United States" },
  { code: "GB", name: "United Kingdom" },
  { code: "AE", name: "United Arab Emirates" },
  { code: "SG", name: "Singapore" },
  { code: "AU", name: "Australia" },
  { code: "CA", name: "Canada" },
  { code: "DE", name: "Germany" },
  { code: "FR", name: "France" },
  { code: "NL", name: "Netherlands" },
  { code: "JP", name: "Japan" },
  { code: "CN", name: "China" },
  { code: "HK", name: "Hong Kong" },
  { code: "MY", name: "Malaysia" },
  { code: "TH", name: "Thailand" },
  { code: "PH", name: "Philippines" },
  { code: "ZA", name: "South Africa" },
  { code: "NG", name: "Nigeria" },
  { code: "KE", name: "Kenya" },
  { code: "GH", name: "Ghana" },
  { code: "UA", name: "Ukraine" },
  { code: "RU", name: "Russia" },
  { code: "PK", name: "Pakistan" },
  { code: "BD", name: "Bangladesh" },
  { code: "BR", name: "Brazil" },
  { code: "MX", name: "Mexico" },
  { code: "AR", name: "Argentina" },
];

// ── Types ────────────────────────────────────────────────────────────────────
interface SimulatorForm {
  cardholder_name: string;
  email: string;
  mobile_number: string;
  payment_method: "credit_card" | "debit_card" | "upi";
  upi_vpa: string;
  card_number: string;
  cvv: string;
  expiry_month: string;
  expiry_year: string;
  amount: string;
  purchase_type: string;
  channel: string;
  merchant_name: string;
  city: string;
  country_code: string;
  device_type: string;
  is_new_device: boolean;
  customer_id: string;
}

interface ReasonCard {
  title: string;
  detail: string;
  severity: string;
}

interface ModelLayer {
  name: string;
  layer: string;
  score: number;
  weight: number;
  contribution: number;
  triggered_rules?: string[];
  individual_models?: Record<string, number>;
  description: string;
}

interface ModelBreakdown {
  layers: ModelLayer[];
  final_score: number;
  final_decision: string;
  rules_score: number;
  ml_available: boolean;
}

interface Conclusion {
  verdict: string;
  headline: string;
  detail: string;
  risk_factors: string[];
  mitigating_factors: string[];
  rules_score: number;
  final_score: number;
  ml_available: boolean;
}

interface SimResult {
  transaction_id: string;
  prediction: string;
  risk_score: number;
  risk_level: string;
  decision: string;
  reasons: ReasonCard[];
  shap_explanation: Array<{ feature: string; shap_value: number; direction: string }> | null;
  journey: Record<string, { ok: boolean; ms?: number; triggered?: number; status?: string; model?: string; score?: number; decision?: string; is_test?: boolean }>;
  sms_status: string | null;
  email_status: string | null;
  email_recipients: Array<{ to: string; status: string }> | null;
  fraud_category: string;
  fraud_risk_level: string | null;
  is_blocked: boolean;
  is_flagged: boolean;
  amount?: number;
  channel?: string;
  merchant_name?: string;
  // New fields
  rules_score?: number;
  model_breakdown?: ModelBreakdown;
  conclusion?: Conclusion;
}

// ── Decision colors ───────────────────────────────────────────────────────────
const DECISION_COLOR: Record<string, string> = {
  PASS:  "#00FF87",
  FLAG:  "#F59E0B",
  ALERT: "#F97316",
  BLOCK: "#EF4444",
};

// ── Preset scenarios ──────────────────────────────────────────────────────────
const PRESETS: Record<string, Partial<SimulatorForm>> = {
  normal: {
    cardholder_name: "Priya Shah",
    email: "priya.shah@gmail.com",
    mobile_number: "+919876543210",
    amount: "1200",
    purchase_type: "grocery",
    channel: "pos_physical",
    merchant_name: "D-Mart",
    city: "Mumbai",
    country_code: "IN",
    device_type: "pos_terminal",
    is_new_device: false,
  },
  impossible_travel: {
    cardholder_name: "Rahul Verma",
    email: "rahul.verma@gmail.com",
    mobile_number: "+919812345678",
    amount: "45000",
    purchase_type: "electronics",
    channel: "online",
    merchant_name: "Amazon UK",
    city: "London",
    country_code: "GB",
    device_type: "mobile",
    is_new_device: true,
  },
  high_value_night: {
    cardholder_name: "Meera Iyer",
    email: "meera.iyer@company.com",
    mobile_number: "+918765432109",
    amount: "95000",
    purchase_type: "atm_withdrawal",
    channel: "atm",
    merchant_name: "ATM Withdrawal",
    city: "Bangalore",
    country_code: "IN",
    device_type: "pos_terminal",
    is_new_device: true,
  },
  velocity_fraud: {
    cardholder_name: "Arun Nair",
    email: "arun.nair@email.com",
    mobile_number: "+917654321098",
    amount: "9500",
    purchase_type: "online_shopping",
    channel: "online",
    merchant_name: "Flipkart",
    city: "Chennai",
    country_code: "IN",
    device_type: "mobile",
    is_new_device: false,
  },
  foreign_wire: {
    cardholder_name: "Suresh Pillai",
    email: "suresh.pillai@corp.com",
    mobile_number: "+919988776655",
    amount: "320000",
    purchase_type: "wire_transfer",
    channel: "wire",
    merchant_name: "International Wire",
    city: "Lagos",
    country_code: "NG",
    device_type: "desktop",
    is_new_device: true,
  },
  structuring: {
    cardholder_name: "Kavitha Reddy",
    email: "kavitha.reddy@biz.com",
    mobile_number: "+917865432190",
    amount: "750000",
    purchase_type: "wire_transfer",
    channel: "online",
    merchant_name: "Overseas Transfer",
    city: "Hyderabad",
    country_code: "IN",
    device_type: "desktop",
    is_new_device: false,
  },
};

const PRESET_LABELS: Record<string, string> = {
  normal:           "Normal Purchase",
  impossible_travel: "Impossible Travel",
  high_value_night: "Large ATM Night",
  velocity_fraud:   "Velocity Fraud",
  foreign_wire:     "Foreign Wire",
  structuring:      "Structuring",
};

const PRESET_COLORS: Record<string, string> = {
  normal:           "#22C55E",
  impossible_travel: "#EF4444",
  high_value_night: "#F97316",
  velocity_fraud:   "#EF4444",
  foreign_wire:     "#8B5CF6",
  structuring:      "#EF4444",
};

// ── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ plan, user, clearAuth, router }: {
  plan: string;
  user: AuthUser;
  clearAuth: () => void;
  router: ReturnType<typeof useRouter>;
}) {
  const planColor = plan === "advanced" ? "#8B5CF6" : plan === "pro" ? "#3B82F6" : "#00FF87";
  const navItems = [
    { icon: Activity,      label: "Dashboard",    href: "/dashboard",             active: false },
    { icon: TrendingUp,    label: "Transactions",  href: "/dashboard/transactions", active: false },
    { icon: AlertTriangle, label: "Fraud Alerts",  href: "/dashboard/alerts",       active: false },
    { icon: FlaskConical,  label: "Test Me",       href: "/dashboard/test-me",      active: true  },
    { icon: Users,         label: "Customers",     href: "/dashboard/customers",    active: false },
    { icon: Database,      label: "Data Sources",  href: "/dashboard/data-sources", active: false },
    { icon: Table,         label: "Data Schema",   href: "/dashboard/data-schema",  active: false },
    { icon: Brain,         label: "ML Training",   href: "/dashboard/ml-training",  active: false },
    { icon: Settings,      label: "Settings",      href: "/dashboard/settings",     active: false },
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
        {navItems.map(({ icon: Icon, label, href, active }) => (
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

// ── Field helpers ─────────────────────────────────────────────────────────────
function Field({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <div>
      <label className="text-xs text-gray-500 mb-1.5 block">
        {label}{required && <span className="text-[#EF4444] ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none";

const selectClass =
  "w-full bg-[#0A0A0F] border border-[#1E1E2E] focus:border-[#00FF87]/40 rounded-xl px-3 py-2 text-sm text-white focus:outline-none";

// ── Blank form ────────────────────────────────────────────────────────────────
const BLANK: SimulatorForm = {
  cardholder_name: "",
  email: "",
  mobile_number: "",
  payment_method: "credit_card",
  upi_vpa: "",
  card_number: "",
  cvv: "",
  expiry_month: "12",
  expiry_year: "27",
  amount: "",
  purchase_type: "online_shopping",
  channel: "online",
  merchant_name: "",
  city: "Mumbai",
  country_code: "IN",
  device_type: "mobile",
  is_new_device: false,
  customer_id: "",
};

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function TestMePage() {
  const { user, token, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  const [form, setForm] = useState<SimulatorForm>(BLANK);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Notification shadow — fetch configured company alert emails to show in the banner
  const [alertEmails, setAlertEmails] = useState<string[]>([]);
  const [hasResend, setHasResend] = useState(false);
  useEffect(() => {
    if (!token) return;
    apiClient.getNotificationSettings(token)
      .then((data) => {
        const raw: string = data.company_alert_email || "";
        setAlertEmails(raw ? raw.split(",").map((e: string) => e.trim()).filter(Boolean) : []);
        setHasResend(data.has_resend ?? false);
      })
      .catch(() => {});
  }, [token]);

  // Phone lookup state
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupStatus, setLookupStatus] = useState<"idle" | "found" | "not_found">("idle");
  const [lookupMsg, setLookupMsg] = useState("");
  const [sampleCustomers, setSampleCustomers] = useState<{
    phone_number: string;
    full_name: string;
    city: string;
    risk_score?: number;
    customer_tier?: string;
    primary_payment_type?: string | null;
    primary_payment_label?: string | null;
  }[]>([]);

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

  // Pre-fetch sample customers so we can show suggestions on lookup failure
  useEffect(() => {
    if (!token) return;
    apiClient.simulatorSampleCustomers(token)
      .then((res) => setSampleCustomers(res.samples ?? []))
      .catch(() => {});
  }, [token]);

  // Test Me is admin-only: redirect non-admins back to dashboard
  if (user && !isAdmin(user)) {
    router.replace("/dashboard");
    return null;
  }

  if (!user) return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <Loader2 className="animate-spin text-[#00FF87]" size={32} />
    </div>
  );

  function applyPreset(key: string) {
    setForm((f) => ({ ...BLANK, ...f, ...PRESETS[key] }));
    setResult(null);
    setError(null);
    setLookupStatus("idle");
  }

  function set(field: keyof SimulatorForm, value: string | boolean) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function lookupByPhone() {
    if (!token || !form.mobile_number) return;
    setLookupLoading(true);
    setLookupStatus("idle");
    setLookupMsg("");
    try {
      const res = await apiClient.simulatorLookupCustomer(form.mobile_number, token);
      if (res.found) {
        // Auto-select the primary payment method if available
        const primaryPm = (res.payment_methods || [])[0];
        const pmType = primaryPm?.payment_type as "credit_card" | "debit_card" | "upi" | undefined;

        setForm((f) => ({
          ...f,
          cardholder_name: res.cardholder_name || f.cardholder_name,
          email: res.email || f.email,
          city: res.city || f.city,
          country_code: res.country_code || f.country_code,
          customer_id: res.customer_id,
          // Auto-fill payment method
          payment_method: pmType || f.payment_method,
          upi_vpa: primaryPm?.payment_type === "upi" ? (primaryPm.upi_vpa || f.upi_vpa) : f.upi_vpa,
          card_number: primaryPm?.card_last4
            ? `**** **** **** ${primaryPm.card_last4}`
            : (f.card_number || `**** **** **** ${res.card_last4}`),
          // Auto-fill masked CVV and expiry
          cvv: res.masked_cvv || "***",
          expiry_month: res.masked_expiry_month != null ? String(res.masked_expiry_month) : f.expiry_month,
          expiry_year:  res.masked_expiry_year  != null ? String(res.masked_expiry_year)  : f.expiry_year,
        }));
        const pmLabel = primaryPm ? ` · ${primaryPm.display_label}` : "";
        setLookupStatus("found");
        setLookupMsg(
          `Found: ${res.cardholder_name} · ${res.customer_tier} · KYC ${res.kyc_status} · Risk ${(res.risk_score * 100).toFixed(0)}%${pmLabel}`
        );
      }
    } catch {
      setLookupStatus("not_found");
      setLookupMsg("No customer found with this number. Try one of the sample customers below, or fill the form manually.");
      // Refresh sample suggestions on failure so they're always visible
      if (token) {
        apiClient.simulatorSampleCustomers(token)
          .then((res) => setSampleCustomers(res.samples ?? []))
          .catch(() => {});
      }
    } finally {
      setLookupLoading(false);
    }
  }

  async function pickSampleCustomer(phone: string) {
    if (!token) return;
    // Set phone first so user sees it immediately
    setForm((f) => ({ ...f, mobile_number: phone }));
    setLookupStatus("idle");
    setLookupMsg("");
    // Auto-trigger full lookup to pre-fill payment details
    setLookupLoading(true);
    try {
      const res = await apiClient.simulatorLookupCustomer(phone, token);
      if (res.found) {
        const primaryPm = (res.payment_methods || [])[0];
        const pmType = primaryPm?.payment_type as "credit_card" | "debit_card" | "upi" | undefined;
        setForm((f) => ({
          ...f,
          mobile_number: phone,
          cardholder_name: res.cardholder_name || f.cardholder_name,
          email: res.email || f.email,
          city: res.city || f.city,
          country_code: res.country_code || f.country_code,
          customer_id: res.customer_id,
          payment_method: pmType || f.payment_method,
          upi_vpa: primaryPm?.payment_type === "upi" ? (primaryPm.upi_vpa || f.upi_vpa) : f.upi_vpa,
          card_number: primaryPm?.card_last4
            ? `**** **** **** ${primaryPm.card_last4}`
            : (f.card_number || `**** **** **** ${res.card_last4}`),
          // Auto-fill masked CVV and expiry
          cvv: res.masked_cvv || "***",
          expiry_month: res.masked_expiry_month != null ? String(res.masked_expiry_month) : f.expiry_month,
          expiry_year:  res.masked_expiry_year  != null ? String(res.masked_expiry_year)  : f.expiry_year,
        }));
        const pmLabel = primaryPm ? ` · ${primaryPm.display_label}` : "";
        setLookupStatus("found");
        setLookupMsg(
          `Found: ${res.cardholder_name} · ${res.customer_tier} · KYC ${res.kyc_status} · Risk ${(res.risk_score * 100).toFixed(0)}%${pmLabel}`
        );
      }
    } catch {
      setLookupStatus("not_found");
      setLookupMsg("No customer found with this number.");
    } finally {
      setLookupLoading(false);
    }
  }

  async function runTest() {
    if (!token || !form.amount) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const rawYear = parseInt(form.expiry_year || "27");
      const expiryYear = isNaN(rawYear) ? 2027 : (rawYear < 100 ? 2000 + rawYear : rawYear);

      const isUpi = form.payment_method === "upi";

      // Strip spaces, dashes and asterisks from the card number.
      // If the result is shorter than 13 digits (e.g. a masked "**** **** **** 5678"
      // that stripped down to "5678"), fall back to a valid test card number so
      // the backend min_length=13 validator always passes.
      const strippedCard = form.card_number.replace(/[\s\-\*]/g, "");
      const resolvedCard = strippedCard.length >= 13 ? strippedCard : "4111111111111111";

      // Normalise CVV: replace "***" (masked placeholder from lookup) with "123"
      const resolvedCvv = /^\*+$/.test(form.cvv || "") ? "123" : (form.cvv || "123");

      const payload: Record<string, unknown> = {
        cardholder_name: form.cardholder_name || "Test User",
        payment_method:  form.payment_method,
        // Card fields — use defaults for UPI so backend validation passes
        card_number:     isUpi ? "0000000000000000" : resolvedCard,
        cvv:             isUpi ? "000" : resolvedCvv,
        expiry_month:    isUpi ? 12 : parseInt(form.expiry_month || "12"),
        expiry_year:     isUpi ? 2030 : expiryYear,
        amount:          parseFloat(form.amount),
        purchase_type:   form.purchase_type,
        channel:         form.channel,
        country_code:    form.country_code || "IN",
        device_type:     form.device_type  || "mobile",
        is_new_device:   form.is_new_device,
      };

      if (form.email)         payload.email         = form.email;
      if (form.mobile_number) payload.mobile_number = form.mobile_number;
      if (form.city)          payload.city          = form.city;
      if (form.merchant_name) payload.merchant_name = form.merchant_name;
      if (form.customer_id)   payload.customer_id   = form.customer_id;
      if (isUpi && form.upi_vpa) payload.upi_vpa    = form.upi_vpa;

      const res = await apiClient.simulatorPredict(payload, token);
      setResult(res as SimResult);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to run simulation");
    } finally {
      setLoading(false);
    }
  }

  const decisionColor = result ? (DECISION_COLOR[result.decision] || "#6B7280") : "#6B7280";

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <Sidebar plan={user.plan} user={user} clearAuth={clearAuth} router={router} />

      <main className="ml-60 p-8">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-black">Test Me</h1>
            <p className="text-gray-500 text-sm mt-1">
              Full card-level transaction simulation — step-by-step ML fraud detection journey
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#00FF87] bg-[#00FF87]/10 border border-[#00FF87]/20 px-3 py-1.5 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00FF87] animate-pulse" />
            is_test = true · won&apos;t affect live metrics
          </div>
        </div>

        {/* Testing purpose note */}
        <div className="flex items-start gap-3 bg-[#F59E0B]/8 border border-[#F59E0B]/30 rounded-xl px-4 py-3 mb-3">
          <Info size={15} className="text-[#F59E0B] shrink-0 mt-0.5" />
          <div className="text-xs text-[#F59E0B]/90 leading-relaxed">
            <span className="font-bold">Testing Environment Only —</span> All transactions submitted here are tagged{" "}
            <span className="font-mono bg-[#F59E0B]/15 px-1 py-0.5 rounded">is_test = true</span> and stored separately from live data.
            They are visible in the Transactions tab with a TEST badge but excluded from fraud rate calculations and live alerts.
            Real customer notifications (SMS/email) will <span className="font-semibold">not</span> fire unless explicitly configured in Settings.
          </div>
        </div>

        {/* Notification shadow — show which email(s) are configured to receive fraud alerts */}
        <div className="flex items-center gap-3 bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-2.5 mb-6">
          <Mail size={13} className={hasResend && alertEmails.length > 0 ? "text-[#00FF87] shrink-0" : "text-gray-600 shrink-0"} />
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <span className="text-xs text-gray-500 shrink-0">Company alert email:</span>
            {alertEmails.length > 0 ? (
              alertEmails.map((email) => (
                <span
                  key={email}
                  className="text-xs font-mono bg-[#00FF87]/8 border border-[#00FF87]/20 text-[#00FF87] px-2 py-0.5 rounded-lg"
                >
                  {email}
                </span>
              ))
            ) : (
              <span className="text-xs text-gray-600 italic">not configured</span>
            )}
            {!hasResend && alertEmails.length > 0 && (
              <span className="text-[10px] text-[#F59E0B]/70 bg-[#F59E0B]/8 border border-[#F59E0B]/20 px-2 py-0.5 rounded-lg">
                no Resend key — emails won&apos;t fire
              </span>
            )}
          </div>
          <Link
            href="/dashboard/settings?section=integrations"
            className="ml-auto text-[10px] text-gray-500 hover:text-white shrink-0 transition-colors"
          >
            Configure →
          </Link>
        </div>

        <div className={`grid ${result ? "grid-cols-3" : "grid-cols-2"} gap-6`}>
          {/* ── LEFT: Form ──────────────────────────────────────────────────── */}
          <div>
            {/* Preset buttons */}
            <div className="mb-5">
              <div className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Quick Scenarios</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(PRESET_LABELS).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className="text-xs border border-[#1E1E2E] hover:border-[#00FF87]/40 text-gray-400 hover:text-white px-3 py-1.5 rounded-xl transition-all"
                    style={{ borderLeftColor: PRESET_COLORS[key], borderLeftWidth: 2 }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 space-y-4">
              {/* ── Cardholder section ───────────────────────────────────── */}
              <div className="flex items-center gap-2 mb-1">
                <User size={13} className="text-[#3B82F6]" />
                <span className="text-xs text-[#3B82F6] font-semibold uppercase tracking-wide">Cardholder</span>
              </div>

              {/* Phone lookup row */}
              <Field label="Mobile Number (lookup customer)">
                <div className="flex gap-2">
                  <input
                    value={form.mobile_number}
                    onChange={(e) => { set("mobile_number", e.target.value); setLookupStatus("idle"); }}
                    placeholder="+919876543210"
                    className={`${inputClass} flex-1`}
                  />
                  <button
                    onClick={lookupByPhone}
                    disabled={lookupLoading || !form.mobile_number}
                    title="Auto-fill cardholder details from phone number"
                    className="flex items-center gap-1.5 text-xs bg-[#3B82F6]/10 border border-[#3B82F6]/30 text-[#3B82F6] px-3 py-2 rounded-xl hover:bg-[#3B82F6]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all shrink-0"
                  >
                    {lookupLoading
                      ? <Loader2 size={13} className="animate-spin" />
                      : <Search size={13} />
                    }
                    Lookup
                  </button>
                </div>
                {/* Lookup status feedback */}
                {lookupStatus !== "idle" && (
                  <div className={`mt-1.5 flex items-start gap-1.5 text-xs ${
                    lookupStatus === "found" ? "text-[#00FF87]" : "text-[#F59E0B]"
                  }`}>
                    {lookupStatus === "found"
                      ? <CheckCircle2 size={11} className="shrink-0 mt-0.5" />
                      : <XCircle size={11} className="shrink-0 mt-0.5" />
                    }
                    {lookupMsg}
                  </div>
                )}

                {/* Sample customer suggestions — shown on failure or when field is empty */}
                {(lookupStatus === "not_found" || (!form.mobile_number && sampleCustomers.length > 0)) && (
                  <div className="mt-2">
                    <p className="text-[10px] text-gray-500 mb-1.5">
                      {lookupStatus === "not_found" ? "Try a sample customer:" : "Sample customers in DB:"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {sampleCustomers.map((c, idx) => (
                        <button
                          key={c.phone_number ?? idx}
                          type="button"
                          onClick={() => pickSampleCustomer(c.phone_number)}
                          className="flex items-center gap-1.5 text-[10px] bg-[#1E1E2E] border border-[#2E2E3E] hover:border-[#3B82F6]/50 hover:bg-[#3B82F6]/10 text-gray-300 hover:text-white px-2 py-1.5 rounded-lg transition-all"
                          title={`${c.full_name} · ${c.city}${c.primary_payment_label ? ` · ${c.primary_payment_label}` : ""}`}
                        >
                          <User size={9} className="text-[#3B82F6]" />
                          <span className="font-mono">{c.phone_number}</span>
                          <span className="text-gray-500">·</span>
                          <span className="text-gray-400 truncate max-w-[70px]">{c.full_name.split(" ")[0]}</span>
                          {c.primary_payment_type && (
                            <span className={`text-[9px] px-1 py-0.5 rounded font-semibold ${
                              c.primary_payment_type === "upi"         ? "bg-[#00FF87]/10 text-[#00FF87]" :
                              c.primary_payment_type === "credit_card" ? "bg-[#8B5CF6]/10 text-[#8B5CF6]" :
                              "bg-[#3B82F6]/10 text-[#3B82F6]"
                            }`}>
                              {c.primary_payment_type === "upi" ? "UPI" : c.primary_payment_type === "credit_card" ? "CC" : "DC"}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </Field>

              <div className="grid grid-cols-2 gap-4">
                <Field label="Full Name" required>
                  <input
                    value={form.cardholder_name}
                    onChange={(e) => set("cardholder_name", e.target.value)}
                    placeholder="Priya Shah"
                    className={inputClass}
                  />
                </Field>
                <Field label="Email">
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => set("email", e.target.value)}
                    placeholder="priya@gmail.com"
                    className={inputClass}
                  />
                </Field>
              </div>

              {/* ── Card / Payment section ───────────────────────────────── */}
              <div className="flex items-center gap-2 mt-2 mb-1">
                <CreditCard size={13} className="text-[#8B5CF6]" />
                <span className="text-xs text-[#8B5CF6] font-semibold uppercase tracking-wide">Card Details</span>
              </div>

              {/* Payment Method selector */}
              <Field label="Payment Method" required>
                <div className="grid grid-cols-3 gap-2">
                  {(["credit_card", "debit_card", "upi"] as const).map((m) => {
                    const labels: Record<string, string> = {
                      credit_card: "💳 Credit Card",
                      debit_card:  "🏧 Debit Card",
                      upi:         "📲 UPI",
                    };
                    const active = form.payment_method === m;
                    return (
                      <button
                        key={m}
                        type="button"
                        onClick={() => set("payment_method", m)}
                        className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all ${
                          active
                            ? "bg-[#8B5CF6]/20 border-[#8B5CF6] text-[#8B5CF6]"
                            : "bg-[#0A0A0F] border-[#1E1E2E] text-gray-400 hover:border-[#8B5CF6]/40"
                        }`}
                      >
                        {labels[m]}
                      </button>
                    );
                  })}
                </div>
              </Field>

              {/* UPI fields — shown only when UPI is selected */}
              {form.payment_method === "upi" ? (
                <Field label="UPI VPA (Virtual Payment Address)" required>
                  <input
                    value={form.upi_vpa}
                    onChange={(e) => set("upi_vpa", e.target.value)}
                    placeholder="e.g. sunil@oksbi  or  9876543210@paytm"
                    className={`${inputClass} font-mono`}
                  />
                  <p className="text-[10px] text-gray-500 mt-1">
                    UPI with linked card — card details optional but improve fraud scoring
                  </p>
                </Field>
              ) : null}

              {/* Card fields — shown for Credit / Debit card, and optionally for UPI */}
              {form.payment_method !== "upi" ? (
                <>
                  <Field label={`${form.payment_method === "credit_card" ? "Credit" : "Debit"} Card Number`} required>
                    <input
                      value={form.card_number}
                      onChange={(e) => set("card_number", e.target.value)}
                      placeholder="4111 1111 1111 1111"
                      maxLength={19}
                      className={`${inputClass} font-mono`}
                    />
                  </Field>
                  <div className="grid grid-cols-3 gap-4">
                    <Field label="CVV" required>
                      <input
                        value={form.cvv}
                        onChange={(e) => set("cvv", e.target.value)}
                        placeholder="123"
                        maxLength={4}
                        className={`${inputClass} font-mono`}
                      />
                    </Field>
                    <Field label="Expiry Month">
                      <input
                        value={form.expiry_month}
                        onChange={(e) => set("expiry_month", e.target.value)}
                        placeholder="MM"
                        maxLength={2}
                        className={`${inputClass} font-mono`}
                      />
                    </Field>
                    <Field label="Expiry Year">
                      <input
                        value={form.expiry_year}
                        onChange={(e) => set("expiry_year", e.target.value)}
                        placeholder="YY"
                        maxLength={4}
                        className={`${inputClass} font-mono`}
                      />
                    </Field>
                  </div>
                </>
              ) : null}

              {/* ── Transaction section ──────────────────────────────────── */}
              <div className="flex items-center gap-2 mt-2 mb-1">
                <FlaskConical size={13} className="text-[#F59E0B]" />
                <span className="text-xs text-[#F59E0B] font-semibold uppercase tracking-wide">Transaction</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Amount (INR)" required>
                  <input
                    type="number"
                    value={form.amount}
                    onChange={(e) => set("amount", e.target.value)}
                    placeholder="e.g. 5000"
                    className={inputClass}
                  />
                </Field>
                <Field label="Purchase Type">
                  <select value={form.purchase_type} onChange={(e) => set("purchase_type", e.target.value)} className={selectClass}>
                    <option value="grocery">Grocery</option>
                    <option value="online_shopping">Online Shopping</option>
                    <option value="electronics">Electronics</option>
                    <option value="restaurant">Restaurant</option>
                    <option value="fuel">Fuel</option>
                    <option value="travel">Travel</option>
                    <option value="wire_transfer">Wire Transfer</option>
                    <option value="atm_withdrawal">ATM Withdrawal</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="crypto">Cryptocurrency</option>
                  </select>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Channel">
                  <select value={form.channel} onChange={(e) => set("channel", e.target.value)} className={selectClass}>
                    <option value="online">Online</option>
                    <option value="pos_physical">POS Physical</option>
                    <option value="atm">ATM</option>
                    <option value="mobile">Mobile</option>
                    <option value="wire">Wire / ACH</option>
                  </select>
                </Field>
                <Field label="Merchant Name">
                  <input
                    value={form.merchant_name}
                    onChange={(e) => set("merchant_name", e.target.value)}
                    placeholder="e.g. Amazon India"
                    className={inputClass}
                  />
                </Field>
              </div>

              {/* ── Location section ─────────────────────────────────────── */}
              <div className="flex items-center gap-2 mt-2 mb-1">
                <MapPin size={13} className="text-[#00FF87]" />
                <span className="text-xs text-[#00FF87] font-semibold uppercase tracking-wide">Location</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Country">
                  <select
                    value={form.country_code}
                    onChange={(e) => set("country_code", e.target.value)}
                    className={selectClass}
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.name} ({c.code})
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="City">
                  <input
                    value={form.city}
                    onChange={(e) => set("city", e.target.value)}
                    placeholder="Mumbai"
                    className={inputClass}
                  />
                </Field>
              </div>

              {/* ── Device section ───────────────────────────────────────── */}
              <div className="grid grid-cols-2 gap-4">
                <Field label="Device Type">
                  <select value={form.device_type} onChange={(e) => set("device_type", e.target.value)} className={selectClass}>
                    <option value="mobile">Mobile</option>
                    <option value="desktop">Desktop</option>
                    <option value="tablet">Tablet</option>
                    <option value="pos_terminal">POS Terminal</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </Field>
                <Field label="New Device?">
                  <select
                    value={form.is_new_device ? "yes" : "no"}
                    onChange={(e) => set("is_new_device", e.target.value === "yes")}
                    className={selectClass}
                  >
                    <option value="no">No (Known Device)</option>
                    <option value="yes">Yes (New / Unknown)</option>
                  </select>
                </Field>
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
                  onClick={() => { setForm(BLANK); setResult(null); setError(null); setLookupStatus("idle"); }}
                  className="flex items-center gap-2 text-sm text-gray-500 hover:text-white border border-[#1E1E2E] px-4 py-3 rounded-xl hover:border-gray-500 transition-all"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Results ──────────────────────────────────────────────── */}
          <div>
            {error && (
              <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-2xl p-4 mb-4 flex items-start gap-3">
                <XCircle size={16} className="text-[#EF4444] mt-0.5 shrink-0" />
                <div className="text-sm text-[#EF4444]">{error}</div>
              </div>
            )}

            {!result && !loading && !error && (
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-12 flex flex-col items-center justify-center h-full min-h-[500px]">
                <FlaskConical size={40} className="text-gray-700 mb-4" />
                <div className="text-gray-600 text-sm">Fill the form and click Run Fraud Detection</div>
                <div className="text-gray-700 text-xs mt-1">Or choose a preset scenario above · Use Lookup to auto-fill from phone</div>
              </div>
            )}

            {loading && (
              <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-12 flex flex-col items-center justify-center h-full min-h-[500px]">
                <Loader2 size={40} className="text-[#00FF87] animate-spin mb-4" />
                <div className="text-gray-400 text-sm">Running fraud detection pipeline…</div>
                <div className="text-gray-600 text-xs mt-1">Rules → Unsupervised → Supervised → Ensemble</div>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Decision banner */}
                <div
                  className="rounded-2xl p-5 border"
                  style={{ backgroundColor: `${decisionColor}12`, borderColor: `${decisionColor}40` }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-xs text-gray-400 uppercase tracking-widest font-medium">Decision</div>
                    <span className="text-2xl font-black tracking-wider" style={{ color: decisionColor }}>
                      {result.decision}
                    </span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div>
                      <div className="text-xs text-gray-500">Fraud Score</div>
                      <div className="text-3xl font-black" style={{ color: decisionColor }}>
                        {(result.risk_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Category</div>
                      <div className="text-sm font-semibold capitalize text-white">{result.fraud_category}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Risk Level</div>
                      <div className="text-sm font-semibold capitalize" style={{ color: decisionColor }}>
                        {result.risk_level || result.fraud_risk_level || "—"}
                      </div>
                    </div>
                    <div className="ml-auto">
                      {result.is_blocked ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#EF4444]">
                          <XCircle size={14} /> Blocked
                        </div>
                      ) : result.is_flagged ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#F59E0B]">
                          <AlertTriangle size={14} /> Flagged
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-[#00FF87]">
                          <CheckCircle2 size={14} /> Passed
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* ── ML Model Breakdown ──────────────────────────────────── */}
                {result.model_breakdown && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Brain size={14} className="text-[#8B5CF6]" />
                      <div className="text-xs font-semibold text-white uppercase tracking-wide">
                        ML Score Breakdown — Layer by Layer
                      </div>
                      <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-mono border ${
                        result.model_breakdown.ml_available
                          ? "text-[#00FF87] border-[#00FF87]/30 bg-[#00FF87]/8"
                          : "text-[#F59E0B] border-[#F59E0B]/30 bg-[#F59E0B]/8"
                      }`}>
                        {result.model_breakdown.ml_available ? "ML Active" : "Rules-Only Mode"}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {result.model_breakdown.layers.map((layer, idx) => {
                        const pct = Math.round(layer.score * 100);
                        const contribPct = Math.round(layer.contribution * 100);
                        const barColor =
                          layer.score < 0.30 ? "#22C55E" :
                          layer.score < 0.60 ? "#F59E0B" :
                          layer.score < 0.80 ? "#F97316" : "#EF4444";

                        return (
                          <div key={idx} className="rounded-xl border border-[#1E1E2E] bg-[#0A0A0F] p-3">
                            {/* Layer header */}
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] bg-[#1E1E2E] text-gray-400 px-1.5 py-0.5 rounded font-mono">
                                  L{idx + 1}
                                </span>
                                <span className="text-xs font-semibold text-white">{layer.name}</span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-[10px] text-gray-500">
                                  weight {Math.round(layer.weight * 100)}%
                                </span>
                                <span className="text-xs font-bold font-mono" style={{ color: barColor }}>
                                  {pct}%
                                </span>
                              </div>
                            </div>

                            {/* Score bar */}
                            <div className="h-2 bg-[#1E1E2E] rounded-full overflow-hidden mb-2">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{ width: `${pct}%`, backgroundColor: barColor }}
                              />
                            </div>

                            {/* Description */}
                            <div className="text-[10px] text-gray-500">{layer.description}</div>

                            {/* Triggered rules inline tags */}
                            {layer.triggered_rules && layer.triggered_rules.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1.5">
                                {layer.triggered_rules.map((r) => (
                                  <span key={r} className="text-[9px] bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20 px-1.5 py-0.5 rounded font-mono">
                                    {r.replace(/_/g, " ")}
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* Individual ML model scores */}
                            {layer.individual_models && Object.keys(layer.individual_models).length > 0 && (
                              <div className="mt-2 space-y-1">
                                {Object.entries(layer.individual_models).map(([modelId, score]) => {
                                  const mPct = Math.round((score as number) * 100);
                                  const mColor =
                                    (score as number) < 0.30 ? "#22C55E" :
                                    (score as number) < 0.60 ? "#F59E0B" :
                                    (score as number) < 0.80 ? "#F97316" : "#EF4444";
                                  return (
                                    <div key={modelId} className="flex items-center gap-2">
                                      <span className="text-[10px] text-gray-600 w-28 truncate capitalize font-mono">
                                        {modelId.replace(/_/g, " ")}
                                      </span>
                                      <div className="flex-1 h-1 bg-[#1E1E2E] rounded-full overflow-hidden">
                                        <div
                                          className="h-full rounded-full"
                                          style={{ width: `${mPct}%`, backgroundColor: mColor }}
                                        />
                                      </div>
                                      <span className="text-[10px] font-mono w-8 text-right" style={{ color: mColor }}>
                                        {mPct}%
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            )}

                            {/* Contribution to final score */}
                            <div className="mt-2 pt-2 border-t border-[#1E1E2E] flex items-center justify-between">
                              <span className="text-[10px] text-gray-600">Contribution to final score</span>
                              <span className="text-[10px] font-mono text-gray-400">
                                {pct}% × {Math.round(layer.weight * 100)}% = <span className="text-white font-bold">{contribPct}%</span>
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Final ensemble row */}
                    <div className="mt-3 rounded-xl border p-3 flex items-center justify-between"
                      style={{
                        borderColor: `${decisionColor}30`,
                        backgroundColor: `${decisionColor}08`,
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] bg-[#1E1E2E] text-gray-400 px-1.5 py-0.5 rounded font-mono">∑</span>
                        <span className="text-xs font-semibold text-white">Ensemble Final Score</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-32 bg-[#1E1E2E] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.round(result.model_breakdown.final_score * 100)}%`,
                              backgroundColor: decisionColor,
                            }}
                          />
                        </div>
                        <span className="text-sm font-black font-mono" style={{ color: decisionColor }}>
                          {Math.round(result.model_breakdown.final_score * 100)}%
                        </span>
                        <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ color: decisionColor, backgroundColor: `${decisionColor}15` }}>
                          {result.model_breakdown.final_decision}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── Conclusion ─────────────────────────────────────────────── */}
                {result.conclusion && (
                  <div className="rounded-2xl border p-4" style={{
                    borderColor: `${decisionColor}30`,
                    backgroundColor: `${decisionColor}06`,
                  }}>
                    <div className="flex items-center gap-2 mb-3">
                      <Brain size={14} style={{ color: decisionColor }} />
                      <div className="text-xs font-semibold uppercase tracking-wide" style={{ color: decisionColor }}>
                        ML Conclusion
                      </div>
                    </div>

                    {/* Headline */}
                    <div className="text-sm font-semibold text-white mb-2 leading-snug">
                      {result.conclusion.headline}
                    </div>

                    {/* Detailed explanation */}
                    <div className="text-xs text-gray-400 leading-relaxed mb-3">
                      {result.conclusion.detail}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {/* Risk factors */}
                      {result.conclusion.risk_factors.length > 0 && (
                        <div>
                          <div className="text-[10px] text-[#EF4444] font-semibold uppercase tracking-wide mb-1.5">
                            Risk Signals Fired
                          </div>
                          <div className="space-y-1">
                            {result.conclusion.risk_factors.map((f, i) => (
                              <div key={i} className="flex items-start gap-1.5 text-[10px] text-gray-400">
                                <span className="text-[#EF4444] mt-0.5 shrink-0">▲</span>
                                {f}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Mitigating factors */}
                      {result.conclusion.mitigating_factors.length > 0 && (
                        <div>
                          <div className="text-[10px] text-[#22C55E] font-semibold uppercase tracking-wide mb-1.5">
                            Risk Factors Absent
                          </div>
                          <div className="space-y-1">
                            {result.conclusion.mitigating_factors.map((f, i) => (
                              <div key={i} className="flex items-start gap-1.5 text-[10px] text-gray-400">
                                <span className="text-[#22C55E] mt-0.5 shrink-0">✓</span>
                                {f}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Score footnote */}
                    <div className="mt-3 pt-3 border-t border-[#1E1E2E] flex items-center gap-4 text-[10px] text-gray-600 font-mono">
                      <span>Rules score: <span className="text-gray-400">{Math.round((result.conclusion.rules_score || 0) * 100)}%</span></span>
                      <span>Final score: <span style={{ color: decisionColor }}>{Math.round((result.conclusion.final_score || 0) * 100)}%</span></span>
                      <span className={result.conclusion.ml_available ? "text-[#00FF87]" : "text-[#F59E0B]"}>
                        {result.conclusion.ml_available ? "✓ ML active" : "⚠ Rules-only mode"}
                      </span>
                    </div>
                  </div>
                )}

                {/* Transaction Summary — cardholder, card (masked), payment method */}
                <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                  <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                    Transaction Summary
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
                    <div>
                      <span className="text-gray-500">Cardholder</span>
                      <div className="text-white font-semibold mt-0.5">{form.cardholder_name || "—"}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Email</span>
                      <div className="text-white font-mono mt-0.5 truncate">{form.email || "—"}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Payment Method</span>
                      <div className="mt-0.5">
                        {form.payment_method === "credit_card" && <span className="text-[#8B5CF6] font-semibold">💳 Credit Card</span>}
                        {form.payment_method === "debit_card"  && <span className="text-[#3B82F6] font-semibold">🏧 Debit Card</span>}
                        {form.payment_method === "upi"         && <span className="text-[#00FF87] font-semibold">📲 UPI</span>}
                      </div>
                    </div>
                    <div>
                      {form.payment_method === "upi" ? (
                        <>
                          <span className="text-gray-500">UPI VPA</span>
                          <div className="text-white font-mono mt-0.5">{form.upi_vpa || "—"}</div>
                        </>
                      ) : (
                        <>
                          <span className="text-gray-500">Card (Masked)</span>
                          <div className="text-white font-mono mt-0.5">
                            {form.card_number
                              ? `**** **** **** ${form.card_number.replace(/\s|\*/g, "").slice(-4)}`
                              : "—"}
                          </div>
                        </>
                      )}
                    </div>
                    <div>
                      <span className="text-gray-500">Amount</span>
                      <div className="text-white font-semibold mt-0.5">₹{parseFloat(form.amount || "0").toLocaleString("en-IN")}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Mobile</span>
                      <div className="text-white font-mono mt-0.5">{form.mobile_number || "—"}</div>
                    </div>
                  </div>
                </div>

                {/* Detection Journey */}
                {result.journey && Object.keys(result.journey).length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                      Detection Journey
                    </div>
                    <div className="space-y-2">
                      {Object.entries(result.journey).map(([key, step], idx) => {
                        const isOk = step.ok;
                        const isSkipped = step.status?.startsWith("skipped");
                        const isPartial = step.status?.startsWith("partial");
                        const label = key.replace(/^step_/, "").replace(/_/g, " ");

                        // Human-readable status line
                        const statusText = (() => {
                          const s = step.status ?? "";
                          if (s.startsWith("sent:")) return `sent to ${s.replace("sent:", "")} recipient(s)`;
                          if (s.startsWith("partial:")) return s.replace("partial:", "partial — ");
                          if (s.startsWith("skipped:")) return `skipped — ${s.replace("skipped:", "")}`;
                          if (s.startsWith("failed:")) return s.replace("failed:", "failed: ");
                          if (s.startsWith("error:")) return s.replace("error:", "error: ");
                          return s || (isOk ? "ok" : "skipped");
                        })();

                        return (
                          <div key={key} className="flex items-start gap-3">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                              isOk
                                ? "bg-[#00FF87]/10 text-[#00FF87]"
                                : isSkipped
                                  ? "bg-[#6B7280]/20 text-gray-500"
                                  : "bg-[#F59E0B]/10 text-[#F59E0B]"
                            }`}>
                              {idx + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-white capitalize">{label}</span>
                                {step.ms != null && (
                                  <span className="text-xs text-gray-600 font-mono">{step.ms}ms</span>
                                )}
                              </div>
                              <div className={`text-xs mt-0.5 ${
                                isOk && !isPartial ? "text-gray-500"
                                : isPartial ? "text-[#F59E0B]/80"
                                : isSkipped ? "text-gray-600"
                                : "text-[#F59E0B]/80"
                              }`}>
                                {step.triggered != null && `${step.triggered} rule(s) triggered · `}
                                {step.score != null && `score: ${(step.score * 100).toFixed(1)}% · `}
                                {step.decision || statusText}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Why detected as fraud */}
                {result.reasons && result.reasons.length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Brain size={14} className="text-[#EF4444]" />
                      <div className="text-xs font-semibold text-white uppercase tracking-wide">
                        Why Was This {result.decision === "PASS" ? "Passed" : "Detected as Fraud"}?
                      </div>
                      <span className="ml-auto text-[10px] bg-[#1E1E2E] text-gray-400 px-2 py-0.5 rounded-full font-mono">
                        {result.reasons.length} signal{result.reasons.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <div className="space-y-3">
                      {result.reasons.map((r, i) => {
                        const sevColor = r.severity === "critical" ? "#EF4444"
                          : r.severity === "high"     ? "#F97316"
                          : r.severity === "medium"   ? "#F59E0B"
                          : "#22C55E";
                        const sevLabel = r.severity === "critical" ? "CRITICAL"
                          : r.severity === "high"     ? "HIGH"
                          : r.severity === "medium"   ? "MEDIUM"
                          : "LOW";
                        return (
                          <div key={i} className="rounded-xl border p-3" style={{ borderColor: `${sevColor}25`, backgroundColor: `${sevColor}06` }}>
                            <div className="flex items-center gap-2 mb-1">
                              <AlertTriangle size={11} style={{ color: sevColor }} className="shrink-0" />
                              <div className="text-xs font-semibold flex-1" style={{ color: sevColor }}>{r.title}</div>
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ color: sevColor, backgroundColor: `${sevColor}15` }}>
                                {sevLabel}
                              </span>
                            </div>
                            <div className="text-xs text-gray-400 leading-relaxed pl-4">{r.detail}</div>
                          </div>
                        );
                      })}
                    </div>
                    {/* Plain-English summary */}
                    <div className="mt-3 pt-3 border-t border-[#1E1E2E] text-xs text-gray-500 leading-relaxed">
                      {result.decision === "PASS"
                        ? "✅ All fraud signals are within normal parameters. The ML ensemble scored this transaction as low risk."
                        : result.decision === "BLOCK"
                        ? "🚫 This transaction was BLOCKED because one or more critical fraud signals exceeded the safety threshold. The ML ensemble confirmed high fraud probability."
                        : result.decision === "ALERT"
                        ? "⚠️ This transaction was FLAGGED for review. Medium-to-high fraud signals detected — requires analyst verification before proceeding."
                        : "🔶 This transaction was FLAGGED as suspicious. Monitor for further activity from this customer."}
                    </div>
                  </div>
                )}

                {/* SHAP */}
                {result.shap_explanation && result.shap_explanation.length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                        Top Fraud Contributors (SHAP)
                      </div>
                      <Info size={12} className="text-gray-600" />
                    </div>
                    <div className="space-y-2">
                      {result.shap_explanation
                        .slice()
                        .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
                        .slice(0, 8)
                        .map((entry) => {
                          const isPositive = entry.shap_value > 0;
                          const barWidth = Math.min(100, Math.abs(entry.shap_value) * 100);
                          return (
                            <div key={entry.feature} className="flex items-center gap-3">
                              <div className="w-36 text-xs text-gray-500 truncate shrink-0 capitalize">
                                {entry.feature.replace(/^feat_/, "").replace(/_/g, " ")}
                              </div>
                              <div className="flex-1 bg-[#0A0A0F] rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="h-full rounded-full"
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
                                {isPositive ? "+" : ""}{entry.shap_value.toFixed(3)}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* SMS status */}
                {result.sms_status && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4 flex items-center gap-3">
                    <MessageSquare size={14} className="text-[#3B82F6]" />
                    <div className="text-xs text-gray-400">
                      SMS Alert: <span className="text-white capitalize">{result.sms_status}</span>
                    </div>
                  </div>
                )}

                {/* Email notification status */}
                {result.email_recipients && result.email_recipients.length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                      Email Notifications
                    </div>
                    <div className="space-y-2">
                      {result.email_recipients.map((r, i) => {
                        const sent = r.status === "sent";
                        const isTestDomainErr = r.status.includes("testing emails") || r.status.includes("422");
                        return (
                          <div key={i} className="flex items-start gap-2">
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 ${
                              sent ? "bg-[#00FF87]/10 text-[#00FF87]" : "bg-[#F59E0B]/10 text-[#F59E0B]"
                            }`}>
                              {sent ? "✓" : "!"}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-xs text-white font-mono truncate">{r.to}</div>
                              <div className={`text-[10px] mt-0.5 ${sent ? "text-gray-500" : "text-[#F59E0B]/80"}`}>
                                {sent ? "delivered" : r.status.replace(/^failed:\d+:/, "").trim()}
                              </div>
                              {isTestDomainErr && (
                                <div className="text-[10px] text-[#F59E0B] mt-1 bg-[#F59E0B]/5 border border-[#F59E0B]/20 rounded px-2 py-1">
                                  Resend test domain can only deliver to your Resend account email.
                                  To send to any address, verify a custom domain at{" "}
                                  <span className="underline font-mono">resend.com/domains</span>{" "}
                                  and save it in Settings → Integrations → Verified Sender Email.
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Written to DB */}
                <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                  <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                    Transaction Written to DB
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      ["Transaction ID", result.transaction_id?.slice(0, 16) + "…"],
                      ["Amount", `₹${Number(result.amount || form.amount).toLocaleString()}`],
                      ["Channel", result.channel || form.channel],
                      ["Merchant", result.merchant_name || form.merchant_name || "—"],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <div className="text-gray-600">{k}</div>
                        <div className="text-gray-300 font-mono">{v}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Link href="/dashboard/alerts" className="text-xs text-[#F59E0B] hover:underline">
                      View Alerts →
                    </Link>
                    <span className="text-gray-600">·</span>
                    <Link href="/dashboard/transactions" className="text-xs text-[#3B82F6] hover:underline">
                      All Transactions →
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT: Transaction Details Panel (shows when result exists) ─ */}
          {result && (
            <TransactionDetailsPanel
              transaction={{
                transaction_id: result.transaction_id || "—",
                cardholder_name: form.cardholder_name,
                card_number: form.card_number,
                amount: form.amount,
                merchant_name: form.merchant_name,
                city: form.city,
                country_code: form.country_code,
                channel: form.channel,
                purchase_type: form.purchase_type,
                device_type: form.device_type,
                is_new_device: form.is_new_device,
              }}
              result={result}
              decisionColor={decisionColor}
            />
          )}
        </div>
      </main>
    </div>
  );
}
