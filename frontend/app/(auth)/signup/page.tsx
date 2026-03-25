"use client";

import { useState, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  User, Building2, CreditCard, CheckCircle2,
  Eye, EyeOff, AlertCircle, Loader2, Check, ArrowRight, ArrowLeft,
} from "lucide-react";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import { useAuthStore } from "@/store/auth-store";

/* ─── Schemas ─────────────────────────────────────────── */
const step1Schema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Enter a valid email"),
  phone_number: z.string()
    .min(10, "Enter a valid phone number")
    .regex(/^[+]?[0-9\s\-()]{10,15}$/, "Enter a valid phone number"),
  password: z.string().min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[0-9]/, "Must contain a number"),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

const step2Schema = z.object({
  institution_name: z.string().min(2, "Institution name required"),
  institution_type: z.enum(["bank", "fintech", "insurance", "payment_processor", "neobank"], {
    error: "Select institution type",
  }),
  country: z.string().min(2, "Country required"),
});

type Step1 = z.infer<typeof step1Schema>;
type Step2 = z.infer<typeof step2Schema>;

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "₹0/mo",
    color: "#00FF87",
    features: ["10K transactions/mo", "2 connectors", "5 rules", "Email alerts"],
  },
  {
    id: "pro",
    name: "Pro",
    price: "₹9,999/mo",
    color: "#3B82F6",
    recommended: true,
    features: ["500K transactions/mo", "10 connectors", "25 rules", "SMS + Email"],
  },
  {
    id: "advanced",
    name: "Advanced",
    price: "₹24,999/mo",
    color: "#8B5CF6",
    features: ["Unlimited", "20+ connectors", "Unlimited rules", "All channels + SLA"],
  },
] as const;

const STEPS = [
  { label: "Personal", icon: User },
  { label: "Institution", icon: Building2 },
  { label: "Plan", icon: CreditCard },
  { label: "Review", icon: CheckCircle2 },
];

const INSTITUTION_TYPES = [
  { value: "bank", label: "Bank / Credit Union" },
  { value: "fintech", label: "Fintech Startup" },
  { value: "insurance", label: "Insurance Company" },
  { value: "payment_processor", label: "Payment Processor" },
  { value: "neobank", label: "Neobank / Digital Bank" },
];

const COUNTRIES = [
  "India", "United States", "United Kingdom", "Singapore", "UAE",
  "Australia", "Canada", "Germany", "France", "Japan",
];

/* ─── Field components ─────────────────────────────────── */
function Field({
  label, error, children,
}: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
      {children}
      {error && (
        <p className="text-xs text-[#EF4444] mt-1 flex items-center gap-1">
          <AlertCircle size={11} /> {error}
        </p>
      )}
    </div>
  );
}

const inputCls =
  "w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors";

