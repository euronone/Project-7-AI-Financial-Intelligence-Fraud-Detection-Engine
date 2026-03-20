import { Badge } from "@/components/ui/badge";

type RiskLevel = "low" | "medium" | "high" | "critical";

const riskConfig: Record<RiskLevel, { variant: "success" | "warning" | "danger" | "danger"; label: string }> = {
  low: { variant: "success", label: "Low" },
  medium: { variant: "warning", label: "Medium" },
  high: { variant: "danger", label: "High" },
  critical: { variant: "danger", label: "Critical" },
};

interface RiskBadgeProps {
  level: string;
  score?: number;
  className?: string;
}

export function RiskBadge({ level, score, className }: RiskBadgeProps) {
  const config = riskConfig[(level as RiskLevel)] || riskConfig.low;

  return (
    <Badge variant={config.variant} dot className={className}>
      {config.label}
      {score !== undefined && ` (${(score * 100).toFixed(0)}%)`}
    </Badge>
  );
}
