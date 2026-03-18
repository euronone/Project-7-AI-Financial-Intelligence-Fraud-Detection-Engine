"use client";

/**
 * Transaction filter panel (F1.5).
 *
 * Renders filter controls for: status, risk level, channel, amount range,
 * date range, country code, and a full-text search input.
 */
import { useEffect, useState } from "react";

import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";
import { CHANNEL_LABELS, RISK_LEVEL_LABELS, TRANSACTION_STATUS_LABELS } from "@/lib/constants";
import type { TransactionFilters } from "@/types/transaction";

interface TransactionFiltersProps {
  value: TransactionFilters;
  onChange: (filters: Partial<TransactionFilters>) => void;
  onReset: () => void;
  className?: string;
}

export function TransactionFiltersPanel({
  value,
  onChange,
  onReset,
  className,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(value.query ?? "");
  const debouncedSearch = useDebounce(searchInput, 400);

  useEffect(() => {
    if (debouncedSearch !== (value.query ?? "")) {
      onChange({ query: debouncedSearch || undefined });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  return (
    <div className={cn("bg-white border rounded-lg p-4 space-y-4", className)}>
      {/* Search */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Search
        </label>
        <input
          type="text"
          placeholder="External ID or description…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {/* Status */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            multiple
            value={value.status ?? []}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions).map(
                (o) => o.value as TransactionFilters["status"] extends Array<infer T> ? T : never
              );
              onChange({ status: selected.length ? selected : undefined });
            }}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            size={3}
          >
            {(Object.entries(TRANSACTION_STATUS_LABELS) as [string, string][]).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Risk level */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Risk Level
          </label>
          <select
            multiple
            value={value.risk_level ?? []}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions).map((o) => o.value);
              onChange({ risk_level: selected.length ? (selected as any) : undefined });
            }}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            size={3}
          >
            {(Object.entries(RISK_LEVEL_LABELS) as [string, string][]).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Channel */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Channel
          </label>
          <select
            multiple
            value={value.channel ?? []}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions).map((o) => o.value);
              onChange({ channel: selected.length ? (selected as any) : undefined });
            }}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            size={3}
          >
            {(Object.entries(CHANNEL_LABELS) as [string, string][]).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Amount range */}
        <div className="space-y-2">
          <label className="block text-xs font-medium text-gray-700">
            Amount Range
          </label>
          <input
            type="number"
            placeholder="Min"
            value={value.min_amount ?? ""}
            min={0}
            onChange={(e) =>
              onChange({ min_amount: e.target.value ? Number(e.target.value) : undefined })
            }
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="number"
            placeholder="Max"
            value={value.max_amount ?? ""}
            min={0}
            onChange={(e) =>
              onChange({ max_amount: e.target.value ? Number(e.target.value) : undefined })
            }
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Date range */}
        <div className="space-y-2">
          <label className="block text-xs font-medium text-gray-700">
            Date Range
          </label>
          <input
            type="datetime-local"
            value={value.date_from ?? ""}
            onChange={(e) => onChange({ date_from: e.target.value || undefined })}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="datetime-local"
            value={value.date_to ?? ""}
            onChange={(e) => onChange({ date_to: e.target.value || undefined })}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Country */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Country Code
          </label>
          <input
            type="text"
            placeholder="e.g. US"
            maxLength={2}
            value={value.country_code ?? ""}
            onChange={(e) =>
              onChange({
                country_code: e.target.value.toUpperCase() || undefined,
              })
            }
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end">
        <button
          onClick={onReset}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Reset filters
        </button>
      </div>
    </div>
  );
}
