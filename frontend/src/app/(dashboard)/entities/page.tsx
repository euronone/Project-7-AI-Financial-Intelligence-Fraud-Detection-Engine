"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEntities } from "@/hooks/use-entities";
import { DataTable } from "@/components/ui/data-table";
import { Pagination } from "@/components/ui/pagination";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { SearchBar } from "@/components/shared/search-bar";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Select } from "@/components/ui/select";
import type { Entity, EntityFilters } from "@/types/entity";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<Entity, any>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-gray-900">{row.original.name}</p>
        <p className="text-xs text-gray-500">{row.original.external_id}</p>
      </div>
    ),
  },
  {
    accessorKey: "entity_type",
    header: "Type",
    cell: ({ row }) => <Badge variant="outline" size="sm">{row.original.entity_type}</Badge>,
  },
  {
    accessorKey: "country_code",
    header: "Country",
    cell: ({ row }) => <span className="text-sm">{row.original.country_code || "—"}</span>,
  },
  {
    accessorKey: "risk_level",
    header: "Risk",
    cell: ({ row }) => <RiskBadge level={row.original.risk_level} score={row.original.risk_score} />,
  },
  {
    accessorKey: "kyc_status",
    header: "KYC",
    cell: ({ row }) => <StatusIndicator status={row.original.kyc_status === "verified" ? "active" : row.original.kyc_status} />,
  },
  {
    accessorKey: "is_watchlisted",
    header: "Watchlisted",
    cell: ({ row }) =>
      row.original.is_watchlisted ? (
        <Badge variant="danger" size="sm" dot>Yes</Badge>
      ) : (
        <span className="text-xs text-gray-400">No</span>
      ),
  },
];

const typeOptions = [
  { value: "", label: "All Types" },
  { value: "individual", label: "Individual" },
  { value: "business", label: "Business" },
  { value: "merchant", label: "Merchant" },
];

const riskOptions = [
  { value: "", label: "All Risk" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export default function EntitiesPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<EntityFilters>({});

  const { data, isLoading } = useEntities(page, 25, filters);

  const updateFilter = (key: keyof EntityFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Entities</h1>
        <p className="mt-1 text-sm text-gray-500">
          {data?.total.toLocaleString() ?? "—"} registered entities
        </p>
      </div>

      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SearchBar
            placeholder="Search by name or ID..."
            onSearch={(q) => updateFilter("search", q)}
            className="w-64"
          />
          <Select
            options={typeOptions}
            value={filters.entity_type || ""}
            onChange={(e) => updateFilter("entity_type", e.target.value)}
            className="w-40"
          />
          <Select
            options={riskOptions}
            value={filters.risk_level || ""}
            onChange={(e) => updateFilter("risk_level", e.target.value)}
            className="w-40"
          />
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          loading={isLoading}
          emptyMessage="No entities found"
          onRowClick={(row) => router.push(`/entities/${row.id}`)}
        />

        {data && data.total_pages > 1 && (
          <div className="mt-4 flex justify-center">
            <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
          </div>
        )}
      </Card>
    </div>
  );
}
