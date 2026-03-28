"use client";

import { useState, Suspense } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { KeyRound, Eye, EyeOff, AlertCircle, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";

function ResetPasswordForm() {
  const router      = useRouter();
  const params      = useSearchParams();
  const { token: authToken } = useAuthStore();

  // URL params set by the reset link: /reset-password?token=xxx&uid=yyy
  // For admin-forced reset: /reset-password?forced=true (use change-password endpoint)
  const resetToken  = params.get("token") || "";
  const uid         = params.get("uid")   || "";
  const forced      = params.get("forced") === "true";

  const [newPassword, setNewPassword]     = useState("");
  const [confirmPass, setConfirmPass]     = useState("");
  const [showNew,  setShowNew]            = useState(false);
  const [showConf, setShowConf]           = useState(false);
  const [currentPass, setCurrentPass]     = useState(""); // only for forced flow
  const [showCurr, setShowCurr]           = useState(false);
  const [loading, setLoading]             = useState(false);
  const [error, setError]                 = useState("");
  const [done, setDone]                   = useState(false);

  const validate = (): string | null => {
    if (newPassword.length < 8)       return "Password must be at least 8 characters";
    if (!/[A-Z]/.test(newPassword))   return "Must contain at least one uppercase letter";
    if (!/[0-9]/.test(newPassword))   return "Must contain at least one number";
    if (newPassword !== confirmPass)   return "Passwords do not match";
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setError(validationError); return; }
    setError("");
    setLoading(true);

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003/api/v1";

    try {
      let res: Response;

      if (forced && authToken) {
        // Admin-forced reset: user is logged in, uses change-password endpoint
        res = await fetch(`${apiBase}/auth/change-password`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            current_password: currentPass,
            new_password:     newPassword,
          }),
        });
      } else {
        // Token-based reset from email link
        if (!resetToken || !uid) {
          setError("Invalid reset link. Please request a new one.");
          setLoading(false);
          return;
        }
        res = await fetch(`${apiBase}/auth/reset-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            token:        resetToken,
            uid:          uid,
            new_password: newPassword,
          }),
        });
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to reset password");
      }

      setDone(true);
      setTimeout(() => router.push("/login"), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reset failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <motion.div
        className="text-center py-8"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="w-16 h-16 rounded-full bg-[#00FF87]/10 border border-[#00FF87]/30 flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 size={30} className="text-[#00FF87]" />
        </div>
        <h2 className="text-xl font-black mb-2">Password updated!</h2>
        <p className="text-gray-400 text-sm">Redirecting to sign in…</p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Forced-reset: require current password first */}
      {forced && (
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Current (temporary) password</label>
          <div className="relative">
            <input
              value={currentPass}
              onChange={(e) => setCurrentPass(e.target.value)}
              type={showCurr ? "text" : "password"}
              placeholder="Your current password"
              className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
            />
            <button type="button" onClick={() => setShowCurr(v => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
              {showCurr ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm text-gray-400 mb-1.5">New password</label>
        <div className="relative">
          <input
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            type={showNew ? "text" : "password"}
            placeholder="Min 8 chars, 1 uppercase, 1 number"
            className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
          />
          <button type="button" onClick={() => setShowNew(v => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
            {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        {/* Password strength indicators */}
        <div className="flex gap-2 mt-2">
          {[
            { label: "8+ chars", ok: newPassword.length >= 8 },
            { label: "Uppercase", ok: /[A-Z]/.test(newPassword) },
            { label: "Number",    ok: /[0-9]/.test(newPassword) },
          ].map(({ label, ok }) => (
            <span
              key={label}
              className="text-[10px] px-2 py-0.5 rounded-full font-mono transition-all"
              style={{
                color: ok ? "#00FF87" : "#6B7280",
                backgroundColor: ok ? "#00FF8715" : "#11111820",
                border: `1px solid ${ok ? "#00FF8740" : "#1E1E2E"}`,
              }}
            >
              {ok ? "✓" : "○"} {label}
            </span>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1.5">Confirm new password</label>
        <div className="relative">
          <input
            value={confirmPass}
            onChange={(e) => setConfirmPass(e.target.value)}
            type={showConf ? "text" : "password"}
            placeholder="Repeat new password"
            className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
          />
          <button type="button" onClick={() => setShowConf(v => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
            {showConf ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      {error && (
        <motion.div
          className="flex items-center gap-2 p-3 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-sm text-[#EF4444]"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        >
          <AlertCircle size={14} /> {error}
        </motion.div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-[#00FF87] text-black font-bold py-3 rounded-xl hover:bg-[#00e87a] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <KeyRound size={16} />}
        {loading ? "Updating password…" : "Set New Password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0A0A0F]" />}>
      <motion.div
        className="max-w-md mx-auto"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#00FF87]/10 border border-[#00FF87]/30 mb-4">
            <KeyRound size={26} className="text-[#00FF87]" />
          </div>
          <h1 className="text-3xl font-black">Set new password</h1>
          <p className="text-gray-500 text-sm mt-2">Choose a strong password for your account.</p>
        </div>

        <ResetPasswordForm />

        <div className="text-center mt-6">
          <Link href="/login" className="text-xs text-gray-600 hover:text-gray-400 flex items-center justify-center gap-1">
            <ArrowLeft size={12} /> Back to sign in
          </Link>
        </div>
      </motion.div>
    </Suspense>
  );
}
