"use client";

import { useState } from "react";
import { cn, formatNumber, formatCurrency, formatPercent } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { FraudTrendChart } from "@/components/charts/fraud-trend-chart";
import { TransactionVolumeChart } from "@/components/charts/transaction-volume-chart";
import { GeoHeatmap } from "@/components/charts/geo-heatmap";
import {
  useOverviewStats,
  useFraudTrends,
  useTransactionVolume,
  useRiskDistribution,
  useTopPatterns,
  useGeoData,
} from "@/hooks/use-analytics";
import type { RiskDistributionResponse, TopPattern } from "@/types/analytics";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  Legend,
} from "recharts";

type Period = "7d" | "30d" | "90d";

const PERIOD_OPTIONS: { value: Period; label: string }[] = [
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "90d", label: "90 Days" },
];

const RISK_COLORS: Record<string, string> = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};

function StatsCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", color)}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

function RiskDonutChart({ data }: { data: RiskDistributionResponse }) {
  const chartData = [
    { name: "Low", value: data.low, color: RISK_COLORS.low },
    { name: "Medium", value: data.medium, color: RISK_COLORS.medium },
    { name: "High", value: data.high, color: RISK_COLORS.high },
    { name: "Critical", value: data.critical, color: RISK_COLORS.critical },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <RechartsTooltip
          formatter={(value: number, name: string) => [value.toLocaleString(), name]}
          contentStyle={{
            borderRadius: "0.5rem",
            border: "1px solid #e5e7eb",
            fontSize: "0.875rem",
          }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

function TopPatternsList({ patterns }: { patterns: TopPattern[] }) {
  const trendIcon = (trend: string) => {
    if (trend === "up") return <span className="text-red-500">&#9650;</span>;
    if (trend === "down") return <span className="text-green-500">&#9660;</span>;
    return <span className="text-gray-400">&#8212;</span>;
  };

  return (
    <div className="divide-y divide-gray-100">
      {patterns.map((pattern) => (
        <div key={pattern.pattern_name} className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            {trendIcon(pattern.trend)}
            <div>
              <p className="text-sm font-medium text-gray-900">{pattern.pattern_name}</p>
              <p className="text-xs text-gray-500">{pattern.count} occurrences</p>
            </div>
          </div>
          <Badge variant={pattern.percentage > 20 ? "danger" : pattern.percentage > 10 ? "warning" : "default"}>
            {pattern.percentage.toFixed(1)}%
          </Badge>
        </div>
      ))}
      {patterns.length === 0 && (
        <p className="py-8 text-center text-sm text-gray-400">No patterns detected</p>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("30d");

  const { data: stats, isLoading: statsLoading } = useOverviewStats();
  const { data: trends, isLoading: trendsLoading } = useFraudTrends(period);
  const { data: volume, isLoading: volumeLoading } = useTransactionVolume(period);
  const { data: riskDist, isLoading: riskLoading } = useRiskDistribution();
  const { data: topPatterns, isLoading: patternsLoading } = useTopPatterns();
  const { data: geoData, isLoading: geoLoading } = useGeoData();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor fraud trends, transaction volumes, and risk patterns.
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

      {/* Stats row */}
      {statsLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : stats ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            label="Total Transactions"
            value={formatNumber(stats.total_transactions)}
            color="bg-blue-100 text-blue-600"
            icon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
            }
          />
          <StatsCard
            label="Fraud Alerts"
            value={formatNumber(stats.total_alerts)}
            color="bg-red-100 text-red-600"
            icon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            }
          />
          <StatsCard
            label="Fraud Rate"
            value={formatPercent(stats.fraud_rate)}
            color="bg-orange-100 text-orange-600"
            icon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            }
          />
          <StatsCard
            label="Avg Risk Score"
            value={formatPercent(stats.avg_risk_score)}
            color="bg-purple-100 text-purple-600"
            icon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            }
          />
        </div>
      ) : null}

      {/* Fraud trends + risk distribution */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Fraud Trends</CardTitle>
          </CardHeader>
          <CardContent>
            {trendsLoading ? (
              <Skeleton className="h-[350px] w-full" />
            ) : trends?.data_points ? (
              <FraudTrendChart data={trends.data_points} />
            ) : (
              <p className="py-20 text-center text-sm text-gray-400">No trend data available</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <Skeleton className="mx-auto h-[250px] w-full" />
            ) : riskDist ? (
              <>
                <RiskDonutChart data={riskDist} />
                <p className="mt-2 text-center text-xs text-gray-500">
                  {formatNumber(riskDist.total)} total entities
                </p>
              </>
            ) : (
              <p className="py-20 text-center text-sm text-gray-400">No data</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transaction volume */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction Volume</CardTitle>
        </CardHeader>
        <CardContent>
          {volumeLoading ? (
            <Skeleton className="h-[350px] w-full" />
          ) : volume?.data_points ? (
            <TransactionVolumeChart data={volume.data_points} />
          ) : (
            <p className="py-20 text-center text-sm text-gray-400">No volume data available</p>
          )}
        </CardContent>
      </Card>

      {/* Geo + patterns */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Geographic Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {geoLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : geoData?.data ? (
              <GeoHeatmap data={geoData.data} />
            ) : (
              <p className="py-12 text-center text-sm text-gray-400">No geographic data</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Fraud Patterns</CardTitle>
          </CardHeader>
          <CardContent>
            {patternsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : topPatterns?.patterns ? (
              <TopPatternsList patterns={topPatterns.patterns} />
            ) : (
              <p className="py-12 text-center text-sm text-gray-400">No patterns detected</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
