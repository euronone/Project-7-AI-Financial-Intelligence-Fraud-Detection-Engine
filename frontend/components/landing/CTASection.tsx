"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import Link from "next/link";
import { ArrowRight, Shield, GitBranch, BookOpen, Headphones } from "lucide-react";

export default function CTASection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="cta" ref={ref} className="py-24 px-6 bg-[#0D0D15] relative overflow-hidden">
      {/* Gradient glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#00FF87] opacity-5 rounded-full blur-3xl" />
      </div>

      <div className="max-w-4xl mx-auto text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-center gap-2 mb-6">
            <Shield size={32} className="text-[#00FF87]" />
            <span className="text-2xl font-black">
              Fin<span className="text-[#00FF87]">Shield</span> AI
            </span>
          </div>

          <h2 className="text-4xl md:text-6xl font-black mb-6">
            Ready to stop fraud
            <br />
            <span className="gradient-text">before it happens?</span>
          </h2>

          <p className="text-gray-400 text-lg mb-10 max-w-xl mx-auto">
            Join 50+ financial institutions using FinShield AI to protect their customers.
            Start free — no credit card required.
          </p>

          <div className="flex flex-wrap justify-center gap-4 mb-16">
            <Link
              href="/signup"
              className="flex items-center gap-2 bg-[#00FF87] text-black font-bold px-8 py-4 rounded-xl hover:bg-[#00e87a] transition-all hover:scale-105 text-lg"
            >
              Get Started Free
              <ArrowRight size={18} />
            </Link>
            <Link
              href="/signup?plan=pro"
              className="flex items-center gap-2 border border-[#00FF87] border-opacity-40 text-[#00FF87] font-semibold px-8 py-4 rounded-xl hover:bg-[#00FF8710] transition-all text-base"
            >
              View Pro Plan
            </Link>
          </div>

          {/* Links */}
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <a href="/docs" className="flex items-center gap-1.5 hover:text-white transition-colors">
              <BookOpen size={14} /> Documentation
            </a>
            <a href="https://github.com" className="flex items-center gap-1.5 hover:text-white transition-colors">
              <GitBranch size={14} /> GitHub
            </a>
            <a href="mailto:support@finshield.ai" className="flex items-center gap-1.5 hover:text-white transition-colors">
              <Headphones size={14} /> Support
            </a>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <motion.div
        className="mt-16 pt-8 border-t border-[#1E1E2E] text-center text-xs text-gray-600"
        initial={{ opacity: 0 }}
        animate={inView ? { opacity: 1 } : {}}
        transition={{ delay: 0.6 }}
      >
        <p>© 2026 FinShield AI. Built for financial institutions. Enterprise fraud detection platform.</p>
        <div className="flex flex-wrap justify-center gap-4 mt-3">
          <a href="/privacy" className="hover:text-gray-400 transition-colors">Privacy Policy</a>
          <a href="/terms" className="hover:text-gray-400 transition-colors">Terms of Service</a>
          <a href="/security" className="hover:text-gray-400 transition-colors">Security</a>
        </div>
      </motion.div>
    </section>
  );
}
