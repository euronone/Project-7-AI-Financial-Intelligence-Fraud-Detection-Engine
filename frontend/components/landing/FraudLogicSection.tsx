"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useState } from "react";

const SIGNALS = [
  {
    category: "Amount",
    icon: "💰",
    color: "#F59E0B",
    rules: [
      { name: "Transaction Deviation", threshold: "> 3σ above avg", level: "HIGH" },
      { name: "Structuring / Smurfing", threshold: "5× < ₹8L in 24h", level: "CRITICAL" },
      { name: "First High-Value Txn", threshold: "> 3× account balance", level: "HIGH" },
    ],
  },
  {
    category: "Velocity",
    icon: "⚡",
    color: "#EF4444",
    rules: [
      { name: "Frequency Spike", threshold: "> 5× baseline / 1h", level: "HIGH" },
      { name: "Rapid Succession", threshold: "5+ txns in 10 min", level: "MEDIUM" },
      { name: "Geographic Velocity", threshold: "> 500 km / 30 min", level: "CRITICAL" },
    ],
  },
  {
    category: "Geographic",
    icon: "🌍",
    color: "#3B82F6",
    rules: [
      { name: "Impossible Travel", threshold: "> 900 km/h between txns", level: "CRITICAL" },
      { name: "New Country", threshold: "First txn in this country", level: "MEDIUM" },
      { name: "High-Risk Country", threshold: "Sanctioned jurisdiction", level: "CRITICAL" },
    ],
  },
  {
    category: "Device",
    icon: "📱",
    color: "#8B5CF6",
    rules: [
      { name: "New Device", threshold: "Unknown fingerprint", level: "MEDIUM" },
      { name: "Proxy / VPN", threshold: "IP flagged as proxy", level: "MEDIUM" },
      { name: "Tor Network", threshold: "Tor exit node detected", level: "CRITICAL" },
    ],
  },
  {
    category: "Behavioral",
    icon: "🧠",
    color: "#00FF87",
    rules: [
      { name: "Unusual Hour", threshold: "2–4 AM vs profile", level: "LOW" },
      { name: "Account Takeover", threshold: "Password reset + txn < 30m", level: "CRITICAL" },
      { name: "Failed Auth Before Txn", threshold: "3+ failed logins", level: "HIGH" },
    ],
  },
];

const LEVEL_COLORS: Record<string, string> = {
  LOW: "#6B7280",
  MEDIUM: "#F59E0B",
  HIGH: "#EF4444",
  CRITICAL: "#DC2626",
};

const SCORE_DECISIONS = [
  { range: "< 0.30", label: "PASS", color: "#00FF87", bg: "#00FF8720", desc: "Allow, log silently" },
  { range: "0.30–0.59", label: "FLAG", color: "#F59E0B", bg: "#F59E0B20", desc: "Allow + analyst email" },
  { range: "0.60–0.79", label: "ALERT", color: "#EF4444", bg: "#EF444420", desc: "SMS + Email + review" },
  { range: "≥ 0.80", label: "BLOCK", color: "#DC2626", bg: "#DC262620", desc: "Block + auto-case" },
];

export default function FraudLogicSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const [active, setActive] = useState(0);

  return (
    <section id="fraud-logic" ref={ref} className="py-24 px-6 bg-[#0A0A0F]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#EF4444] text-sm font-mono uppercase tracking-widest">Fraud Detection Logic</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            5 signal categories, <span className="gradient-text">infinite protection</span>
          </h2>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Signal tabs */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="flex gap-2 flex-wrap mb-6">
              {SIGNALS.map(({ category, icon, color }, i) => (
                <button
                  key={category}
                  onClick={() => setActive(i)}
                  className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-all"
                  style={
                    active === i
                      ? { backgroundColor: `${color}20`, color, border: `1px solid ${color}50` }
                      : { border: "1px solid #1E1E2E", color: "#6B7280" }
                  }
                >
                  <span>{icon}</span> {category}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              {SIGNALS[active].rules.map(({ name, threshold, level }, i) => (
                <motion.div
                  key={`${active}-${name}`}
                  className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold">{name}</span>
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded"
                      style={{
                        color: LEVEL_COLORS[level],
                        backgroundColor: `${LEVEL_COLORS[level]}20`,
                        border: `1px solid ${LEVEL_COLORS[level]}30`,
                      }}
                    >
                      {level}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 font-mono">{threshold}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Decision matrix */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h3 className="text-lg font-bold mb-4">Score → Decision Matrix</h3>
            <div className="space-y-3 mb-8">
              {SCORE_DECISIONS.map(({ range, label, color, bg, desc }) => (
                <div
                  key={label}
                  className="flex items-center gap-4 rounded-xl p-4"
                  style={{ backgroundColor: bg, border: `1px solid ${color}30` }}
                >
                  <div className="font-mono text-sm w-24 text-center" style={{ color }}>
                    {range}
                  </div>
                  <div
                    className="font-black text-sm w-16 text-center px-2 py-1 rounded"
                    style={{ backgroundColor: `${color}30`, color }}
                  >
                    {label}
                  </div>
                  <div className="text-xs text-gray-400">{desc}</div>
                </div>
              ))}
            </div>

            {/* Animated gauge */}
            <div className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-5">
              <div className="text-xs text-gray-500 font-mono mb-3">{"// Live fraud score gauge"}</div>
              <div className="relative h-3 bg-[#1E1E2E] rounded-full overflow-hidden mb-2">
                <div className="absolute inset-0 bg-gradient-to-r from-[#00FF87] via-[#F59E0B] to-[#EF4444]" />
                <motion.div
                  className="absolute right-0 top-0 bottom-0 bg-[#111118]"
                  animate={{ right: ["20%", "60%", "10%", "85%"] }}
                  transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-gray-600 font-mono">
                <span>0.0 SAFE</span>
                <span>0.3 FLAG</span>
                <span>0.6 ALERT</span>
                <span>0.8 BLOCK</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
