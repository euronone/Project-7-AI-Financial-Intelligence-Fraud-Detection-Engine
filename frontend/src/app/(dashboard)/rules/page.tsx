"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRules, useToggleRule, useDeleteRule } from "@/hooks/use-rules";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Pagination } from "@/components/ui/pagination";
import { Select } from "@/components/ui/select";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmationDialog } from "@/components/shared/confirmation-dialog";
import type { Rule } from "@/types/rule";

const severityVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  low: "success",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

const categoryOptions = [
  { value: "", label: "All Categories" },
  { value: "velocity", label: "Velocity" },
  { value: "amount", label: "Amount" },
  { value: "geography", label: "Geography" },
  { value: "pattern", label: "Pattern" },
  { value: "device", label: "Device" },
  { value: "custom", label: "Custom" },
];

export default function RulesPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Rule | null>(null);

  const { data, isLoading } = useRules(page, 25, { category: category || undefined });
  const toggleMut = useToggleRule();
  const deleteMut = useDeleteRule();

  return (
    <div className="space-y-6">
      <Breadcrumbs />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Rules Engine</h1>
          <p className="mt-1 text-sm text-gray-500">
            {data?.total ?? "—"} rules configured
          </p>
        </div>
        <Button onClick={() => router.push("/rules/create")}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Create Rule
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <Select
          options={categoryOptions}
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="w-44"
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((rule) => (
            <Card key={rule.id} className="transition-shadow hover:shadow-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Switch
                    checked={rule.is_active}
                    onChange={(checked) => toggleMut.mutate({ id: rule.id, is_active: checked })}
                  />
                  <div>
                    <button
                      onClick={() => router.push(`/rules/${rule.id}`)}
                      className="text-base font-semibold text-gray-900 hover:text-primary-600"
                    >
                      {rule.name}
                    </button>
                    <p className="mt-0.5 text-sm text-gray-500">
                      {rule.description || "No description"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-500">Hits</p>
                    <p className="text-lg font-bold text-gray-900">{rule.hit_count.toLocaleString()}</p>
                  </div>
                  <Badge variant={severityVariant[rule.severity] || "default"} size="sm">
                    {rule.severity}
                  </Badge>
                  <Badge variant="outline" size="sm">P{rule.priority}</Badge>
                  <Badge variant="outline" size="sm">{rule.category}</Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteTarget(rule)}
                  >
                    <svg className="h-4 w-4 text-gray-400 hover:text-danger-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                    </svg>
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex justify-center">
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </div>
      )}

      <ConfirmationDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) {
            deleteMut.mutate(deleteTarget.id, { onSuccess: () => setDeleteTarget(null) });
          }
        }}
        title="Delete Rule"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMut.isPending}
      />
    </div>
  );
}
