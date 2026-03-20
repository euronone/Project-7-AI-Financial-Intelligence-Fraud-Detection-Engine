"use client";

import { cn } from "@/lib/utils";

interface MetricBar {
  label: string;
  value: number;
  color?: string;
}

interface ModelPerformanceChartProps {
  metrics: Record<string, number>;
  className?: string;
}

const METRIC_LABELS: Record<string, string> = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1_score: "F1 Score",
  auc_roc: "AUC-ROC",
};

const METRIC_COLORS: Record<string, string> = {
  accuracy: "bg-primary-500",
  precision: "bg-success-500",
  recall: "bg-warning-500",
  f1_score: "bg-blue-500",
  auc_roc: "bg-purple-500",
};

export function ModelPerformanceChart({ metrics, className }: ModelPerformanceChartProps) {
  const bars: MetricBar[] = Object.entries(METRIC_LABELS)
    .filter(([key]) => metrics[key] !== undefined)
    .map(([key, label]) => ({
      label,
      value: metrics[key],
      color: METRIC_COLORS[key] || "bg-gray-400",
    }));

  return (
    <div className={cn("space-y-3", className)}>
      {bars.map((bar) => (
        <div key={bar.label}>
          <div className="mb-1 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">{bar.label}</span>
            <span className="text-sm font-bold text-gray-900">{(bar.value * 100).toFixed(1)}%</span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className={cn("h-full rounded-full transition-all duration-500", bar.color)}
              style={{ width: `${Math.min(bar.value * 100, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
