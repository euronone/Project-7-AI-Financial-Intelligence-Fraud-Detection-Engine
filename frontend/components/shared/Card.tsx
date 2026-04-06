import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  glow?: "green" | "blue" | "purple" | "none";
}

const glowColors = {
  green: "hover:border-[#00FF87]/50 hover:shadow-[0_0_20px_rgba(0,255,135,0.1)]",
  blue: "hover:border-[#3B82F6]/50 hover:shadow-[0_0_20px_rgba(59,130,246,0.1)]",
  purple: "hover:border-[#8B5CF6]/50 hover:shadow-[0_0_20px_rgba(139,92,246,0.1)]",
  none: "",
};

export default function Card({
  children,
  className = "",
  hoverable = true,
  glow = "none",
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-[#111118] border border-[#1E1E2E] rounded-xl transition-all duration-300",
        hoverable && "card-hover",
        glow !== "none" && glowColors[glow],
        className
      )}
    >
      {children}
    </div>
  );
}
