"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useEntity, useEntityTransactions } from "@/hooks/use-entities";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTable } from "@/components/ui/data-table";
import { Pagination } from "@/components/ui/pagination";
import { formatCurrency } from "@/lib/utils";
import type { Transaction } from "@/types/transaction";
import type { ColumnDef } from "@tanstack/react-table";

const txnColumns: ColumnDef<Transaction, any>[] = [
  {
    accessorKey: "external_id",
    header: "ID",
    cell: ({ row }) => <span className="font-mono text-xs">{row.original.external_id}</span>,
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: ({ row }) => <span className="font-semibold">{formatCurrency(row.original.amount, row.original.currency)}</span>,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusIndicator status={row.original.status} />,
  },
  {
    accessorKey: "risk_level",
    header: "Risk",
    cell: ({ row }) => row.original.risk_level ? <RiskBadge level={row.original.risk_level} /> : <span className="text-gray-400">—</span>,
  },
  {
    accessorKey: "processed_at",
    header: "Date",
    cell: ({ row }) => <span className="text-xs text-gray-500">{new Date(row.original.processed_at).toLocaleDateString()}</span>,
  },
];

export default function EntityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { data: entity, isLoading } = useEntity(params.id as string);
  const [txnPage, setTxnPage] = useState(1);
  const { data: txns, isLoading: txnsLoading } = useEntityTransactions(params.id as string, txnPage);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </div>
    );
  }

  if (!entity) return null;

  return (
    <div className="space-y-6">
      <Breadcrumbs />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{entity.name}</h1>
          <p className="mt-1 font-mono text-sm text-gray-500">{entity.external_id}</p>
        </div>
        <Button variant="secondary" onClick={() => router.back()}>Back</Button>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-gray-500">Transactions</p>
          <p className="mt-1 text-2xl font-bold">{entity.transaction_count.toLocaleString()}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Total Volume</p>
          <p className="mt-1 text-2xl font-bold">{formatCurrency(entity.total_transaction_amount)}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Alerts</p>
          <p className="mt-1 text-2xl font-bold">{entity.alert_count}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Risk Score</p>
          <div className="mt-1 flex items-center gap-2">
            <p className="text-2xl font-bold">{(entity.risk_score * 100).toFixed(1)}%</p>
            <RiskBadge level={entity.risk_level} />
          </div>
        </Card>
      </div>

      {/* Info grid */}
      <Card>
        <CardHeader><CardTitle>Entity Information</CardTitle></CardHeader>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { label: "Type", value: <Badge variant="outline">{entity.entity_type}</Badge> },
            { label: "Email", value: entity.email || "—" },
            { label: "Phone", value: entity.phone || "—" },
            { label: "Country", value: entity.country_code || "—" },
            { label: "KYC Status", value: <StatusIndicator status={entity.kyc_status === "verified" ? "active" : entity.kyc_status} /> },
            { label: "Watchlisted", value: entity.is_watchlisted ? <Badge variant="danger" dot>Yes</Badge> : "No" },
          ].map((d) => (
            <div key={d.label}>
              <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{d.label}</p>
              <div className="mt-1 text-sm text-gray-900">{d.value}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent transactions */}
      <Card>
        <CardHeader><CardTitle>Recent Transactions</CardTitle></CardHeader>
        <DataTable
          columns={txnColumns}
          data={txns?.items ?? []}
          loading={txnsLoading}
          emptyMessage="No transactions for this entity"
          onRowClick={(row) => router.push(`/transactions/${row.id}`)}
        />
        {txns && txns.total_pages > 1 && (
          <div className="mt-4 flex justify-center">
            <Pagination page={txnPage} totalPages={txns.total_pages} onPageChange={setTxnPage} />
          </div>
        )}
      </Card>
    </div>
  );
}
