"use client";

import { cn } from "@/lib/utils";
import type { RiskDistribution } from "@/types/risk";

interface RiskDistributionChartProps {
  data: RiskDistribution;
  className?: string;
}

const SEGMENTS = [
  { key: "low" as const, label: "Low", color: "bg-success-500", textColor: "text-success-700" },
  { key: "medium_low" as const, label: "Med-Low", color: "bg-success-300", textColor: "text-success-600" },
  { key: "medium" as const, label: "Medium", color: "bg-warning-400", textColor: "text-warning-700" },
  { key: "high" as const, label: "High", color: "bg-danger-400", textColor: "text-danger-600" },
  { key: "critical" as const, label: "Critical", color: "bg-danger-600", textColor: "text-danger-700" },
];

export function RiskDistributionChart({ data, className }: RiskDistributionChartProps) {
  const total = data.total || 1;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Stacked bar */}
      <div className="flex h-8 w-full overflow-hidden rounded-lg">
        {SEGMENTS.map(({ key, color }) => {
          const pct = (data[key] / total) * 100;
          if (pct === 0) return null;
          return (
            <div
              key={key}
              className={cn("transition-all duration-500", color)}
              style={{ width: `${pct}%` }}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-5 gap-2 text-center">
        {SEGMENTS.map(({ key, label, color, textColor }) => (
          <div key={key}>
            <div className="flex items-center justify-center gap-1.5">
              <span className={cn("inline-block h-2.5 w-2.5 rounded-full", color)} />
              <span className="text-xs text-gray-500">{label}</span>
            </div>
            <p className={cn("text-lg font-bold", textColor)}>{data[key]}</p>
            <p className="text-xs text-gray-400">{((data[key] / total) * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
