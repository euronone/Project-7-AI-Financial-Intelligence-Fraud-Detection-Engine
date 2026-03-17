"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTransactions } from "@/hooks/use-transactions";
import { DataTable } from "@/components/ui/data-table";
import { Pagination } from "@/components/ui/pagination";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { SearchBar } from "@/components/shared/search-bar";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Select } from "@/components/ui/select";
import { formatCurrency } from "@/lib/utils";
import type { Transaction, TransactionFilters } from "@/types/transaction";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<Transaction, any>[] = [
  {
    accessorKey: "external_id",
    header: "ID",
    cell: ({ row }) => (
      <span className="font-mono text-xs text-gray-600">{row.original.external_id}</span>
    ),
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: ({ row }) => (
      <span className="font-semibold">{formatCurrency(row.original.amount, row.original.currency)}</span>
    ),
  },
  {
    accessorKey: "transaction_type",
    header: "Type",
    cell: ({ row }) => <Badge variant="outline" size="sm">{row.original.transaction_type}</Badge>,
  },
  {
    accessorKey: "channel",
    header: "Channel",
    cell: ({ row }) => <span className="capitalize text-gray-600">{row.original.channel}</span>,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusIndicator status={row.original.status} />,
  },
  {
    accessorKey: "risk_level",
    header: "Risk",
    cell: ({ row }) =>
      row.original.risk_level ? (
        <RiskBadge level={row.original.risk_level} score={row.original.fraud_score ?? undefined} />
      ) : (
        <span className="text-gray-400">—</span>
      ),
  },
  {
    accessorKey: "processed_at",
    header: "Date",
    cell: ({ row }) => (
      <span className="text-xs text-gray-500">
        {new Date(row.original.processed_at).toLocaleDateString()}
      </span>
    ),
  },
];

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "completed", label: "Completed" },
  { value: "flagged", label: "Flagged" },
  { value: "blocked", label: "Blocked" },
  { value: "failed", label: "Failed" },
];

const riskOptions = [
  { value: "", label: "All Risk Levels" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export default function TransactionsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<TransactionFilters>({});

  const { data, isLoading } = useTransactions(page, 25, filters);

  const updateFilter = (key: keyof TransactionFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="mt-1 text-sm text-gray-500">
            {data?.total.toLocaleString() ?? "—"} total transactions
          </p>
        </div>
      </div>

      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SearchBar
            placeholder="Search by transaction ID..."
            onSearch={(q) => updateFilter("search", q)}
            className="w-64"
          />
          <Select
            options={statusOptions}
            value={filters.status || ""}
            onChange={(e) => updateFilter("status", e.target.value)}
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
          emptyMessage="No transactions found"
          onRowClick={(row) => router.push(`/transactions/${row.id}`)}
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
