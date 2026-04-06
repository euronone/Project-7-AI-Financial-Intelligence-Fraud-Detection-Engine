"use client";

import { ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  icon?: ReactNode;
}

const variants = {
  primary: "bg-[#00FF87] text-black hover:bg-[#00e87a] disabled:opacity-60",
  secondary: "bg-[#3B82F6] text-white hover:bg-[#2563eb] disabled:opacity-60",
  ghost: "text-white hover:bg-[#111118] disabled:opacity-60",
  outline: "border border-[#1E1E2E] text-gray-400 hover:border-gray-500 disabled:opacity-60",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3 text-base font-bold",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  icon,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={cn(
        "rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {isLoading ? <Loader2 size={16} className="animate-spin" /> : icon}
      {isLoading ? "Loading..." : children}
    </button>
  );
}
