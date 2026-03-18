import { cn } from "@/lib/utils";
import { RISK_LEVEL_COLORS, RISK_LEVEL_LABELS } from "@/lib/constants";
import type { RiskLevel } from "@/types/transaction";

interface RiskBadgeProps {
  level: RiskLevel | null | undefined;
  className?: string;
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  if (!level) return <span className="text-gray-400 text-xs">—</span>;

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
        RISK_LEVEL_COLORS[level],
        className
      )}
    >
      {RISK_LEVEL_LABELS[level]}
    </span>
  );
}
