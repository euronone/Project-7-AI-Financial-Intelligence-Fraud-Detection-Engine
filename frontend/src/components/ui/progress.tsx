import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  max?: number;
  size?: "sm" | "md" | "lg";
  color?: "primary" | "success" | "warning" | "danger";
  showLabel?: boolean;
  className?: string;
}

const barColors = {
  primary: "bg-primary-600",
  success: "bg-success-600",
  warning: "bg-warning-500",
  danger: "bg-danger-600",
};

const trackSizes = {
  sm: "h-1.5",
  md: "h-2.5",
  lg: "h-4",
};

export function Progress({ value, max = 100, size = "md", color = "primary", showLabel, className }: ProgressProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="mb-1 flex justify-between text-xs text-gray-500">
          <span>{percent.toFixed(0)}%</span>
        </div>
      )}
      <div className={cn("w-full overflow-hidden rounded-full bg-gray-200", trackSizes[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-300", barColors[color])}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
