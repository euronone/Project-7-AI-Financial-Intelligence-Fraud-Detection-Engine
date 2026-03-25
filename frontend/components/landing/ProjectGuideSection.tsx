"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Building2, Rocket, ShieldCheck, CreditCard, FileText } from "lucide-react";

const USE_CASES = [
  { icon: Building2, label: "Retail Bank", use: "Card-not-present fraud, impossible travel", color: "#3B82F6" },
  { icon: Rocket, label: "Neobank", use: "Account takeover, identity fraud", color: "#8B5CF6" },
  { icon: FileText, label: "Insurance", use: "Claim fraud from spending pattern changes", color: "#F59E0B" },
  { icon: CreditCard, label: "Payment Gateway", use: "Real-time transaction screening", color: "#EF4444" },
  { icon: ShieldCheck, label: "Fintech Lending", use: "Loan application fraud, velocity patterns", color: "#00FF87" },
];

const STEPS = [
  { step: "01", title: "Sign Up", desc: "Choose Free / Pro / Advanced plan for your institution" },
  { step: "02", title: "Connect Data", desc: "Provide API keys or DB credentials for your transaction data" },
  { step: "03", title: "Model Training", desc: "System auto-trains ML models on your historical data" },
  { step: "04", title: "Real-Time Scoring", desc: "Every new transaction is scored by the ML engine in <20ms" },
  { step: "05", title: "Smart Alerts", desc: "Suspicious transactions trigger automated SMS/email/in-app alerts" },
  { step: "06", title: "Investigate & Improve", desc: "Review alerts, manage cases, and retrain models with feedback" },
];

export default function ProjectGuideSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="guide" ref={ref} className="py-24 px-6 bg-[#0D0D15]">
      <div className="max-w-7xl mx-auto">

        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#00FF87] text-sm font-mono uppercase tracking-widest">Project Guide</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3 mb-4">
            What is <span className="gradient-text">FinShield AI?</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            An end-to-end fraud detection platform that connects to your databases,
            trains ML models on your data, and provides real-time fraud scoring.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          {/* Who it's for */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="text-2xl">🏦</span> Who Is It For?
            </h3>
            <div className="space-y-3">
              {USE_CASES.map(({ icon: Icon, label, use, color }, i) => (
                <motion.div
                  key={label}
                  className="flex items-start gap-4 bg-[#111118] border border-[#1E1E2E] rounded-xl p-4 card-hover"
                  initial={{ opacity: 0, x: -20 }}
                  animate={inView ? { opacity: 1, x: 0 } : {}}
                  transition={{ delay: 0.3 + i * 0.08 }}
                >
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: `${color}20`, border: `1px solid ${color}40` }}
                  >
                    <Icon size={16} style={{ color }} />
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{label}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{use}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* How it works steps */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="text-2xl">🔄</span> How Does It Work?
            </h3>
            <div className="space-y-3">
              {STEPS.map(({ step, title, desc }, i) => (
                <motion.div
                  key={step}
                  className="flex gap-4"
                  initial={{ opacity: 0, y: 10 }}
                  animate={inView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.4 + i * 0.08 }}
                >
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-[#00FF87] text-black flex items-center justify-center text-xs font-black flex-shrink-0">
                      {step}
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className="w-px flex-1 bg-[#1E1E2E] my-1" />
                    )}
                  </div>
                  <div className="pb-3">
                    <div className="font-semibold text-sm">{title}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Summary box */}
        <motion.div
          className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 font-mono text-sm"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-[#EF4444]" />
            <div className="w-3 h-3 rounded-full bg-[#F59E0B]" />
            <div className="w-3 h-3 rounded-full bg-[#00FF87]" />
            <span className="ml-2 text-gray-500 text-xs">finshield-overview.txt</span>
          </div>
          <pre className="text-gray-300 text-xs leading-relaxed overflow-x-auto">{`📖 WHAT IS FINSHIELD AI?
FinShield AI is an end-to-end fraud detection platform designed for financial
institutions. It connects to customer and transaction databases, trains ML
models on historical data, and provides real-time fraud scoring with alerting.

🎯 KEY METRICS:
  - Fraud detection accuracy:  96.4%
  - Average inference time:    <18ms
  - False positive rate:       <2.4%
  - Supported connectors:      20+
  - ML features engineered:    200+
  - Supported alert channels:  SMS, Email, Push, Voice, Webhook`}</pre>
        </motion.div>

      </div>
    </section>
  );
}
