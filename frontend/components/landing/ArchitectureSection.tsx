"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

const LAYERS = [
  {
    label: "Data Sources",
    items: ["Supabase", "PostgreSQL", "Stripe", "Kafka", "CSV", "+15 more"],
    color: "#3B82F6",
  },
  {
    label: "Ingestion Layer",
    items: ["Schema Normalizer", "CDC Polling", "Batch Import", "Webhook Receiver"],
    color: "#8B5CF6",
  },
  {
    label: "Feature Engineering",
    items: ["200+ Features", "Velocity", "Geo", "Device", "Behavioral"],
    color: "#F59E0B",
  },
  {
    label: "ML Engine",
    items: ["Isolation Forest", "XGBoost", "Neural Net (ONNX)", "Ensemble"],
    color: "#00FF87",
  },
  {
    label: "Action Layer",
    items: ["Rules Engine", "Decision Engine", "Alert Creator", "Score Write-back"],
    color: "#EF4444",
  },
  {
    label: "Dashboard & API",
    items: ["Next.js UI", "FastAPI REST", "WebSocket", "SHAP Reports"],
    color: "#3B82F6",
  },
];

export default function ArchitectureSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="architecture" ref={ref} className="py-24 px-6 bg-[#0D0D15]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#3B82F6] text-sm font-mono uppercase tracking-widest">Architecture</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            Built for <span className="gradient-text">scale & speed</span>
          </h2>
        </motion.div>

        {/* Architecture diagram */}
        <div className="space-y-3">
          {LAYERS.map(({ label, items, color }, i) => (
            <motion.div
              key={label}
              className="relative"
              initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: i * 0.1 }}
            >
              <div className="flex items-center gap-4">
                <div
                  className="text-xs font-mono w-36 text-right flex-shrink-0"
                  style={{ color }}
                >
                  {label}
                </div>
                <div
                  className="flex-1 flex flex-wrap gap-2 bg-[#111118] border rounded-xl p-3"
                  style={{ borderColor: `${color}30` }}
                >
                  {items.map((item) => (
                    <span
                      key={item}
                      className="text-xs px-2.5 py-1 rounded-lg"
                      style={{
                        backgroundColor: `${color}15`,
                        color: color,
                        border: `1px solid ${color}25`,
                      }}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
              {i < LAYERS.length - 1 && (
                <div
                  className="w-px h-3 mx-auto ml-[10.5rem]"
                  style={{ backgroundColor: `${color}40` }}
                />
              )}
            </motion.div>
          ))}
        </div>

        {/* Tech stack */}
        <motion.div
          className="mt-12 grid sm:grid-cols-3 gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8 }}
        >
          {[
            { label: "Frontend", items: "Next.js 14 · Tailwind · Zustand · Recharts · Framer Motion", color: "#3B82F6" },
            { label: "Backend", items: "FastAPI · SQLAlchemy 2.0 · Redis · Celery · Pydantic v2", color: "#00FF87" },
            { label: "ML Stack", items: "scikit-learn · XGBoost · PyTorch · ONNX Runtime · SHAP", color: "#8B5CF6" },
          ].map(({ label, items, color }) => (
            <div
              key={label}
              className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-4"
            >
              <div className="text-xs font-mono mb-2" style={{ color }}>{label}</div>
              <div className="text-xs text-gray-500">{items}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
