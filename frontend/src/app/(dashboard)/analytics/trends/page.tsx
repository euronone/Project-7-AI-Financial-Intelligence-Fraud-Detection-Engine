"use client";

import { useState } from "react";
import { cn, formatNumber, formatCurrency, formatPercent } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";
import { FraudTrendChart } from "@/components/charts/fraud-trend-chart";
import { useFraudTrends } from "@/hooks/use-analytics";

type Period = "7d" | "30d" | "90d";

const PERIOD_OPTIONS: { value: Period; label: string }[] = [
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "90d", label: "90 Days" },
];

export default function TrendsPage() {
  const [period, setPeriod] = useState<Period>("30d");
  const { data: trends, isLoading } = useFraudTrends(period);

  const points = trends?.data_points ?? [];
  const totalCount = points.reduce((sum, p) => sum + p.count, 0);
  const totalAmount = points.reduce((sum, p) => sum + p.amount, 0);
  const avgScore = points.length > 0
    ? points.reduce((sum, p) => sum + p.avg_score, 0) / points.length
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fraud Trends</h1>
          <p className="mt-1 text-sm text-gray-500">
            Detailed analysis of fraud patterns and trends over time.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white p-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                period === opt.value
                  ? "bg-primary-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-100",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <p className="text-sm font-medium text-gray-500">Total Fraud Count</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{formatNumber(totalCount)}</p>
            <p className="mt-1 text-xs text-gray-400">in {period} period</p>
          </Card>
          <Card>
            <p className="text-sm font-medium text-gray-500">Total Fraud Amount</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{formatCurrency(totalAmount)}</p>
            <p className="mt-1 text-xs text-gray-400">in {period} period</p>
          </Card>
          <Card>
            <p className="text-sm font-medium text-gray-500">Avg Fraud Score</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{formatPercent(avgScore)}</p>
            <p className="mt-1 text-xs text-gray-400">across all data points</p>
          </Card>
        </div>
      )}

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Fraud Trend Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[400px] w-full" />
          ) : points.length > 0 ? (
            <FraudTrendChart data={points} height={400} />
          ) : (
            <p className="py-20 text-center text-sm text-gray-400">No trend data available for this period</p>
          )}
        </CardContent>
      </Card>

      {/* Data table */}
      <Card>
        <CardHeader>
          <CardTitle>Trend Data Points</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : points.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="py-3 pr-4">Date</th>
                    <th className="px-4 py-3 text-right">Count</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3 text-right">Avg Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {points.map((point) => (
                    <tr key={point.date} className="hover:bg-gray-50">
                      <td className="py-3 pr-4 font-medium text-gray-900">{point.date}</td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {formatNumber(point.count)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {formatCurrency(point.amount)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={cn(
                            "inline-flex rounded-full px-2 py-0.5 text-xs font-semibold",
                            point.avg_score >= 0.8
                              ? "bg-red-100 text-red-700"
                              : point.avg_score >= 0.6
                                ? "bg-orange-100 text-orange-700"
                                : point.avg_score >= 0.3
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-green-100 text-green-700",
                          )}
                        >
                          {formatPercent(point.avg_score)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="py-12 text-center text-sm text-gray-400">No data points for this period</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
