"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Lock, Eye, Server, Trash2, CheckCircle2 } from "lucide-react";

const PRIVACY_FEATURES = [
  {
    icon: Eye,
    title: "No Data Storage",
    desc: "We don't save transaction data. Your information is used only for real-time fraud detection.",
    color: "#00FF87"
  },
  {
    icon: Lock,
    title: "End-to-End Encryption",
    desc: "All data is encrypted in transit (TLS 1.3) and at rest (AES-256). Your secrets stay yours.",
    color: "#3B82F6"
  },
  {
    icon: Server,
    title: "Your Data, Your Server",
    desc: "Connect your own database. FinShield accesses your data only when needed for fraud detection.",
    color: "#8B5CF6"
  },
  {
    icon: Trash2,
    title: "Instant Deletion",
    desc: "Fraud scores are written back to your system. Cached data expires in minutes, never stored permanently.",
    color: "#F59E0B"
  },
];

export default function PrivacySection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="privacy" ref={ref} className="py-24 px-6 bg-[#0A0A0F]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#00FF87] text-sm font-mono uppercase tracking-widest">
            Privacy First
          </span>
          <h2 className="text-4xl md:text-5xl font-black mt-3 mb-4">
            Your data stays<span className="gradient-text"> yours</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            FinShield never stores transaction data. We analyze and forget.
            Your institution controls everything.
          </p>
        </motion.div>

        {/* Privacy Features Grid */}
        <motion.div
          className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2 }}
        >
          {PRIVACY_FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div
              key={title}
              className="bg-[#111118] border border-[#1E1E2E] rounded-xl p-5 card-hover group"
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 + i * 0.1 }}
              whileHover={{ borderColor: `${color}50` }}
            >
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"
                style={{ backgroundColor: `${color}15`, border: `1px solid ${color}30` }}
              >
                <Icon size={18} style={{ color }} />
              </div>
              <h3 className="font-bold text-white mb-2">{title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Privacy Commitment Box */}
        <motion.div
          className="bg-gradient-to-r from-[#00FF87]/10 to-[#3B82F6]/10 border border-[#00FF87]/30 rounded-2xl p-8 text-center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ delay: 0.6 }}
        >
          <div className="flex justify-center mb-4">
            <CheckCircle2 size={32} className="text-[#00FF87]" />
          </div>
          <h3 className="text-2xl font-bold mb-3">
            Built for <span className="text-[#00FF87]">institutional trust</span>
          </h3>
          <p className="text-gray-300 max-w-2xl mx-auto mb-6">
            FinShield is designed for regulated institutions. Your transaction data
            never leaves your servers. We provide fraud intelligence, not data storage.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <div className="px-4 py-2 rounded-lg bg-[#00FF87]/10 border border-[#00FF87]/30 text-sm text-gray-300">
              ✓ ISO 27001 certified
            </div>
            <div className="px-4 py-2 rounded-lg bg-[#00FF87]/10 border border-[#00FF87]/30 text-sm text-gray-300">
              ✓ GDPR compliant
            </div>
            <div className="px-4 py-2 rounded-lg bg-[#00FF87]/10 border border-[#00FF87]/30 text-sm text-gray-300">
              ✓ SOC 2 Type II
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
