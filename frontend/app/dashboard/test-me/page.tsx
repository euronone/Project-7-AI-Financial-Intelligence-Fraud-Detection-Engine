"use client";

import { useAuthStore, isAdmin } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Shield, LogOut, Settings, AlertTriangle, TrendingUp, Activity,
  Users, Database, FlaskConical, Loader2, Play, RefreshCw,
  CheckCircle2, XCircle, Info, Brain, CreditCard, User,
  MessageSquare, Search, MapPin,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

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

interface SimResult {
  transaction_id: string;
  prediction: string;
  risk_score: number;
  risk_level: string;
  decision: string;
  reasons: ReasonCard[];
  shap_explanation: Record<string, number> | null;
  journey: Record<string, { ok: boolean; ms?: number; triggered?: number; status?: string; model?: string; score?: number; decision?: string; is_test?: boolean }>;
  sms_status: string | null;
  fraud_category: string;
  fraud_risk_level: string | null;
  is_blocked: boolean;
  is_flagged: boolean;
  amount?: number;
  channel?: string;
  merchant_name?: string;
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
  user: { avatar_initials: string; full_name: string; email: string; plan: string };
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
    { icon: Brain,         label: "ML Details",    href: "/dashboard/ml-details",   active: false },
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

  // Phone lookup state
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupStatus, setLookupStatus] = useState<"idle" | "found" | "not_found">("idle");
  const [lookupMsg, setLookupMsg] = useState("");

  useEffect(() => {
    if (!isAuthenticated) { router.replace("/login"); }
  }, [isAuthenticated, router]);

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
        setForm((f) => ({
          ...f,
          cardholder_name: res.cardholder_name || f.cardholder_name,
          email: res.email || f.email,
          city: res.city || f.city,
          country_code: res.country_code || f.country_code,
          customer_id: res.customer_id,
          // Pre-fill last 4 into card number field if it's empty
          card_number: f.card_number || `**** **** **** ${res.card_last4}`,
        }));
        setLookupStatus("found");
        setLookupMsg(
          `Found: ${res.cardholder_name} · ${res.customer_tier} · KYC ${res.kyc_status} · Risk ${(res.risk_score * 100).toFixed(0)}%`
        );
      }
    } catch {
      setLookupStatus("not_found");
      setLookupMsg("No customer found with this phone number — fill details manually.");
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
      const expiryYear = rawYear < 100 ? 2000 + rawYear : rawYear;

      const payload: Record<string, unknown> = {
        cardholder_name: form.cardholder_name || "Test User",
        card_number:     form.card_number.replace(/\s|\*/g, "") || "4111111111111111",
        cvv:             form.cvv || "123",
        expiry_month:    parseInt(form.expiry_month || "12"),
        expiry_year:     expiryYear,
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
        <div className="flex items-start justify-between mb-8">
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

        <div className="grid grid-cols-2 gap-8">
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

              {/* ── Card section ─────────────────────────────────────────── */}
              <div className="flex items-center gap-2 mt-2 mb-1">
                <CreditCard size={13} className="text-[#8B5CF6]" />
                <span className="text-xs text-[#8B5CF6] font-semibold uppercase tracking-wide">Card Details</span>
              </div>
              <Field label="Card Number" required>
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

                {/* Detection Journey */}
                {result.journey && Object.keys(result.journey).length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                      Detection Journey
                    </div>
                    <div className="space-y-2">
                      {Object.entries(result.journey).map(([key, step], idx) => {
                        const isOk = step.ok;
                        const label = key.replace(/^step_/, "").replace(/_/g, " ");
                        return (
                          <div key={key} className="flex items-start gap-3">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                              !isOk
                                ? "bg-[#6B7280]/20 text-gray-500"
                                : "bg-[#00FF87]/10 text-[#00FF87]"
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
                              <div className="text-xs text-gray-500 mt-0.5">
                                {step.triggered != null && `${step.triggered} rule(s) triggered · `}
                                {step.score != null && `score: ${(step.score * 100).toFixed(1)}% · `}
                                {step.decision || (isOk ? "ok" : "skipped")}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Fraud Signals */}
                {result.reasons && result.reasons.length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
                      Fraud Signals ({result.reasons.length})
                    </div>
                    <div className="space-y-3">
                      {result.reasons.map((r, i) => {
                        const sevColor = r.severity === "critical" ? "#EF4444"
                          : r.severity === "high"     ? "#F97316"
                          : r.severity === "medium"   ? "#F59E0B"
                          : "#6B7280";
                        return (
                          <div key={i} className="flex items-start gap-2">
                            <AlertTriangle size={12} className="shrink-0 mt-0.5" style={{ color: sevColor }} />
                            <div>
                              <div className="text-xs font-semibold" style={{ color: sevColor }}>{r.title}</div>
                              <div className="text-xs text-gray-400 mt-0.5 leading-relaxed">{r.detail}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* SHAP */}
                {result.shap_explanation && Object.keys(result.shap_explanation).length > 0 && (
                  <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                        Top Fraud Contributors (SHAP)
                      </div>
                      <Info size={12} className="text-gray-600" />
                    </div>
                    <div className="space-y-2">
                      {Object.entries(result.shap_explanation)
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
                                {isPositive ? "+" : ""}{val.toFixed(3)}
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
        </div>
      </main>
    </div>
  );
}
