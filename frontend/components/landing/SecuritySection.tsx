"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Lock, Shield, Eye, Key, Database, Globe } from "lucide-react";

const BADGES = [
  { label: "ISO 27001", desc: "Information Security Management" },
  { label: "SOC 2 Type II", desc: "Security & Availability" },
  { label: "PCI-DSS", desc: "Payment Card Industry Standard" },
  { label: "GDPR", desc: "European Data Privacy" },
];

const SECURITY_FEATURES = [
  { icon: Lock, title: "AES-256 Encryption", desc: "All credentials and PII encrypted at rest. TLS 1.3 in transit.", color: "#00FF87" },
  { icon: Shield, title: "JWT + RBAC", desc: "15-minute access tokens, 7-day refresh, role-based access control per tenant.", color: "#3B82F6" },
  { icon: Eye, title: "Row-Level Security", desc: "Supabase RLS policies ensure zero cross-tenant data leakage.", color: "#8B5CF6" },
  { icon: Key, title: "API Key Rotation", desc: "Automatic key rotation with audit trail. Keys encrypted with per-tenant keys.", color: "#F59E0B" },
  { icon: Database, title: "Data Isolation", desc: "Dedicated schemas for Pro/Advanced. Shared schema with RLS for Free.", color: "#EF4444" },
  { icon: Globe, title: "Rate Limiting", desc: "1K/min (Free), 5K/min (Pro), Unlimited (Advanced) per tenant.", color: "#00FF87" },
];

export default function SecuritySection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="security" ref={ref} className="py-24 px-6 bg-[#0D0D15]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#00FF87] text-sm font-mono uppercase tracking-widest">Security & Compliance</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            Enterprise-grade <span className="gradient-text">security by default</span>
          </h2>
        </motion.div>

        {/* Compliance badges */}
        <motion.div
          className="flex flex-wrap justify-center gap-4 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2 }}
        >
          {BADGES.map(({ label, desc }, i) => (
            <motion.div
              key={label}
              className="bg-[#111118] border border-[#00FF87] border-opacity-30 rounded-xl px-6 py-4 text-center glow-green"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={inView ? { opacity: 1, scale: 1 } : {}}
              transition={{ delay: 0.3 + i * 0.1 }}
            >
              <div className="text-[#00FF87] font-bold text-sm">{label}</div>
              <div className="text-gray-500 text-xs mt-1">{desc}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Security features grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {SECURITY_FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div
              key={title}
              className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-5 card-hover"
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.4 + i * 0.08 }}
              whileHover={{ borderColor: color + "50" }}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${color}15`, border: `1px solid ${color}30` }}
                >
                  <Icon size={16} style={{ color }} />
                </div>
                <h3 className="font-semibold text-sm">{title}</h3>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
