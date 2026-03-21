"use client";

import { useRiskDistribution, useTopRiskEntities } from "@/hooks/use-risk-scores";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskDistributionChart } from "@/components/charts/risk-distribution-chart";
import { RiskBadge } from "@/components/shared/risk-badge";

const levelColors: Record<string, string> = {
  low: "text-success-600",
  medium_low: "text-success-500",
  medium: "text-warning-600",
  high: "text-danger-500",
  critical: "text-danger-700",
};

export default function RiskScoringPage() {
  const router = useRouter();
  const { data: distribution, isLoading: distLoading } = useRiskDistribution();
  const { data: topRisk, isLoading: topLoading } = useTopRiskEntities(10);

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Risk Scoring Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Overview of risk distribution and highest-risk entities</p>
      </div>

      {/* Distribution */}
      <Card>
        <CardHeader><CardTitle>Risk Distribution</CardTitle></CardHeader>
        {distLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : distribution ? (
          <div>
            <p className="mb-4 text-sm text-gray-500">{distribution.total} entities scored</p>
            <RiskDistributionChart data={distribution} />
          </div>
        ) : (
          <p className="text-sm text-gray-500">No risk scores computed yet. Score a transaction to begin.</p>
        )}
      </Card>

      {/* Top Risk Entities */}
      <Card>
        <CardHeader><CardTitle>Highest Risk Entities</CardTitle></CardHeader>
        {topLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : topRisk && topRisk.length > 0 ? (
          <div className="divide-y">
            {topRisk.map((entity, i) => (
              <div
                key={entity.entity_id}
                className="flex cursor-pointer items-center justify-between py-3 transition-colors hover:bg-gray-50"
                onClick={() => router.push(`/risk-scoring/profiles/${entity.entity_id}`)}
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-100 text-xs font-bold text-gray-500">
                    {i + 1}
                  </span>
                  <div>
                    <p className="font-medium text-gray-900">
                      {entity.entity_name || entity.entity_id.slice(0, 8)}
                    </p>
                    <p className="text-xs text-gray-400">
                      {entity.last_scored ? `Scored ${new Date(entity.last_scored).toLocaleDateString()}` : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xl font-bold ${levelColors[entity.risk_level] || "text-gray-600"}`}>
                    {(entity.risk_score * 100).toFixed(0)}
                  </span>
                  <RiskBadge level={entity.risk_level as "low" | "medium" | "high" | "critical"} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No entities scored yet.</p>
        )}
      </Card>
    </div>
  );
}
