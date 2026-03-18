"use client";

/**
 * Transaction data table using TanStack Table v8 (F1.5).
 *
 * Columns: processed_at, external_id, amount, channel, status, fraud_score, risk_level, actions
 * Supports sort and click-through to transaction detail.
 */
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import Link from "next/link";

import { FraudScoreIndicator } from "./fraud-score-indicator";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { EmptyState } from "@/components/shared/empty-state";
import { formatCurrency, formatDateTime } from "@/lib/formatters";
import { CHANNEL_LABELS } from "@/lib/constants";
import type { TransactionResponse } from "@/types/transaction";

const columnHelper = createColumnHelper<TransactionResponse>();

const columns = [
  columnHelper.accessor("processed_at", {
    header: "Date / Time",
    cell: (info) => (
      <span className="text-xs text-gray-600 whitespace-nowrap">
        {formatDateTime(info.getValue())}
      </span>
    ),
  }),
  columnHelper.accessor("external_id", {
    header: "External ID",
    cell: (info) => (
      <span className="font-mono text-xs text-gray-800">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor("amount", {
    header: "Amount",
    cell: (info) => (
      <span className="text-sm font-medium text-gray-900 whitespace-nowrap">
        {formatCurrency(info.getValue(), info.row.original.currency)}
      </span>
    ),
  }),
  columnHelper.accessor("channel", {
    header: "Channel",
    cell: (info) => (
      <span className="text-sm text-gray-600">
        {CHANNEL_LABELS[info.getValue()] ?? info.getValue()}
      </span>
    ),
  }),
  columnHelper.accessor("transaction_type", {
    header: "Type",
    cell: (info) => (
      <span className="text-sm text-gray-600 capitalize">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => <StatusIndicator status={info.getValue()} />,
  }),
  columnHelper.accessor("fraud_score", {
    header: "Fraud Score",
    cell: (info) => (
      <FraudScoreIndicator
        score={info.getValue()}
        riskLevel={info.row.original.risk_level}
      />
    ),
  }),
  columnHelper.accessor("risk_level", {
    header: "Risk",
    cell: (info) => <RiskBadge level={info.getValue()} />,
  }),
  columnHelper.display({
    id: "actions",
    header: "",
    cell: (info) => (
      <Link
        href={`/transactions/${info.row.original.id}`}
        className="text-blue-600 hover:text-blue-800 text-xs font-medium"
      >
        View
      </Link>
    ),
  }),
];

interface TransactionTableProps {
  data: TransactionResponse[];
  isLoading?: boolean;
}

export function TransactionTable({ data, isLoading }: TransactionTableProps) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading) {
    return (
      <div className="space-y-2 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data.length) {
    return (
      <EmptyState
        title="No transactions found"
        description="Try adjusting your filters or date range."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="hover:bg-gray-50 transition-colors">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