const COUNTRY_CODES = [
  { code: "+91",  flag: "🇮🇳", name: "India" },
  { code: "+1",   flag: "🇺🇸", name: "United States" },
  { code: "+1",   flag: "🇨🇦", name: "Canada" },
  { code: "+44",  flag: "🇬🇧", name: "United Kingdom" },
  { code: "+61",  flag: "🇦🇺", name: "Australia" },
  { code: "+971", flag: "🇦🇪", name: "UAE" },
  { code: "+65",  flag: "🇸🇬", name: "Singapore" },
  { code: "+49",  flag: "🇩🇪", name: "Germany" },
  { code: "+33",  flag: "🇫🇷", name: "France" },
  { code: "+81",  flag: "🇯🇵", name: "Japan" },
  { code: "+86",  flag: "🇨🇳", name: "China" },
  { code: "+55",  flag: "🇧🇷", name: "Brazil" },
  { code: "+27",  flag: "🇿🇦", name: "South Africa" },
  { code: "+234", flag: "🇳🇬", name: "Nigeria" },
  { code: "+20",  flag: "🇪🇬", name: "Egypt" },
  { code: "+62",  flag: "🇮🇩", name: "Indonesia" },
  { code: "+60",  flag: "🇲🇾", name: "Malaysia" },
  { code: "+63",  flag: "🇵🇭", name: "Philippines" },
  { code: "+82",  flag: "🇰🇷", name: "South Korea" },
  { code: "+92",  flag: "🇵🇰", name: "Pakistan" },
  { code: "+880", flag: "🇧🇩", name: "Bangladesh" },
  { code: "+94",  flag: "🇱🇰", name: "Sri Lanka" },
  { code: "+977", flag: "🇳🇵", name: "Nepal" },
  { code: "+966", flag: "🇸🇦", name: "Saudi Arabia" },
  { code: "+974", flag: "🇶🇦", name: "Qatar" },
  { code: "+973", flag: "🇧🇭", name: "Bahrain" },
  { code: "+968", flag: "🇴🇲", name: "Oman" },
  { code: "+965", flag: "🇰🇼", name: "Kuwait" },
  { code: "+7",   flag: "🇷🇺", name: "Russia" },
  { code: "+31",  flag: "🇳🇱", name: "Netherlands" },
  { code: "+41",  flag: "🇨🇭", name: "Switzerland" },
  { code: "+34",  flag: "🇪🇸", name: "Spain" },
  { code: "+39",  flag: "🇮🇹", name: "Italy" },
  { code: "+46",  flag: "🇸🇪", name: "Sweden" },
  { code: "+47",  flag: "🇳🇴", name: "Norway" },
  { code: "+45",  flag: "🇩🇰", name: "Denmark" },
  { code: "+358", flag: "🇫🇮", name: "Finland" },
  { code: "+64",  flag: "🇳🇿", name: "New Zealand" },
  { code: "+52",  flag: "🇲🇽", name: "Mexico" },
  { code: "+54",  flag: "🇦🇷", name: "Argentina" },
  { code: "+56",  flag: "🇨🇱", name: "Chile" },
  { code: "+57",  flag: "🇨🇴", name: "Colombia" },
];

