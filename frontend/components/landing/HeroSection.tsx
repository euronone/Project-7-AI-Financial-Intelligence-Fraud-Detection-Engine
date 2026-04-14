"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Shield, Zap, ArrowRight, Activity } from "lucide-react";

const LIVE_METRICS = [
  { label: "Fraud Score", value: "0.91", color: "#EF4444", status: "BLOCKED" },
  { label: "Fraud Score", value: "0.12", color: "#00FF87", status: "PASSED" },
  { label: "Fraud Score", value: "0.67", color: "#F59E0B", status: "FLAGGED" },
];

function AnimatedGraph() {
  const points = [20, 45, 30, 65, 40, 80, 55, 35, 70, 50, 90, 60, 75, 45, 85];
  const maxH = 100;
  const w = 300;
  const h = 100;
  const step = w / (points.length - 1);

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${h - (p / maxH) * h}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-24 opacity-40">
      <defs>
        <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#00FF87" />
          <stop offset="100%" stopColor="#3B82F6" />
        </linearGradient>
        <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#00FF87" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#00FF87" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`${path} L ${(points.length - 1) * step} ${h} L 0 ${h} Z`}
        fill="url(#areaGrad)"
      />
      <motion.path
        d={path}
        fill="none"
        stroke="url(#lineGrad)"
        strokeWidth="2"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
      />
      {points.map((p, i) => (
        <motion.circle
          key={i}
          cx={i * step}
          cy={h - (p / maxH) * h}
          r="2.5"
          fill={p > 60 ? "#EF4444" : "#00FF87"}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5 + i * 0.1 }}
        />
      ))}
    </svg>
  );
}

function FraudScoreWidget() {
  return (
    <motion.div
      className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 w-72 shadow-2xl"
      initial={{ opacity: 0, y: 30, rotate: 3 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ duration: 0.8, delay: 0.6 }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Live Fraud Detection</span>
        <motion.span
          className="w-2 h-2 rounded-full bg-[#00FF87]"
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        />
      </div>

      <AnimatedGraph />

      <div className="mt-3 space-y-2">
        {LIVE_METRICS.map((m, i) => (
          <motion.div
            key={i}
            className="flex items-center justify-between text-xs"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.2 + i * 0.15 }}
          >
            <span className="text-gray-400">{m.label}</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-[#1E1E2E] rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: m.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${parseFloat(m.value) * 100}%` }}
                  transition={{ delay: 1.4 + i * 0.15, duration: 0.8 }}
                />
              </div>
              <span className="font-mono" style={{ color: m.color }}>{m.value}</span>
              <span
                className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                style={{
                  color: m.color,
                  backgroundColor: `${m.color}20`,
                  border: `1px solid ${m.color}40`
                }}
              >
                {m.status}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-[#1E1E2E] flex items-center gap-2">
        <Activity size={12} className="text-[#00FF87]" />
        <span className="text-[10px] text-gray-500 font-mono">18ms avg inference · 96.4% accuracy</span>
      </div>
    </motion.div>
  );
}

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-[#0A0A0F]">
      {/* Grid background */}
      <div className="absolute inset-0 grid-bg opacity-50" />

      {/* Radial glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#00FF87] opacity-5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#3B82F6] opacity-5 rounded-full blur-3xl" />
      </div>

      {/* Navbar */}
      <nav className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 md:px-12 py-5">
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Shield size={24} className="text-[#00FF87]" />
          <span className="text-xl font-bold tracking-tight">
            Fin<span className="text-[#00FF87]">Shield</span> AI
          </span>
        </motion.div>

        <motion.div
          className="hidden md:flex items-center gap-8"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {[
            { label: "Features", href: "#features" },
            { label: "Pricing", href: "#pricing" },
            { label: "How It Works", href: "#how-it-works" },
            { label: "Docs", href: "/docs" },
          ].map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              {item.label}
            </a>
          ))}
        </motion.div>

        <motion.div
          className="flex items-center gap-3"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Link
            href="/login"
            className="text-sm text-gray-300 hover:text-white transition-colors px-4 py-2"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="text-sm bg-[#00FF87] text-black font-semibold px-4 py-2 rounded-lg hover:bg-[#00e87a] transition-colors"
          >
            Get Started Free
          </Link>
        </motion.div>
      </nav>

      {/* Main hero content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 w-full pt-24 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 items-center">

          {/* Left: Text */}
          <div>
            <motion.div
              className="inline-flex items-center gap-2 bg-[#111118] border border-[#1E1E2E] rounded-full px-4 py-2 mb-6"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Zap size={12} className="text-[#00FF87]" />
              <span className="text-xs text-gray-400">Real-time ML · &lt;100ms · 96.4% accuracy</span>
            </motion.div>

            <motion.h1
              className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-none mb-6"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4 }}
            >
              Stop Fraud
              <br />
              <span className="gradient-text">Before It</span>
              <br />
              Happens
            </motion.h1>

            <motion.p
              className="text-lg text-gray-400 leading-relaxed mb-8 max-w-lg"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.55 }}
            >
              Real-time ML-powered fraud detection for banks, fintechs, and insurance companies.
              Connect your data, train models, and block fraud in milliseconds.
            </motion.p>

            <motion.div
              className="flex flex-wrap gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
            >
              <Link
                href="/signup"
                className="flex items-center gap-2 bg-[#00FF87] text-black font-bold px-6 py-3 rounded-xl hover:bg-[#00e87a] transition-all hover:scale-105 active:scale-95"
              >
                Get Started Free
                <ArrowRight size={16} />
              </Link>
              <a
                href="#how-it-works"
                className="flex items-center gap-2 border border-[#1E1E2E] text-white px-6 py-3 rounded-xl hover:border-[#00FF87] hover:text-[#00FF87] transition-all"
              >
                View Demo
              </a>
            </motion.div>

            {/* Stats row */}
            <motion.div
              className="flex flex-wrap gap-8 mt-12 pt-8 border-t border-[#1E1E2E]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.9 }}
            >
              {[
                { value: "10M+", label: "Transactions/day" },
                { value: "99.7%", label: "Uptime SLA" },
                { value: "<18ms", label: "Avg latency" },
                { value: "200+", label: "ML features" },
              ].map((stat) => (
                <div key={stat.label}>
                  <div className="text-2xl font-black text-[#00FF87]">{stat.value}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{stat.label}</div>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right: Floating widget */}
          <div className="flex justify-center lg:justify-end">
            <motion.div
              className="relative"
              animate={{ y: [0, -10, 0] }}
              transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
            >
              <FraudScoreWidget />

              {/* Floating badges */}
              <motion.div
                className="absolute -top-4 -left-8 bg-[#EF444420] border border-[#EF444440] rounded-xl px-3 py-2 text-xs"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.8 }}
              >
                <span className="text-[#EF4444] font-bold">🚨 BLOCKED</span>
                <div className="text-gray-500 mt-0.5">Impossible travel</div>
              </motion.div>

              <motion.div
                className="absolute -bottom-4 -right-8 bg-[#00FF8720] border border-[#00FF8740] rounded-xl px-3 py-2 text-xs"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.0 }}
              >
                <span className="text-[#00FF87] font-bold">✓ PASSED</span>
                <div className="text-gray-500 mt-0.5">Score: 0.04</div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0A0A0F] to-transparent" />
    </section>
  );
}
