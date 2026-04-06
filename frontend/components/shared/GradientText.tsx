import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface GradientTextProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "green-blue" | "purple" | "red-orange";
}

const gradients = {
  default: "bg-gradient-to-r from-[#00FF87] via-[#3B82F6] to-[#8B5CF6] bg-clip-text text-transparent",
  "green-blue": "bg-gradient-to-r from-[#00FF87] to-[#3B82F6] bg-clip-text text-transparent",
  purple: "bg-gradient-to-r from-[#8B5CF6] to-[#00FF87] bg-clip-text text-transparent",
  "red-orange": "bg-gradient-to-r from-[#EF4444] to-[#F59E0B] bg-clip-text text-transparent",
};

export default function GradientText({
  children,
  className = "",
  variant = "default",
}: GradientTextProps) {
  return (
    <span className={cn(gradients[variant], className)}>
      {children}
    </span>
  );
}
