"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAlerts, useAlertStatistics } from "@/hooks/use-alerts";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Pagination } from "@/components/ui/pagination";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCard } from "@/components/fraud/alert-card";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "open", label: "Open" },
  { value: "investigating", label: "Investigating" },
  { value: "escalated", label: "Escalated" },
  { value: "resolved_fraud", label: "Resolved (Fraud)" },
  { value: "resolved_false_positive", label: "Resolved (FP)" },
  { value: "dismissed", label: "Dismissed" },
];

const severityOptions = [
  { value: "", label: "All Severities" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export default function FraudAlertsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");

  const { data, isLoading } = useAlerts(page, 25, {
    status: status || undefined,
    severity: severity || undefined,
  });
  const { data: stats } = useAlertStatistics();

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fraud Alerts</h1>
        <p className="mt-1 text-sm text-gray-500">{data?.total ?? "—"} total alerts</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {[
            { label: "Open", value: stats.open, color: "text-red-600" },
            { label: "Investigating", value: stats.investigating, color: "text-yellow-600" },
            { label: "Escalated", value: stats.escalated, color: "text-orange-600" },
            { label: "Resolved", value: stats.resolved_fraud, color: "text-green-600" },
            { label: "False Positive", value: stats.resolved_false_positive, color: "text-gray-600" },
            { label: "Dismissed", value: stats.dismissed, color: "text-gray-400" },
            { label: "Total", value: stats.total, color: "text-gray-900" },
          ].map((s) => (
            <Card key={s.label} className="text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <Select options={statusOptions} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="w-44" />
        <Select options={severityOptions} value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }} className="w-40" />
      </div>

      {/* Alert List */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}
        </div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onClick={() => router.push(`/fraud-alerts/${alert.id}`)} />
          ))}
          {data?.items.length === 0 && (
            <Card className="text-center py-12">
              <p className="text-gray-500">No alerts match your filters.</p>
            </Card>
          )}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex justify-center">
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
