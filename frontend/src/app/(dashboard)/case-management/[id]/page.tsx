"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useCase, useUpdateCaseStatus } from "@/hooks/use-cases";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AlertTimeline } from "@/components/fraud/alert-timeline";
import { useToast } from "@/components/ui/toast";

const priorityVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  low: "success", medium: "warning", high: "danger", critical: "danger",
};

const statusOptions = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "pending_review", label: "Pending Review" },
  { value: "escalated", label: "Escalated" },
  { value: "closed_confirmed_fraud", label: "Closed (Confirmed Fraud)" },
  { value: "closed_false_positive", label: "Closed (False Positive)" },
];

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const caseId = params.id as string;
  const { data: caseData, isLoading } = useCase(caseId);
  const updateStatus = useUpdateCaseStatus();

  const [newStatus, setNewStatus] = useState("");
  const [notes, setNotes] = useState("");

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-6 w-48" /><Skeleton className="h-64 w-full" /></div>;
  if (!caseData) return null;

  const handleStatusUpdate = () => {
    if (!newStatus) return;
    updateStatus.mutate(
      { id: caseId, status: newStatus, notes: notes || undefined },
      {
        onSuccess: () => { toast("Case status updated", "success"); setNewStatus(""); setNotes(""); },
        onError: () => toast("Failed to update", "error"),
      },
    );
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm text-gray-400">{caseData.case_number}</span>
            <h1 className="text-2xl font-bold text-gray-900">{caseData.title}</h1>
          </div>
          <p className="mt-1 text-sm text-gray-500">{caseData.description || "No description"}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={priorityVariant[caseData.priority] || "default"} size="lg">{caseData.priority}</Badge>
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Status", value: caseData.status.replace(/_/g, " ") },
                { label: "Priority", value: caseData.priority },
                { label: "Linked Alerts", value: caseData.alert_ids?.length ?? 0 },
                { label: "Created", value: new Date(caseData.created_at).toLocaleDateString() },
              ].map((d) => (
                <div key={d.label}>
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{d.label}</p>
                  <p className="mt-1 text-sm font-medium text-gray-900 capitalize">{String(d.value)}</p>
                </div>
              ))}
            </div>
            {caseData.findings && (
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Findings</p>
                <p className="mt-1 text-sm text-gray-700">{caseData.findings}</p>
              </div>
            )}
            {caseData.closed_at && (
              <div className="mt-4 rounded-lg bg-green-50 p-3">
                <p className="text-sm font-medium text-green-800">Closed on {new Date(caseData.closed_at).toLocaleString()}</p>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <Card>
            <CardHeader><CardTitle>Case Timeline</CardTitle></CardHeader>
            <AlertTimeline events={caseData.timeline?.events || []} />
          </Card>
        </TabsContent>

        <TabsContent value="actions">
          <Card>
            <CardHeader><CardTitle>Update Status</CardTitle></CardHeader>
            <div className="flex items-end gap-3">
              <Select label="New Status" options={statusOptions} value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="w-64" />
              <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} className="flex-1" />
              <Button onClick={handleStatusUpdate} loading={updateStatus.isPending} disabled={!newStatus}>Update</Button>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
