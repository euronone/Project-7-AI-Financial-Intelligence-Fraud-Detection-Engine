"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Check, ArrowRight } from "lucide-react";
import Link from "next/link";

const PLANS = [
  {
    name: "Free",
    price: "₹0",
    period: "/month",
    desc: "Perfect for evaluation and small pilots",
    color: "#00FF87",
    badge: null,
    features: [
      "10,000 transactions/month",
      "2 connectors (Supabase + CSV)",
      "5 built-in fraud rules",
      "Pre-built FinShield models",
      "Email alerts only",
      "Basic dashboard",
      "Monthly model retraining",
      "Read-only API access",
    ],
    cta: "Start Free",
    href: "/signup?plan=free",
  },
  {
    name: "Pro",
    price: "₹9,999",
    period: "/month",
    desc: "For growing fintechs and banks",
    color: "#3B82F6",
    badge: "Most Popular",
    features: [
      "500,000 transactions/month",
      "10 connectors",
      "25 custom fraud rules",
      "Pre-built + custom rules",
      "Email + SMS alerts",
      "Full analytics dashboard",
      "Weekly auto-retraining",
      "Full REST API access",
      "SHAP summaries",
      "Dedicated schema",
    ],
    cta: "Start Pro Trial",
    href: "/signup?plan=pro",
  },
  {
    name: "Advanced",
    price: "₹24,999",
    period: "/month",
    desc: "Enterprise-grade for large institutions",
    color: "#8B5CF6",
    badge: "Enterprise",
    features: [
      "Unlimited transactions",
      "All 20+ connectors",
      "Unlimited custom rules",
      "Personalized ML model",
      "Email + SMS + Call + Webhook",
      "White-label dashboard",
      "On-demand retraining",
      "Full API + WebSocket",
      "Full SHAP + audit trail",
      "Custom schema support",
      "Dedicated schema + VPC",
      "Dedicated SLA support",
    ],
    cta: "Contact Sales",
    href: "/signup?plan=advanced",
  },
];

export default function PricingSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="pricing" ref={ref} className="py-24 px-6 bg-[#0A0A0F]">
      <div className="max-w-7xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-[#F59E0B] text-sm font-mono uppercase tracking-widest">Pricing</span>
          <h2 className="text-4xl md:text-5xl font-black mt-3">
            Simple, <span className="gradient-text">transparent</span> pricing
          </h2>
          <p className="text-gray-400 mt-4">No hidden fees. Start free, scale as you grow.</p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6 items-start">
          {PLANS.map(({ name, price, period, desc, color, badge, features, cta, href }, i) => (
            <motion.div
              key={name}
              className={`relative bg-[#111118] rounded-2xl p-7 ${i === 1 ? "border-2" : "border border-[#1E1E2E]"}`}
              style={i === 1 ? { borderColor: color + "60" } : {}}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.15 }}
              whileHover={i !== 1 ? { borderColor: color + "40" } : {}}
            >
              {badge && (
                <div
                  className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold px-3 py-1 rounded-full"
                  style={{ backgroundColor: color, color: "#000" }}
                >
                  {badge}
                </div>
              )}

              {i === 1 && (
                <div
                  className="absolute inset-0 rounded-2xl opacity-5 pointer-events-none"
                  style={{ background: `radial-gradient(circle at 50% 0%, ${color}, transparent 70%)` }}
                />
              )}

              <div className="mb-6">
                <div className="text-sm font-mono" style={{ color }}>{name}</div>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-4xl font-black">{price}</span>
                  <span className="text-gray-500 text-sm">{period}</span>
                </div>
                <p className="text-sm text-gray-500 mt-2">{desc}</p>
              </div>

              <Link
                href={href}
                className="flex items-center justify-center gap-2 w-full py-3 rounded-xl font-semibold text-sm transition-all mb-6"
                style={
                  i === 1
                    ? { backgroundColor: color, color: "#000" }
                    : { border: `1px solid ${color}40`, color: color }
                }
              >
                {cta}
                <ArrowRight size={14} />
              </Link>

              <ul className="space-y-2.5">
                {features.map((f) => (
                  <li key={f} className="flex items-center gap-2.5 text-sm text-gray-400">
                    <Check size={13} style={{ color, flexShrink: 0 }} />
                    {f}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
