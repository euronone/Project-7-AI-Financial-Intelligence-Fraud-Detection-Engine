"use client";

import { cn } from "@/lib/utils";
import { formatFraudScore } from "@/lib/formatters";
import type { RiskLevel } from "@/types/transaction";

interface FraudScoreIndicatorProps {
  score: string | number | null;
  riskLevel?: RiskLevel | null;
  showLabel?: boolean;
  className?: string;
}

function getBarColor(score: number): string {
  if (score >= 0.8) return "bg-red-500";
  if (score >= 0.6) return "bg-orange-500";
  if (score >= 0.3) return "bg-yellow-400";
  return "bg-green-500";
}

export function FraudScoreIndicator({
  score,
  riskLevel,
  showLabel = true,
  className,
}: FraudScoreIndicatorProps) {
  if (score === null || score === undefined) {
    return <span className="text-gray-400 text-xs">—</span>;
  }

  const num = typeof score === "string" ? parseFloat(score) : score;
  const pct = Math.min(Math.max(num * 100, 0), 100);
  const barColor = getBarColor(num);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 bg-gray-200 rounded-full h-1.5 min-w-[60px]">
        <div
          className={cn("h-1.5 rounded-full transition-all", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono text-gray-700 w-10 text-right">
          {formatFraudScore(num)}
        </span>
      )}
    </div>
  );
}
