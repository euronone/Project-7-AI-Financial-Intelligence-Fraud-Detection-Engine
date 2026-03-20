import { cn } from "@/lib/utils";

const variants = {
  default: "bg-gray-100 text-gray-800",
  primary: "bg-primary-100 text-primary-800",
  success: "bg-success-100 text-success-800",
  warning: "bg-warning-100 text-warning-800",
  danger: "bg-danger-100 text-danger-800",
  outline: "border border-gray-300 text-gray-700 bg-transparent",
} as const;

const sizes = {
  sm: "px-1.5 py-0.5 text-[10px]",
  md: "px-2 py-0.5 text-xs",
  lg: "px-2.5 py-1 text-sm",
} as const;

interface BadgeProps {
  children: React.ReactNode;
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  dot?: boolean;
  className?: string;
}

export function Badge({ children, variant = "default", size = "md", dot, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {dot && (
        <span
          className={cn("h-1.5 w-1.5 rounded-full", {
            "bg-gray-500": variant === "default",
            "bg-primary-500": variant === "primary",
            "bg-success-500": variant === "success",
            "bg-warning-500": variant === "warning",
            "bg-danger-500": variant === "danger",
            "bg-gray-400": variant === "outline",
          })}
        />
      )}
      {children}
    </span>
  );
}
