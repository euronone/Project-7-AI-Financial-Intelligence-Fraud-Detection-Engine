"use client";

/**
 * Transaction list page with full filter support (F1.5) and export (F1.7).
 */
import { useCallback } from "react";

import { TransactionTable } from "@/components/transactions/transaction-table";
import { TransactionFiltersPanel } from "@/components/transactions/transaction-filters";
import { useTransactions, useExportTransactions } from "@/hooks/use-transactions";
import { useFilterStore } from "@/stores/filter-store";

export default function TransactionsPage() {
  const { filters, setFilters, resetFilters } = useFilterStore();
  const { data, isLoading, isFetching } = useTransactions(filters);
  const exportMutation = useExportTransactions();

  const handleExport = useCallback(
    (format: "csv" | "json") => {
      exportMutation.mutate({ filters, format });
    },
    [exportMutation, filters]
  );

  const handlePageChange = (page: number) => setFilters({ page });

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Transactions</h2>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total != null
              ? `${data.total.toLocaleString()} transaction${data.total !== 1 ? "s" : ""}`
              : "Loading…"}
          </p>
        </div>

        {/* Export buttons (F1.7) */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("csv")}
            disabled={exportMutation.isPending}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport("json")}
            disabled={exportMutation.isPending}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            Export JSON
          </button>
        </div>
      </div>

      {/* Filters (F1.5) */}
      <TransactionFiltersPanel
        value={filters}
        onChange={setFilters}
        onReset={resetFilters}
      />

      {/* Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <TransactionTable
          data={data?.items ?? []}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
            <span className="text-sm text-gray-600">
              Page {data.page} of {data.total_pages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(data.page - 1)}
                disabled={data.page <= 1 || isFetching}
                className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-white"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(data.page + 1)}
                disabled={data.page >= data.total_pages || isFetching}
                className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-white"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
