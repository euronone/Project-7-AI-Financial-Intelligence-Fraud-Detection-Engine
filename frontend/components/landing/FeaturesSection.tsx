"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Brain, Zap, Plug, LayoutDashboard, Bell, Building } from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Multi-Layer ML Detection",
    desc: "4-layer architecture: Rules → Isolation Forest → XGBoost/RF/NN → Ensemble. 200+ engineered features per transaction.",
    color: "#00FF87",
    tag: "96.4% accuracy",
  },
  {
    icon: Zap,
    title: "Real-Time Scoring <100ms",
    desc: "ONNX-optimized neural network inference. Fraud scored before transaction settles. P95 latency under 50ms.",
    color: "#3B82F6",
    tag: "18ms avg",
  },
  {
    icon: Plug,
    title: "20+ Data Connectors",
    desc: "Supabase, PostgreSQL, MySQL, Stripe, Razorpay, Kafka, CSV, and 13 more. Auto schema normalization.",
    color: "#8B5CF6",
    tag: "Plug & Play",
  },
  {
    icon: LayoutDashboard,
    title: "Live Admin Dashboard",
    desc: "Real-time KPIs, fraud trends, geographic heatmaps, model performance, and SHAP explanability charts.",
    color: "#F59E0B",
    tag: "WebSocket",
  },
  {
    icon: Bell,
    title: "Multi-Channel Alerts",
    desc: "SMS via Twilio, email via Resend, Firebase push notifications, phone calls, Slack, and custom webhooks.",
    color: "#EF4444",
    tag: "5 channels",
  },
  {
    icon: Building,
    title: "Multi-Tenant Architecture",
    desc: "Row-level security isolates data per institution. Dedicated schemas for Pro/Advanced. Global model sharing for Free.",
    color: "#00FF87",
    tag: "Enterprise-ready",
  },
];

export default function FeaturesSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="features" ref={ref} className="py-24 px-6 bg-[#0D0D15]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#8B5CF6] text-sm font-mono uppercase tracking-widest">Features</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            Everything you need to <span className="gradient-text">fight fraud</span>
          </h2>
        </motion.div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc, color, tag }, i) => (
            <motion.div
              key={title}
              className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 card-hover group"
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              whileHover={{ borderColor: color + "60" }}
            >
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: `${color}15`, border: `1px solid ${color}30` }}
                >
                  <Icon size={22} style={{ color }} />
                </div>
                <span
                  className="text-[10px] font-mono px-2 py-1 rounded-full"
                  style={{
                    color: color,
                    backgroundColor: `${color}15`,
                    border: `1px solid ${color}30`,
                  }}
                >
                  {tag}
                </span>
              </div>
              <h3 className="font-bold text-base mb-2">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
