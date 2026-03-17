"use client";

import { memo, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  change: number;
  trend: "up" | "down" | "stable";
  icon: ReactNode;
  color?: string;
}

function TrendIcon({ trend }: { trend: StatsCardProps["trend"] }) {
  if (trend === "up") {
    return (
      <svg
        className="h-4 w-4"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M12 7a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 11-2 0V9.414l-4.293 4.293a1 1 0 01-1.414 0L8 11.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 11.586 14.586 8H13a1 1 0 01-1-1z"
          clipRule="evenodd"
        />
      </svg>
    );
  }

  if (trend === "down") {
    return (
      <svg
        className="h-4 w-4"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M12 13a1 1 0 011 1v.586l4.293-4.293a1 1 0 011.414 1.414l-5 5a1 1 0 01-1.414 0L8 12.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 12.586 14.586 9H13a1 1 0 01-1-1z"
          clipRule="evenodd"
        />
      </svg>
    );
  }

  return (
    <svg
      className="h-4 w-4"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M4 10a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export const StatsCard = memo(function StatsCard({
  title,
  value,
  change,
  trend,
  icon,
  color = "blue",
}: StatsCardProps) {
  const isPositive = change >= 0;

  const colorMap: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
    green: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400",
    red: "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400",
    amber: "bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400",
    cyan: "bg-cyan-50 text-cyan-600 dark:bg-cyan-950 dark:text-cyan-400",
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
          {title}
        </p>
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            colorMap[color] ?? colorMap.blue
          )}
        >
          {icon}
        </div>
      </div>

      <div className="mt-3">
        <p className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
          {value}
        </p>
      </div>

      <div className="mt-2 flex items-center gap-1.5">
        <span
          className={cn(
            "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold",
            trend === "up" &&
              "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
            trend === "down" &&
              "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
            trend === "stable" &&
              "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
          )}
        >
          <TrendIcon trend={trend} />
          {isPositive ? "+" : ""}
          {change.toFixed(1)}%
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          vs last period
        </span>
      </div>
    </div>
  );
});
