"use client";

import type { NetworkNode } from "@/types/network";
import { cn } from "@/lib/utils";

interface NodeTooltipProps {
  node: NetworkNode | null;
  position: { x: number; y: number };
  visible: boolean;
}

const RISK_DOT_COLORS: Record<string, string> = {
  low: "bg-emerald-500",
  medium: "bg-amber-500",
  high: "bg-orange-500",
  critical: "bg-red-500",
};

export function NodeTooltip({ node, position, visible }: NodeTooltipProps) {
  if (!visible || !node) return null;

  return (
    <div
      className="pointer-events-none fixed z-50 w-56 rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
      style={{ left: position.x + 14, top: position.y + 14 }}
    >
      <p className="truncate text-sm font-semibold text-gray-900">{node.label}</p>
      <p className="mb-2 text-xs capitalize text-gray-500">{node.entity_type}</p>

      <div className="space-y-1 text-xs text-gray-700">
        <div className="flex items-center justify-between">
          <span>Risk Score</span>
          <span className="flex items-center gap-1.5 font-medium">
            <span
              className={cn(
                "inline-block h-2 w-2 rounded-full",
                RISK_DOT_COLORS[node.risk_level] ?? "bg-gray-400"
              )}
            />
            {(node.risk_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span>Alerts</span>
          <span className="font-medium">{node.alert_count}</span>
        </div>
        <div className="flex justify-between">
          <span>Transactions</span>
          <span className="font-medium">{node.transaction_count}</span>
        </div>
        {node.country_code && (
          <div className="flex justify-between">
            <span>Country</span>
            <span className="font-medium">{node.country_code}</span>
          </div>
        )}
      </div>
    </div>
  );
}
