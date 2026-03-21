"use client";

import { memo, useMemo } from "react";
import { cn } from "@/lib/utils";

interface AlertItem {
  id: string;
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  created_at: string;
}

interface AlertFeedProps {
  alerts: AlertItem[];
  maxItems?: number;
}

const SEVERITY_STYLES: Record<AlertItem["severity"], string> = {
  low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export const AlertFeed = memo(function AlertFeed({
  alerts,
  maxItems = 5,
}: AlertFeedProps) {
  const visibleAlerts = useMemo(
    () => alerts.slice(0, maxItems),
    [alerts, maxItems]
  );

  if (visibleAlerts.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Recent Alerts
        </h3>
        <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          No alerts to display
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Recent Alerts
          </h3>
          <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900 dark:text-red-300">
            {alerts.length}
          </span>
        </div>
      </div>

      <ul className="divide-y divide-gray-100 dark:divide-gray-800">
        {visibleAlerts.map((alert) => (
          <li
            key={alert.id}
            className="flex items-start gap-3 px-6 py-3.5 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
          >
            <span
              className={cn(
                "mt-0.5 inline-flex shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                SEVERITY_STYLES[alert.severity]
              )}
            >
              {alert.severity}
            </span>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                {alert.title}
              </p>
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                {formatRelativeTime(alert.created_at)}
              </p>
            </div>

            <span
              className={cn(
                "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                alert.status === "open"
                  ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                  : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
              )}
            >
              {alert.status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
});
