"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { useOverviewStats, useFraudTrends, useRiskDistribution } from "@/hooks/use-analytics";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { StatsCard } from "@/components/dashboard/stats-card";
import { RiskGauge } from "@/components/dashboard/risk-gauge";
import { FraudTrendChart } from "@/components/charts/fraud-trend-chart";

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

function formatCurrency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useOverviewStats();
  const { data: trends, isLoading: trendsLoading } = useFraudTrends("30d");
  const { data: riskDist, isLoading: riskLoading } = useRiskDistribution();

  return (
    <div className="space-y-6">
      <Breadcrumbs />

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back, {user?.first_name}. Here&apos;s your fraud detection overview.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}><Skeleton className="h-20 w-full" /></Card>
          ))
        ) : stats ? (
          <>
            <StatsCard
              title="Total Transactions"
              value={formatNumber(stats.total_transactions)}
              change={12.3}
              trend="up"
              color="primary"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                </svg>
              }
            />
            <StatsCard
              title="Fraud Alerts"
              value={formatNumber(stats.total_alerts)}
              change={3.1}
              trend="up"
              color="danger"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
              }
            />
            <StatsCard
              title="Active Rules"
              value={stats.active_rules.toString()}
              change={0}
              trend="stable"
              color="warning"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
                </svg>
              }
            />
            <StatsCard
              title="Open Cases"
              value={stats.total_cases.toString()}
              change={-2}
              trend="down"
              color="success"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0M12 12.75h.008v.008H12v-.008Z" />
                </svg>
              }
            />
          </>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Fraud Trends Chart */}
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Fraud Trends (30 Days)</h2>
            <Link href="/analytics/trends" className="text-sm text-primary-600 hover:text-primary-700">
              View Details
            </Link>
          </div>
          {trendsLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : trends?.data_points ? (
            <FraudTrendChart data={trends.data_points} height={280} />
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-gray-400">No trend data available</div>
          )}
        </Card>

        {/* Risk Overview */}
        <Card>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Risk Overview</h2>
          {riskLoading || statsLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <div className="space-y-6">
              <div className="flex justify-center">
                <RiskGauge
                  score={Math.round((stats?.avg_risk_score ?? 0) * 100)}
                  label="Avg Risk Score"
                />
              </div>
              {riskDist && (
                <div className="space-y-3">
                  {[
                    { label: "Critical", value: riskDist.critical, color: "bg-red-500" },
                    { label: "High", value: riskDist.high, color: "bg-orange-500" },
                    { label: "Medium", value: riskDist.medium, color: "bg-yellow-500" },
                    { label: "Low", value: riskDist.low, color: "bg-green-500" },
                  ].map((level) => (
                    <div key={level.label} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className={`h-2.5 w-2.5 rounded-full ${level.color}`} />
                        <span className="text-gray-600">{level.label}</span>
                      </div>
                      <span className="font-semibold text-gray-900">{level.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Bottom row: Key Metrics + Quick Actions */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">System Metrics</h2>
            <Badge variant="success" dot>Healthy</Badge>
          </div>
          <div className="space-y-5">
            {statsLoading ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)
            ) : (
              <>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-600">Fraud Rate</span>
                    <span className="font-medium text-gray-900">{((stats?.fraud_rate ?? 0) * 100).toFixed(1)}%</span>
                  </div>
                  <Progress value={(stats?.fraud_rate ?? 0) * 100} color="danger" size="sm" />
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-600">Amount Processed</span>
                    <span className="font-medium text-gray-900">{formatCurrency(stats?.total_amount_processed ?? 0)}</span>
                  </div>
                  <Progress value={65} color="primary" size="sm" />
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-600">Entity Coverage</span>
                    <span className="font-medium text-gray-900">{formatNumber(stats?.total_entities ?? 0)} entities</span>
                  </div>
                  <Progress value={80} color="success" size="sm" />
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-600">Alert Resolution</span>
                    <span className="font-medium text-gray-900">64%</span>
                  </div>
                  <Progress value={64} color="warning" size="sm" />
                </div>
              </>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { label: "View Transactions", href: "/transactions", color: "bg-blue-50 text-blue-700 hover:bg-blue-100" },
              { label: "Fraud Alerts", href: "/fraud-alerts", color: "bg-red-50 text-red-700 hover:bg-red-100" },
              { label: "Analytics", href: "/analytics", color: "bg-purple-50 text-purple-700 hover:bg-purple-100" },
              { label: "Network Graph", href: "/network-graph", color: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100" },
              { label: "Rules Engine", href: "/rules", color: "bg-amber-50 text-amber-700 hover:bg-amber-100" },
              { label: "Settings", href: "/settings", color: "bg-gray-50 text-gray-700 hover:bg-gray-100" },
            ].map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${action.color}`}
              >
                {action.label}
                <svg className="ml-auto h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
