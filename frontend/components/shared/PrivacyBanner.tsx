"use client";

import { motion } from "framer-motion";
import { Lock, Info } from "lucide-react";
import { useState } from "react";

interface PrivacyBannerProps {
  variant?: "inline" | "modal" | "footer";
  fullMessage?: boolean;
}

export default function PrivacyBanner({
  variant = "inline",
  fullMessage = false
}: PrivacyBannerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (variant === "footer") {
    return (
      <div className="text-center text-xs text-gray-500 pt-6 border-t border-[#1E1E2E]">
        <p className="flex items-center justify-center gap-1">
          <Lock size={12} className="text-[#00FF87]" />
          We don&apos;t save or store any of your transaction data
        </p>
        <p className="text-[11px] text-gray-600 mt-1">
          FinShield uses your data only for real-time fraud detection
        </p>
      </div>
    );
  }

  if (variant === "modal") {
    return (
      <motion.div
        className="bg-[#00FF87]/10 border border-[#00FF87]/30 rounded-xl p-4 mb-6"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-start gap-3">
          <Lock size={16} className="text-[#00FF87] mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-[#00FF87] mb-1">
              Your Privacy is Protected
            </p>
            <p className="text-xs text-gray-300">
              We don&apos;t save or store transaction data. Your information is encrypted
              and used only for real-time fraud detection. Learn more in our{" "}
              <a href="#" className="underline hover:opacity-80">
                privacy policy
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#00FF87]/5 border border-[#00FF87]/20 hover:border-[#00FF87]/40 transition-colors cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Lock size={14} className="text-[#00FF87] flex-shrink-0" />
      <span className="text-xs text-gray-400">
        {fullMessage ? "We don't save your data" : "Privacy protected"}
      </span>
      <Info size={12} className="text-gray-600" />
    </motion.div>
  );
}
