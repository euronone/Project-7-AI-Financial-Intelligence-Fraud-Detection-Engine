"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAlert, useUpdateAlertStatus, useEscalateAlert, useCreateCaseFromAlert } from "@/hooks/use-alerts";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";

const severityVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  low: "success", medium: "warning", high: "danger", critical: "danger",
};

const statusOptions = [
  { value: "open", label: "Open" },
  { value: "investigating", label: "Investigating" },
  { value: "escalated", label: "Escalated" },
  { value: "resolved_fraud", label: "Resolved (Fraud)" },
  { value: "resolved_false_positive", label: "Resolved (False Positive)" },
  { value: "dismissed", label: "Dismissed" },
];

export default function AlertDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const alertId = params.id as string;
  const { data: alert, isLoading } = useAlert(alertId);
  const updateStatus = useUpdateAlertStatus();
  const escalate = useEscalateAlert();
  const createCase = useCreateCaseFromAlert();

  const [newStatus, setNewStatus] = useState("");
  const [notes, setNotes] = useState("");

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-6 w-48" /><Skeleton className="h-64 w-full" /></div>;
  if (!alert) return null;

  const handleStatusUpdate = () => {
    if (!newStatus) return;
    updateStatus.mutate(
      { id: alertId, status: newStatus, resolution_notes: notes || undefined },
      {
        onSuccess: () => { toast("Status updated", "success"); setNewStatus(""); setNotes(""); },
        onError: () => toast("Failed to update status", "error"),
      },
    );
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{alert.title}</h1>
          <p className="mt-1 text-sm text-gray-500">{alert.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={severityVariant[alert.severity] || "default"} size="lg">{alert.severity}</Badge>
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
        </div>
      </div>

      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
        </TabsList>

        <TabsContent value="details">
          <Card>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Status", value: alert.status.replace(/_/g, " ") },
                { label: "Type", value: alert.alert_type.replace(/_/g, " ") },
                { label: "Confidence", value: alert.confidence_score ? `${(alert.confidence_score * 100).toFixed(0)}%` : "N/A" },
                { label: "Created", value: new Date(alert.created_at).toLocaleString() },
              ].map((d) => (
                <div key={d.label}>
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{d.label}</p>
                  <p className="mt-1 text-sm font-medium text-gray-900 capitalize">{d.value}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Transaction ID</p>
                <p className="mt-1 font-mono text-sm text-primary-600 cursor-pointer" onClick={() => router.push(`/transactions/${alert.transaction_id}`)}>
                  {alert.transaction_id}
                </p>
              </div>
              {alert.entity_id && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Entity ID</p>
                  <p className="mt-1 font-mono text-sm text-primary-600 cursor-pointer" onClick={() => router.push(`/entities/${alert.entity_id}`)}>
                    {alert.entity_id}
                  </p>
                </div>
              )}
            </div>
            {alert.resolved_at && (
              <div className="mt-4 rounded-lg bg-green-50 p-3">
                <p className="text-sm font-medium text-green-800">Resolved: {new Date(alert.resolved_at).toLocaleString()}</p>
                {alert.resolution_notes && <p className="mt-1 text-sm text-green-700">{alert.resolution_notes}</p>}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="evidence">
          <Card>
            <CardHeader><CardTitle>Evidence</CardTitle></CardHeader>
            {alert.evidence ? (
              <pre className="overflow-auto rounded-lg bg-gray-50 p-4 font-mono text-xs text-gray-800">
                {JSON.stringify(alert.evidence, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-gray-500">No evidence recorded.</p>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="actions">
          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Update Status</CardTitle></CardHeader>
              <div className="flex items-end gap-3">
                <Select label="New Status" options={statusOptions} value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="w-56" />
                <Input label="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} className="flex-1" />
                <Button onClick={handleStatusUpdate} loading={updateStatus.isPending} disabled={!newStatus}>Update</Button>
              </div>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={() => escalate.mutate(alertId, {
                  onSuccess: () => toast("Alert escalated", "success"),
                  onError: () => toast("Escalation failed", "error"),
                })}
                loading={escalate.isPending}
              >
                Escalate
              </Button>
              <Button
                onClick={() => createCase.mutate(alertId, {
                  onSuccess: (c) => { toast("Case created", "success"); router.push(`/case-management/${c.id}`); },
                  onError: () => toast("Failed to create case", "error"),
                })}
                loading={createCase.isPending}
              >
                Create Case
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
