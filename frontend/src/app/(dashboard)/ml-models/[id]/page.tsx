"use client";

import { useParams, useRouter } from "next/navigation";
import { useModel, usePromoteModel, useRetireModel } from "@/hooks/use-models";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ModelPerformanceChart } from "@/components/charts/model-performance-chart";
import { useToast } from "@/components/ui/toast";

const statusVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  active: "success",
  training: "warning",
  validating: "warning",
  retired: "default",
  failed: "danger",
};

export default function ModelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const modelId = params.id as string;
  const { data: model, isLoading } = useModel(modelId);
  const promoteMut = usePromoteModel();
  const retireMut = useRetireModel();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (!model) return null;

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{model.name}</h1>
          <p className="mt-1 text-sm text-gray-500">
            v{model.version} &middot; {model.framework} &middot; {model.model_type.replace("_", " ")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={statusVariant[model.status] || "default"} size="lg" dot>
            {model.status}
          </Badge>
          {model.status !== "active" && model.status !== "retired" && (
            <Button
              onClick={() => promoteMut.mutate(model.id, {
                onSuccess: () => toast("Model promoted to active", "success"),
                onError: () => toast("Failed to promote model", "error"),
              })}
              loading={promoteMut.isPending}
            >
              Promote to Active
            </Button>
          )}
          {model.status === "active" && (
            <Button
              variant="secondary"
              onClick={() => retireMut.mutate(model.id, {
                onSuccess: () => toast("Model retired", "success"),
                onError: () => toast("Failed to retire model", "error"),
              })}
              loading={retireMut.isPending}
            >
              Retire
            </Button>
          )}
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
        </div>
      </div>

      <Tabs defaultValue="metrics">
        <TabsList>
          <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
          <TabsTrigger value="params">Parameters</TabsTrigger>
          <TabsTrigger value="info">Training Info</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Metrics</CardTitle></CardHeader>
              <ModelPerformanceChart metrics={model.metrics} />
            </Card>
            <Card>
              <CardHeader><CardTitle>Raw Metrics</CardTitle></CardHeader>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(model.metrics).map(([key, val]) => (
                  <div key={key}>
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                      {key.replace(/_/g, " ")}
                    </p>
                    <p className="text-lg font-bold text-gray-900">
                      {typeof val === "number" && val <= 1 ? `${(val * 100).toFixed(2)}%` : String(val).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="params">
          <Card>
            <CardHeader><CardTitle>Model Parameters</CardTitle></CardHeader>
            {model.parameters ? (
              <pre className="overflow-auto rounded-lg bg-gray-50 p-4 font-mono text-sm text-gray-800">
                {JSON.stringify(model.parameters, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-gray-500">No parameters recorded.</p>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="info">
          <Card>
            <CardHeader><CardTitle>Training Details</CardTitle></CardHeader>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Artifact Path</p>
                <p className="mt-1 font-mono text-sm text-gray-700">{model.artifact_path}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Promoted At</p>
                <p className="mt-1 text-sm text-gray-700">
                  {model.promoted_at ? new Date(model.promoted_at).toLocaleString() : "Not promoted"}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Created</p>
                <p className="mt-1 text-sm text-gray-700">{new Date(model.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Last Updated</p>
                <p className="mt-1 text-sm text-gray-700">{new Date(model.updated_at).toLocaleString()}</p>
              </div>
            </div>
            {model.training_dataset_info && (
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Dataset Info</p>
                <pre className="mt-1 overflow-auto rounded-lg bg-gray-50 p-4 font-mono text-sm text-gray-800">
                  {JSON.stringify(model.training_dataset_info, null, 2)}
                </pre>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
