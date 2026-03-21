"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCases, useCaseStatistics, useCreateCase } from "@/hooks/use-cases";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Pagination } from "@/components/ui/pagination";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { Input } from "@/components/ui/input";
import { Modal, ModalHeader, ModalTitle } from "@/components/ui/modal";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "pending_review", label: "Pending Review" },
  { value: "escalated", label: "Escalated" },
  { value: "closed_confirmed_fraud", label: "Closed (Fraud)" },
  { value: "closed_false_positive", label: "Closed (FP)" },
];

const priorityOptions = [
  { value: "", label: "All Priorities" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

const priorityVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  low: "success", medium: "warning", high: "danger", critical: "danger",
};

const statusColors: Record<string, string> = {
  open: "bg-red-100 text-red-800",
  in_progress: "bg-blue-100 text-blue-800",
  pending_review: "bg-yellow-100 text-yellow-800",
  escalated: "bg-orange-100 text-orange-800",
  closed_confirmed_fraud: "bg-green-100 text-green-800",
  closed_false_positive: "bg-gray-100 text-gray-600",
};

export default function CaseManagementPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const { data, isLoading } = useCases(page, 25, {
    status: status || undefined,
    priority: priority || undefined,
  });
  const { data: stats } = useCaseStatistics();
  const createMut = useCreateCase();

  const handleCreate = () => {
    if (!newTitle.trim()) return;
    createMut.mutate(
      { title: newTitle, priority: "medium" },
      {
        onSuccess: (c) => { toast("Case created", "success"); setShowCreate(false); setNewTitle(""); router.push(`/case-management/${c.id}`); },
        onError: () => toast("Failed to create case", "error"),
      },
    );
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Case Management</h1>
          <p className="mt-1 text-sm text-gray-500">{data?.total ?? "—"} cases</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>New Case</Button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {[
            { label: "Open", value: stats.open, color: "text-red-600" },
            { label: "In Progress", value: stats.in_progress, color: "text-blue-600" },
            { label: "Review", value: stats.pending_review, color: "text-yellow-600" },
            { label: "Escalated", value: stats.escalated, color: "text-orange-600" },
            { label: "Fraud", value: stats.closed_confirmed_fraud, color: "text-green-600" },
            { label: "False Pos", value: stats.closed_false_positive, color: "text-gray-500" },
            { label: "Total", value: stats.total, color: "text-gray-900" },
          ].map((s) => (
            <Card key={s.label} className="text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </Card>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <Select options={statusOptions} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="w-44" />
        <Select options={priorityOptions} value={priority} onChange={(e) => { setPriority(e.target.value); setPage(1); }} className="w-40" />
      </div>

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-xl" />)}</div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((c) => (
            <Card key={c.id} className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => router.push(`/case-management/${c.id}`)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-gray-400">{c.case_number}</span>
                    <h3 className="font-semibold text-gray-900">{c.title}</h3>
                  </div>
                  <p className="mt-0.5 text-sm text-gray-500">{c.description || "No description"}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={priorityVariant[c.priority] || "default"} size="sm">{c.priority}</Badge>
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[c.status] || ""}`}>
                    {c.status.replace(/_/g, " ")}
                  </span>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                <span>Created {new Date(c.created_at).toLocaleDateString()}</span>
                {c.alert_ids && <span>{c.alert_ids.length} alert(s)</span>}
              </div>
            </Card>
          ))}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex justify-center"><Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} /></div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)}>
        <ModalHeader><ModalTitle>Create New Case</ModalTitle></ModalHeader>
        <div className="space-y-4">
          <Input label="Case Title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="Enter case title..." />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} loading={createMut.isPending}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
