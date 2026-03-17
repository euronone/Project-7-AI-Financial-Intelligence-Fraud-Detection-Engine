"use client";

import { Badge } from "@/components/ui/badge";
import type { FraudAlert } from "@/types/alert";

const severityVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  low: "success",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

const statusColors: Record<string, string> = {
  open: "bg-red-100 text-red-800",
  investigating: "bg-yellow-100 text-yellow-800",
  escalated: "bg-orange-100 text-orange-800",
  resolved_fraud: "bg-green-100 text-green-800",
  resolved_false_positive: "bg-gray-100 text-gray-800",
  dismissed: "bg-gray-100 text-gray-500",
};

interface AlertCardProps {
  alert: FraudAlert;
  onClick?: () => void;
}

export function AlertCard({ alert, onClick }: AlertCardProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-lg border bg-white p-4 transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{alert.title}</h3>
          <p className="mt-0.5 text-sm text-gray-500 line-clamp-2">{alert.description}</p>
        </div>
        <div className="ml-3 flex flex-col items-end gap-1.5">
          <Badge variant={severityVariant[alert.severity] || "default"} size="sm">
            {alert.severity}
          </Badge>
          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[alert.status] || ""}`}>
            {alert.status.replace(/_/g, " ")}
          </span>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
        <span>{alert.alert_type.replace(/_/g, " ")}</span>
        {alert.confidence_score !== null && (
          <span>Confidence: {(alert.confidence_score * 100).toFixed(0)}%</span>
        )}
        <span>{new Date(alert.created_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
