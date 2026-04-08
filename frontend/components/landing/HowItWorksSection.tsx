"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Database, Cpu, AlertTriangle, Search, TrendingUp, Plug } from "lucide-react";

const STEPS = [
  {
    icon: Plug,
    title: "Connect",
    desc: "Link your Supabase, PostgreSQL, MySQL or 20+ supported data sources in minutes",
    color: "#3B82F6",
    num: "01",
  },
  {
    icon: Database,
    title: "Ingest",
    desc: "Automatic schema normalization pulls historical transactions and customer data",
    color: "#8B5CF6",
    num: "02",
  },
  {
    icon: Cpu,
    title: "Detect",
    desc: "200+ ML features scored across 4 detection layers: Rules → Anomaly → Supervised → Ensemble",
    color: "#00FF87",
    num: "03",
  },
  {
    icon: AlertTriangle,
    title: "Alert",
    desc: "Multi-channel notifications via SMS, email, push, and in-app for suspicious activity",
    color: "#F59E0B",
    num: "04",
  },
  {
    icon: Search,
    title: "Investigate",
    desc: "Case management dashboard with SHAP explainability to review and resolve alerts",
    color: "#EF4444",
    num: "05",
  },
  {
    icon: TrendingUp,
    title: "Improve",
    desc: "Feedback loop retrains models weekly. Each confirmed fraud makes detection smarter",
    color: "#00FF87",
    num: "06",
  },
];

export default function HowItWorksSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="how-it-works" ref={ref} className="py-24 px-6 bg-[#0A0A0F]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#3B82F6] text-sm font-mono uppercase tracking-widest">How It Works</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            Six steps to <span className="gradient-text-purple">zero fraud</span>
          </h2>
        </motion.div>

        <div className="relative">
          {/* Connecting line (desktop) */}
          <div className="hidden lg:block absolute top-16 left-[8.33%] right-[8.33%] h-px bg-gradient-to-r from-[#3B82F6] via-[#00FF87] to-[#EF4444] opacity-30" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
            {STEPS.map(({ icon: Icon, title, desc, color, num }, i) => (
              <motion.div
                key={title}
                className="relative bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 text-center card-hover"
                initial={{ opacity: 0, y: 30 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                style={{
                  "--hover-color": color,
                } as React.CSSProperties}
                whileHover={{ borderColor: color + "80" }}
              >
                <div className="relative z-10">
                  <div
                    className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center"
                    style={{ backgroundColor: `${color}20`, border: `1px solid ${color}40` }}
                  >
                    <Icon size={20} style={{ color }} />
                  </div>
                  <div
                    className="text-xs font-mono mb-1"
                    style={{ color: color + "80" }}
                  >
                    {num}
                  </div>
                  <h3 className="font-bold text-sm mb-2" style={{ color }}>
                    {title}
                  </h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Pipeline visualization */}
        <motion.div
          className="mt-16 bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 font-mono text-xs"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8 }}
        >
          <div className="text-gray-500 mb-3">{"// 4-Layer ML Detection Pipeline"}</div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-[#3B82F6]">Rules Engine</span>
            <span className="text-gray-600">→</span>
            <span className="text-[#8B5CF6]">Isolation Forest</span>
            <span className="text-gray-600">→</span>
            <span className="text-[#F59E0B]">XGBoost + RF + NN</span>
            <span className="text-gray-600">→</span>
            <span className="text-[#00FF87]">Ensemble Scorer</span>
            <span className="text-gray-600">→</span>
            <span className="px-2 py-0.5 rounded" style={{ background: "#EF444420", color: "#EF4444", border: "1px solid #EF444440" }}>
              DECISION
            </span>
          </div>
          <div className="mt-3 text-gray-600">
            avg_latency: <span className="text-[#00FF87]">18ms</span> ·
            precision: <span className="text-[#00FF87]">0.91</span> ·
            recall: <span className="text-[#00FF87]">0.88</span> ·
            auc_roc: <span className="text-[#00FF87]">0.967</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