/* ─── Main component ───────────────────────────────────── */
function SignupPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { setUser } = useAuthStore();

  const [step, setStep] = useState(1);
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>(params.get("plan") || "free");
  const [dialCode, setDialCode] = useState("+91");
  const [formData, setFormData] = useState<Partial<Step1 & Step2>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const form1 = useForm<Step1>({ resolver: zodResolver(step1Schema) });
  const form2 = useForm<Step2>({ resolver: zodResolver(step2Schema) });

  /* Step navigation */
  const nextStep1 = form1.handleSubmit((data) => {
    setFormData((p) => ({ ...p, ...data }));
    setStep(2);
  });

  const nextStep2 = form2.handleSubmit((data) => {
    setFormData((p) => ({ ...p, ...data }));
    setStep(3);
  });

  /* Final submit */
  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      // If Supabase not configured, create demo session and redirect
      if (!isSupabaseConfigured) {
        setUser(
          {
            id: `local-${Date.now()}`,
            email: formData.email!,
            full_name: formData.full_name!,
            role: "admin",
            institution_name: formData.institution_name!,
            institution_type: formData.institution_type!,
            plan: selectedPlan as "free" | "pro" | "advanced",
            avatar_initials: formData.full_name!.slice(0, 2).toUpperCase(),
          },
          "local-session-token"
        );
        setDone(true);
        setTimeout(() => router.push("/dashboard"), 2000);
        return;
      }

      const { data: authData, error: authErr } = await supabase.auth.signUp({
        email: formData.email!,
        password: formData.password!,
        options: {
          data: {
            full_name: formData.full_name,
            phone_number: `${dialCode} ${formData.phone_number}`,
            institution_name: formData.institution_name,
            institution_type: formData.institution_type,
            country: formData.country,
            plan: selectedPlan,
            role: "admin",
          },
        },
      });

      if (authErr) throw new Error(authErr.message);

      // Auto login after signup
      setUser(
        {
          id: authData.user?.id || "new-user",
          email: formData.email!,
          full_name: formData.full_name!,
          role: "admin",
          institution_name: formData.institution_name!,
          institution_type: formData.institution_type!,
          plan: selectedPlan as "free" | "pro" | "advanced",
          avatar_initials: formData.full_name!.slice(0, 2).toUpperCase(),
        },
        authData.session?.access_token || "pending-verification"
      );

      setDone(true);
      setTimeout(() => router.push("/dashboard"), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  /* ─── Success screen ───────────────────────────── */
  if (done) {
    return (
      <motion.div
        className="max-w-md mx-auto text-center py-16"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="w-20 h-20 rounded-full bg-[#00FF87]/10 border border-[#00FF87]/40 flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 size={40} className="text-[#00FF87]" />
        </div>
        <h2 className="text-3xl font-black mb-2">You&apos;re in!</h2>
        <p className="text-gray-400">Redirecting to your dashboard...</p>
      </motion.div>
    );
  }

  /* ─── Step indicator ───────────────────────────── */
  const StepBar = () => (
    <div className="flex items-center justify-center mb-8 gap-0">
      {STEPS.map(({ label, icon: Icon }, i) => {
        const n = i + 1;
        const active = step === n;
        const done = step > n;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
                style={{
                  backgroundColor: done ? "#00FF87" : active ? "#00FF8720" : "#111118",
                  border: `2px solid ${done || active ? "#00FF87" : "#1E1E2E"}`,
                  color: done ? "#000" : active ? "#00FF87" : "#4B5563",
                }}
              >
                {done ? <Check size={14} /> : <Icon size={14} />}
              </div>
              <span
                className="text-[10px] mt-1 font-mono"
                style={{ color: active ? "#00FF87" : done ? "#00FF8780" : "#4B5563" }}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className="w-12 h-px mb-5 transition-all duration-500"
                style={{ backgroundColor: step > n ? "#00FF87" : "#1E1E2E" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );

  const slideVariants = {
    enter: { opacity: 0, x: 30 },
    center: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -30 },
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-6">
        <h1 className="text-3xl font-black">Create your account</h1>
        <p className="text-gray-500 text-sm mt-1">Set up fraud detection for your institution</p>
      </div>

      <StepBar />

      <AnimatePresence mode="wait">
        {/* ── STEP 1: Personal Info ── */}
        {step === 1 && (
          <motion.div
            key="step1"
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <Field label="Full Name" error={form1.formState.errors.full_name?.message}>
              <input
                {...form1.register("full_name")}
                placeholder="Rajesh Kumar Sharma"
                className={inputCls}
              />
            </Field>
            <Field label="Email Address" error={form1.formState.errors.email?.message}>
              <input
                {...form1.register("email")}
                type="email"
                placeholder="you@institution.com"
                className={inputCls}
              />
            </Field>
            <Field label="Mobile Number" error={form1.formState.errors.phone_number?.message}>
              <div className="flex gap-2">
                <select
                  value={dialCode}
                  onChange={(e) => setDialCode(e.target.value)}
                  className="bg-[#111118] border border-[#1E1E2E] rounded-xl px-2 py-3 text-sm text-white focus:outline-none focus:border-[#00FF87]/60 transition-colors flex-shrink-0 w-36"
                >
                  {COUNTRY_CODES.map((c) => (
                    <option key={`${c.flag}-${c.code}`} value={c.code}>
                      {c.flag} {c.code} {c.name}
                    </option>
                  ))}
                </select>
                <input
                  {...form1.register("phone_number")}
                  type="tel"
                  placeholder="98765 43210"
                  className={inputCls}
                />
              </div>
            </Field>
            <Field label="Password" error={form1.formState.errors.password?.message}>
              <div className="relative">
                <input
                  {...form1.register("password")}
                  type={showPass ? "text" : "password"}
                  placeholder="Min 8 chars, 1 uppercase, 1 number"
                  className={`${inputCls} pr-11`}
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </Field>
            <Field label="Confirm Password" error={form1.formState.errors.confirm_password?.message}>
              <div className="relative">
                <input
                  {...form1.register("confirm_password")}
                  type={showConfirm ? "text" : "password"}
                  placeholder="Repeat password"
                  className={`${inputCls} pr-11`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </Field>
            <button
              onClick={nextStep1}
              className="w-full bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all flex items-center justify-center gap-2 mt-2"
            >
              Continue <ArrowRight size={16} />
            </button>
          </motion.div>
        )}

        {/* ── STEP 2: Institution ── */}
        {step === 2 && (
          <motion.div
            key="step2"
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <Field label="Institution Name" error={form2.formState.errors.institution_name?.message}>
              <input
                {...form2.register("institution_name")}
                placeholder="Acme Bank Ltd."
                className={inputCls}
              />
            </Field>
            <Field label="Institution Type" error={form2.formState.errors.institution_type?.message}>
              <select {...form2.register("institution_type")} className={inputCls}>
                <option value="">Select type...</option>
                {INSTITUTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Country / Jurisdiction" error={form2.formState.errors.country?.message}>
              <select {...form2.register("country")} className={inputCls}>
                <option value="">Select country...</option>
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </Field>
            <div className="flex gap-3 mt-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 border border-[#1E1E2E] text-gray-400 font-semibold py-3 rounded-xl hover:border-gray-500 transition-all flex items-center justify-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                onClick={nextStep2}
                className="flex-[2] bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all flex items-center justify-center gap-2"
              >
                Continue <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {/* ── STEP 3: Plan Selection ── */}
        {step === 3 && (
          <motion.div
            key="step3"
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <div className="space-y-3 mb-6">
              {PLANS.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan.id)}
                  className="w-full text-left p-4 rounded-xl border-2 transition-all"
                  style={{
                    borderColor: selectedPlan === plan.id ? plan.color : "#1E1E2E",
                    backgroundColor: selectedPlan === plan.id ? `${plan.color}08` : "#111118",
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                        style={{ borderColor: plan.color }}
                      >
                        {selectedPlan === plan.id && (
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: plan.color }} />
                        )}
                      </div>
                      <span className="font-bold text-sm" style={{ color: plan.color }}>{plan.name}</span>
                      {"recommended" in plan && plan.recommended && (
                        <span className="text-[9px] bg-[#3B82F6] text-white px-1.5 py-0.5 rounded font-bold">POPULAR</span>
                      )}
                    </div>
                    <span className="font-mono text-sm text-gray-300">{plan.price}</span>
                  </div>
                  <div className="flex flex-wrap gap-2 ml-6">
                    {plan.features.map((f) => (
                      <span key={f} className="text-[10px] text-gray-500 flex items-center gap-1">
                        <Check size={9} style={{ color: plan.color }} /> {f}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setStep(2)}
                className="flex-1 border border-[#1E1E2E] text-gray-400 font-semibold py-3 rounded-xl hover:border-gray-500 transition-all flex items-center justify-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                onClick={() => setStep(4)}
                className="flex-[2] bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all flex items-center justify-center gap-2"
              >
                Continue <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {/* ── STEP 4: Review ── */}
        {step === 4 && (
          <motion.div
            key="step4"
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 mb-5 space-y-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider font-mono">Review your details</h3>

              {[
                { label: "Full Name", value: formData.full_name },
                { label: "Email", value: formData.email },
                { label: "Mobile", value: formData.phone_number ? `${dialCode} ${formData.phone_number}` : "—" },
                { label: "Institution", value: formData.institution_name },
                { label: "Type", value: INSTITUTION_TYPES.find((t) => t.value === formData.institution_type)?.label },
                { label: "Country", value: formData.country },
                { label: "Plan", value: PLANS.find((p) => p.id === selectedPlan)?.name + " — " + PLANS.find((p) => p.id === selectedPlan)?.price },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-sm border-b border-[#1E1E2E] pb-2 last:border-0 last:pb-0">
                  <span className="text-gray-500">{label}</span>
                  <span className="text-white font-medium text-right max-w-[200px] truncate">{value}</span>
                </div>
              ))}
            </div>

            {error && (
              <motion.div
                className="flex items-center gap-2 p-3 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-sm text-[#EF4444] mb-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <AlertCircle size={14} /> {error}
              </motion.div>
            )}

            <p className="text-xs text-gray-600 text-center mb-4">
              By creating an account, you agree to our{" "}
              <a href="#" className="text-[#00FF87] hover:underline">Terms</a> and{" "}
              <a href="#" className="text-[#00FF87] hover:underline">Privacy Policy</a>.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(3)}
                className="flex-1 border border-[#1E1E2E] text-gray-400 font-semibold py-3 rounded-xl hover:border-gray-500 transition-all flex items-center justify-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-[2] bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <p className="text-center text-sm text-gray-600 mt-6">
        Already have an account?{" "}
        <Link href="/login" className="text-[#00FF87] hover:underline font-medium">Sign in</Link>
      </p>
    </div>
  );
}

export default function SignupPageWrapper() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0A0A0F]" />}>
      <SignupPage />
    </Suspense>
  );
}
