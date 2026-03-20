"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Pagination } from "@/components/ui/pagination";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

interface AuditLogListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: AuditLog[];
}

const resourceTypeOptions = [
  { value: "", label: "All Resources" },
  { value: "user", label: "User" },
  { value: "transaction", label: "Transaction" },
  { value: "entity", label: "Entity" },
  { value: "rule", label: "Rule" },
  { value: "alert", label: "Alert" },
  { value: "case", label: "Case" },
  { value: "model", label: "Model" },
];

const actionColors: Record<string, string> = {
  create: "bg-green-100 text-green-800",
  update: "bg-blue-100 text-blue-800",
  delete: "bg-red-100 text-red-800",
  login: "bg-purple-100 text-purple-800",
  view: "bg-gray-100 text-gray-600",
};

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const [resourceType, setResourceType] = useState("");

  const { data, isLoading } = useQuery<AuditLogListResponse>({
    queryKey: ["audit-logs", page, resourceType],
    queryFn: () => api.get<AuditLogListResponse>("/audit/logs", {
      params: { page, page_size: 25, resource_type: resourceType || undefined },
    }),
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <p className="mt-1 text-sm text-gray-500">{data?.total ?? "—"} entries</p>
      </div>

      <div className="flex items-center gap-3">
        <Select options={resourceTypeOptions} value={resourceType} onChange={(e) => { setResourceType(e.target.value); setPage(1); }} className="w-44" />
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}</div>
      ) : (
        <Card>
          <div className="divide-y">
            {data?.items.map((log) => (
              <div key={log.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${actionColors[log.action] || "bg-gray-100 text-gray-600"}`}>
                    {log.action}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {log.resource_type}
                      {log.resource_id && <span className="ml-1 font-mono text-xs text-gray-400">{log.resource_id.slice(0, 8)}</span>}
                    </p>
                    {log.details && (
                      <p className="text-xs text-gray-500 line-clamp-1">
                        {JSON.stringify(log.details).slice(0, 80)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">{new Date(log.created_at).toLocaleString()}</p>
                  {log.ip_address && <p className="font-mono text-xs text-gray-300">{log.ip_address}</p>}
                </div>
              </div>
            ))}
            {data?.items.length === 0 && (
              <p className="py-8 text-center text-sm text-gray-500">No audit log entries found.</p>
            )}
          </div>
        </Card>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex justify-center"><Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} /></div>
      )}
    </div>
  );
}
