"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useModels } from "@/hooks/use-models";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { ModelPerformanceChart } from "@/components/charts/model-performance-chart";

const statusVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  active: "success",
  training: "warning",
  validating: "warning",
  retired: "default",
  failed: "danger",
};

const typeOptions = [
  { value: "", label: "All Types" },
  { value: "fraud_classifier", label: "Fraud Classifier" },
  { value: "anomaly_detector", label: "Anomaly Detector" },
  { value: "risk_scorer", label: "Risk Scorer" },
  { value: "behavioral_profiler", label: "Behavioral Profiler" },
];

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "active", label: "Active" },
  { value: "training", label: "Training" },
  { value: "validating", label: "Validating" },
  { value: "retired", label: "Retired" },
];

export default function MLModelsPage() {
  const router = useRouter();
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useModels({
    model_type: typeFilter || undefined,
    status: statusFilter || undefined,
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ML Model Registry</h1>
        <p className="mt-1 text-sm text-gray-500">
          {data?.total ?? "—"} models registered
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Select options={typeOptions} value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="w-44" />
        <Select options={statusOptions} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-40" />
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data?.items.map((model) => (
            <Card
              key={model.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => router.push(`/ml-models/${model.id}`)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{model.name}</h3>
                  <p className="mt-0.5 text-sm text-gray-500">v{model.version} &middot; {model.framework}</p>
                </div>
                <Badge variant={statusVariant[model.status] || "default"} dot>
                  {model.status}
                </Badge>
              </div>

              <div className="mt-4">
                <ModelPerformanceChart metrics={model.metrics} />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
                <span>{model.model_type.replace("_", " ")}</span>
                <span>{new Date(model.created_at).toLocaleDateString()}</span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
