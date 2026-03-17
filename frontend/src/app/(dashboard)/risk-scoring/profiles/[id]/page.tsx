"use client";

import { useParams, useRouter } from "next/navigation";
import { useEntityRiskHistory, useCalculateEntityRisk } from "@/hooks/use-risk-scores";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskBadge } from "@/components/shared/risk-badge";
import { useToast } from "@/components/ui/toast";

export default function EntityRiskProfilePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const entityId = params.id as string;
  const { data: history, isLoading } = useEntityRiskHistory(entityId);
  const calculateMut = useCalculateEntityRisk();

  const latest = history?.items?.[0];

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Entity Risk Profile</h1>
          <p className="mt-1 font-mono text-sm text-gray-500">{entityId}</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() =>
              calculateMut.mutate(entityId, {
                onSuccess: () => toast("Risk recalculated", "success"),
                onError: () => toast("Failed to calculate risk", "error"),
              })
            }
            loading={calculateMut.isPending}
          >
            Recalculate Risk
          </Button>
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
        </div>
      </div>

      {/* Latest Score */}
      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : latest ? (
        <Card>
          <CardHeader><CardTitle>Current Risk Score</CardTitle></CardHeader>
          <div className="grid gap-6 sm:grid-cols-4">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900">
                {(latest.overall_score * 100).toFixed(0)}
              </p>
              <p className="text-sm text-gray-500">Overall Score</p>
            </div>
            <div className="text-center">
              <RiskBadge level={_mapLevel(latest.overall_score)} />
              <p className="mt-1 text-sm text-gray-500">Risk Level</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-900">{latest.model_version}</p>
              <p className="text-sm text-gray-500">Model Version</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-900">
                {new Date(latest.created_at).toLocaleDateString()}
              </p>
              <p className="text-sm text-gray-500">Last Scored</p>
            </div>
          </div>
          {latest.explanation && (
            <div className="mt-4 rounded-lg bg-gray-50 p-3">
              <p className="text-sm text-gray-700">{latest.explanation}</p>
            </div>
          )}
        </Card>
      ) : (
        <Card>
          <p className="text-sm text-gray-500">No risk scores for this entity. Click &quot;Recalculate Risk&quot; to score.</p>
        </Card>
      )}

      {/* Score Component Breakdown */}
      {latest?.component_scores && (
        <Card>
          <CardHeader><CardTitle>Component Scores</CardTitle></CardHeader>
          <div className="space-y-3">
            {Object.entries(latest.component_scores).map(([key, val]) => {
              const pct = Number(val) * 100;
              return (
                <div key={key}>
                  <div className="mb-1 flex justify-between">
                    <span className="text-sm font-medium text-gray-700">{key.replace(/_/g, " ")}</span>
                    <span className="text-sm font-bold text-gray-900">{pct.toFixed(1)}%</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                      className={`h-full rounded-full ${pct >= 60 ? "bg-danger-500" : pct >= 30 ? "bg-warning-400" : "bg-success-400"}`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* History */}
      <Card>
        <CardHeader><CardTitle>Score History ({history?.total ?? 0})</CardTitle></CardHeader>
        {history && history.items.length > 0 ? (
          <div className="divide-y">
            {history.items.map((score) => (
              <div key={score.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Score: {(score.overall_score * 100).toFixed(0)}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(score.created_at).toLocaleString()} &middot; {score.model_version}
                  </p>
                </div>
                <RiskBadge level={_mapLevel(score.overall_score)} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No history available.</p>
        )}
      </Card>

      {/* Pipeline Result (if just calculated) */}
      {calculateMut.data && (
        <Card>
          <CardHeader><CardTitle>Latest Pipeline Result</CardTitle></CardHeader>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="mb-2 text-sm font-medium text-gray-700">Explanation</p>
            <p className="text-sm text-gray-600">{calculateMut.data.explanation.summary}</p>
          </div>
          {calculateMut.data.explanation.top_risk_factors.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-sm font-medium text-gray-700">Top Risk Factors</p>
              <div className="space-y-1">
                {calculateMut.data.explanation.top_risk_factors.map((f, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{f.description}</span>
                    <Badge variant={f.impact > 0.05 ? "danger" : "warning"} size="sm">
                      +{(f.impact * 100).toFixed(1)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function _mapLevel(score: number): "low" | "medium" | "high" | "critical" {
  if (score < 0.3) return "low";
  if (score < 0.6) return "medium";
  if (score < 0.8) return "high";
  return "critical";
}
