import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface BadgeProps {
  children: ReactNode;
  variant?: "success" | "warning" | "danger" | "info" | "neutral";
  size?: "sm" | "md";
  className?: string;
}

const variants = {
  success: "bg-[#00FF87]/10 text-[#00FF87] border border-[#00FF87]/30",
  warning: "bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/30",
  danger: "bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/30",
  info: "bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/30",
  neutral: "bg-[#6B7280]/10 text-[#9CA3AF] border border-[#6B7280]/30",
};

const sizes = {
  sm: "px-2 py-1 text-[10px] font-semibold",
  md: "px-3 py-1.5 text-xs font-semibold",
};

export default function Badge({
  children,
  variant = "neutral",
  size = "md",
  className = "",
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg font-mono",
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}
