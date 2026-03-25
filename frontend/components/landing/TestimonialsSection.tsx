"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useEffect, useState } from "react";

const STATS = [
  { value: 10000000, label: "Transactions/day", suffix: "+", color: "#00FF87" },
  { value: 94, label: "Fraud Caught (%)", suffix: "%", color: "#3B82F6" },
  { value: 50, label: "Institutions Served", suffix: "+", color: "#8B5CF6" },
  { value: 18, label: "Avg Latency (ms)", suffix: "ms", color: "#F59E0B" },
];

const TESTIMONIALS = [
  {
    quote: "FinShield reduced our card fraud losses by 73% in the first quarter. The ML explainability made our compliance team very happy.",
    name: "Priya Agarwal",
    role: "Head of Risk, Neobank India",
    avatar: "PA",
    color: "#00FF87",
  },
  {
    quote: "The impossible travel detection alone blocked 40+ fraudulent international transactions on day one. Setup took 2 hours.",
    name: "Raj Mehta",
    role: "CTO, Fintech Lending Platform",
    avatar: "RM",
    color: "#3B82F6",
  },
  {
    quote: "We connected our Supabase DB, trained the model overnight, and had live fraud scoring by morning. Exceptional product.",
    name: "Anjali Shah",
    role: "VP Engineering, Digital Bank",
    avatar: "AS",
    color: "#8B5CF6",
  },
];

function AnimatedCounter({ value, suffix }: { value: number; suffix: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    const duration = 2000;
    const steps = 60;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + increment, value);
      setCount(Math.floor(current));
      if (current >= value) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [inView, value]);

  const display = value >= 1000000
    ? `${(count / 1000000).toFixed(1)}M`
    : count.toLocaleString("en-IN");

  return <span ref={ref}>{display}{suffix}</span>;
}

export default function TestimonialsSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="testimonials" ref={ref} className="py-24 px-6 bg-[#0A0A0F]">
      <div className="max-w-7xl mx-auto">
        {/* Animated counters */}
        <motion.div
          className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          {STATS.map(({ value, label, suffix, color }) => (
            <div
              key={label}
              className="text-center bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6"
            >
              <div className="text-3xl md:text-4xl font-black mb-2" style={{ color }}>
                <AnimatedCounter value={value} suffix={suffix} />
              </div>
              <div className="text-xs text-gray-500">{label}</div>
            </div>
          ))}
        </motion.div>

        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-3xl md:text-4xl font-black">
            Trusted by <span className="gradient-text">financial innovators</span>
          </h2>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {TESTIMONIALS.map(({ quote, name, role, avatar, color }, i) => (
            <motion.div
              key={name}
              className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-6 card-hover"
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.4 + i * 0.15 }}
              whileHover={{ borderColor: color + "50" }}
            >
              <div className="text-3xl mb-4" style={{ color, opacity: 0.5 }}>&ldquo;</div>
              <p className="text-gray-300 text-sm leading-relaxed mb-6">{quote}</p>
              <div className="flex items-center gap-3">
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}
                >
                  {avatar}
                </div>
                <div>
                  <div className="text-sm font-semibold">{name}</div>
                  <div className="text-xs text-gray-500">{role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
