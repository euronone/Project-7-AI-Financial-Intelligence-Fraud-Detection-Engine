"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Shield, KeyRound, AlertCircle, Loader2, CheckCircle2, ArrowLeft, Copy } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [sent, setSent]         = useState(false);
  // Dev-only: the link returned when no email service is configured
  const [devLink, setDevLink]   = useState<string | null>(null);
  const [copied, setCopied]     = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) { setError("Please enter your email address."); return; }
    setError("");
    setLoading(true);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003/api/v1";
      const res = await fetch(`${apiBase}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      const json = await res.json();

      // In development mode, the backend returns a dev_reset_link
      if (json.dev_reset_link) {
        setDevLink(json.dev_reset_link);
      }
      setSent(true);
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const copyLink = async () => {
    if (!devLink) return;
    await navigator.clipboard.writeText(devLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
          <KeyRound size={26} className="text-[#00FF87]" />
        </div>
        <h1 className="text-3xl font-black">Forgot password?</h1>
        <p className="text-gray-500 text-sm mt-2">
          Enter your email and we&apos;ll send a reset link.
        </p>
      </div>

      {!sent ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@institution.com"
              autoComplete="email"
              className="w-full bg-[#111118] border border-[#1E1E2E] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00FF87]/60 transition-colors"
            />
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
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Shield size={16} />}
            {loading ? "Sending…" : "Send Reset Link"}
          </button>
        </form>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-4"
        >
          <div className="bg-[#00FF87]/10 border border-[#00FF87]/30 rounded-2xl p-5 text-center">
            <CheckCircle2 size={32} className="text-[#00FF87] mx-auto mb-3" />
            <p className="text-sm text-gray-300">
              If <span className="text-white font-semibold">{email}</span> exists in our system,
              a reset link has been sent.
            </p>
            <p className="text-xs text-gray-600 mt-2">Check your inbox — the link expires in 1 hour.</p>
          </div>

          {/* Dev mode: show the link inline for testing */}
          {devLink && (
            <div className="bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-2xl p-4 space-y-2">
              <p className="text-xs font-mono text-[#F59E0B] font-semibold uppercase">
                Dev Mode — No email service configured
              </p>
              <p className="text-xs text-gray-400">
                Add <code className="bg-[#1E1E2E] px-1 rounded">RESEND_API_KEY</code> to your backend
                <code className="bg-[#1E1E2E] px-1 rounded ml-1">.env</code> to send real emails.
                Use this link directly:
              </p>
              <div className="flex items-center gap-2 bg-[#111118] border border-[#1E1E2E] rounded-xl p-3">
                <span className="text-xs text-gray-400 font-mono truncate flex-1">{devLink}</span>
                <button
                  onClick={copyLink}
                  className="shrink-0 text-xs text-[#00FF87] hover:underline flex items-center gap-1"
                >
                  <Copy size={11} /> {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <a
                href={devLink}
                className="block w-full text-center bg-[#F59E0B] text-black text-xs font-bold py-2 rounded-xl hover:bg-[#d97706] transition-all"
              >
                Open Reset Link →
              </a>
            </div>
          )}

          <button
            onClick={() => { setSent(false); setDevLink(null); }}
            className="w-full border border-[#1E1E2E] text-gray-400 py-3 rounded-xl hover:border-gray-500 text-sm transition-all"
          >
            Send to a different email
          </button>
        </motion.div>
      )}

      <div className="text-center mt-6">
        <Link href="/login" className="text-xs text-gray-600 hover:text-gray-400 flex items-center justify-center gap-1">
          <ArrowLeft size={12} /> Back to sign in
        </Link>
      </div>
    </motion.div>
  );
}
