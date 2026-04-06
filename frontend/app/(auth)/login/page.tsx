"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Shield, Zap, AlertCircle, Loader2, KeyRound } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { apiClient } from "@/lib/api-client";
import PrivacyBanner from "@/components/shared/PrivacyBanner";

const schema = z.object({
  email:    z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});
type FormData = z.infer<typeof schema>;

const DEMO_ACCOUNTS = [
  {
    label: "Admin",
    email: "admin@finshield.local",
    password: "Admin123!@#",
    role: "admin" as const,
    color: "#00FF87",
    institution: "FinShield Demo Bank",
    plan: "advanced" as const,
  },
  {
    label: "Analyst",
    email: "analyst@finshield.local",
    password: "Analyst123!@#",
    role: "analyst" as const,
    color: "#3B82F6",
    institution: "FinShield Demo Bank",
    plan: "pro" as const,
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { setUser, completeOnboarding } = useAuthStore();
  const [showPass, setShowPass]   = useState(false);
  const [error, setError]         = useState("");
  const [loading, setLoading]     = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const handleDemoLogin = (demo: (typeof DEMO_ACCOUNTS)[0]) => {
    setValue("email",    demo.email);
    setValue("password", demo.password);
  };

  const onSubmit = async (data: FormData) => {
    setError("");
    setLoading(true);

    try {
      const json = await apiClient.login(data.email, data.password);
      const u = json.user as Record<string, unknown>;

      setUser(
        {
          id:               u.id as string,
          email:            u.email as string,
          full_name:        u.full_name as string,
          phone_number:     u.phone_number as string,
          role:             u.role as "admin" | "analyst" | "viewer",
          institution_name: (u.institution_name as string) || "FinShield Demo Bank",
          institution_type: (u.institution_type as string) || "bank",
          plan:             (u.plan as "free" | "pro" | "advanced") || "free",
          avatar_initials:  (u.avatar_initials as string) || (u.full_name as string).slice(0, 2).toUpperCase(),
          must_change_password: u.must_change_password as boolean,
        },
        json.access_token
      );

      if (u.has_completed_onboarding) {
        completeOnboarding({ db_type: "supabase", db_url: "" });
      }

      // If admin forced a password reset, redirect to change-password first
      if (u.must_change_password) {
        router.push("/reset-password?forced=true");
        return;
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="max-w-md mx-auto"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#00FF87]/10 border border-[#00FF87]/30 mb-4">
          <Shield size={26} className="text-[#00FF87]" />
        </div>
        <h1 className="text-3xl font-black">Welcome back</h1>
        <p className="text-gray-500 text-sm mt-2">Sign in to your FinShield dashboard</p>
      </div>

      {/* Demo accounts */}
      <div className="mb-6">
        <p className="text-xs text-gray-600 text-center mb-3 font-mono uppercase tracking-wider">
          Quick Demo Access
        </p>
        <div className="grid grid-cols-2 gap-3">
          {DEMO_ACCOUNTS.map((demo) => (
            <button
              key={demo.role}
              onClick={() => handleDemoLogin(demo)}
              className="flex items-center gap-2.5 p-3 rounded-xl border border-[#1E1E2E] hover:border-opacity-80 transition-all text-left group"
              style={{ borderColor: `${demo.color}30` }}
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
                style={{ backgroundColor: `${demo.color}20`, color: demo.color }}
              >
                <Zap size={14} />
              </div>
              <div>
                <div className="text-xs font-semibold" style={{ color: demo.color }}>
                  {demo.label}
                </div>
                <div className="text-[10px] text-gray-600 font-mono">{demo.plan}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 h-px bg-[#1E1E2E]" />
        <span className="text-xs text-gray-600">or sign in with email</span>
        <div className="flex-1 h-px bg-[#1E1E2E]" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email */}
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Email address</label>
          <input
            {...register("email")}
            type="email"
            placeholder="you@institution.com"
            autoComplete="email"
            className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87] focus:border-opacity-60 transition-colors"
          />
          {errors.email && (
            <p className="text-xs text-[#EF4444] mt-1 flex items-center gap-1">
              <AlertCircle size={11} /> {errors.email.message}
            </p>
          )}
        </div>

        {/* Password */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm text-gray-400">Password</label>
            {/* ✅ FIXED: Forgot password now navigates to dedicated page */}
            <Link
              href="/forgot-password"
              className="text-xs text-[#00FF87] hover:underline flex items-center gap-1"
            >
              <KeyRound size={11} /> Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              {...register("password")}
              type={showPass ? "text" : "password"}
              placeholder="••••••••"
              autoComplete="current-password"
              className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87] focus:border-opacity-60 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition-colors"
            >
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.password && (
            <p className="text-xs text-[#EF4444] mt-1 flex items-center gap-1">
              <AlertCircle size={11} /> {errors.password.message}
            </p>
          )}
        </div>

        {/* Error */}
        {error && (
          <motion.div
            className="flex items-center gap-2 p-3 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-sm text-[#EF4444]"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <AlertCircle size={14} />
            {error}
          </motion.div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : null}
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <p className="text-center text-sm text-gray-600 mt-6">
        No account?{" "}
        <Link href="/signup" className="text-[#00FF87] hover:underline font-medium">
          Create one free
        </Link>
      </p>

      <PrivacyBanner variant="footer" />
    </motion.div>
  );
}
