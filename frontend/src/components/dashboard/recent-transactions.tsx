"use client";

import { memo, useMemo } from "react";
import { cn, formatCurrency } from "@/lib/utils";

interface TransactionItem {
  id: string;
  external_id: string;
  amount: number;
  currency: string;
  status: string;
  risk_level: "low" | "medium" | "high" | "critical";
  created_at: string;
}

interface RecentTransactionsProps {
  transactions: TransactionItem[];
  maxItems?: number;
}

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
  pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  flagged: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  blocked: "bg-red-200 text-red-900 dark:bg-red-950 dark:text-red-300",
  reversed: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
};

const RISK_STYLES: Record<TransactionItem["risk_level"], string> = {
  low: "text-emerald-600 dark:text-emerald-400",
  medium: "text-amber-600 dark:text-amber-400",
  high: "text-orange-600 dark:text-orange-400",
  critical: "text-red-600 dark:text-red-400",
};

const RISK_DOT: Record<TransactionItem["risk_level"], string> = {
  low: "bg-emerald-500",
  medium: "bg-amber-500",
  high: "bg-orange-500",
  critical: "bg-red-500",
};

export const RecentTransactions = memo(function RecentTransactions({
  transactions,
  maxItems = 8,
}: RecentTransactionsProps) {
  const visible = useMemo(
    () => transactions.slice(0, maxItems),
    [transactions, maxItems]
  );

  if (visible.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Recent Transactions
        </h3>
        <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          No transactions to display
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Recent Transactions
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-800 dark:text-gray-400">
              <th className="px-6 py-3">ID</th>
              <th className="px-6 py-3 text-right">Amount</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Risk</th>
              <th className="px-6 py-3 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {visible.map((txn) => (
              <tr
                key={txn.id}
                className="transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td className="whitespace-nowrap px-6 py-3 font-mono text-xs text-gray-700 dark:text-gray-300">
                  {txn.external_id.length > 12
                    ? `${txn.external_id.slice(0, 12)}…`
                    : txn.external_id}
                </td>
                <td className="whitespace-nowrap px-6 py-3 text-right font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(txn.amount, txn.currency)}
                </td>
                <td className="whitespace-nowrap px-6 py-3">
                  <span
                    className={cn(
                      "inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                      STATUS_STYLES[txn.status] ?? STATUS_STYLES.pending
                    )}
                  >
                    {txn.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-3">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 text-xs font-medium capitalize",
                      RISK_STYLES[txn.risk_level]
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block h-1.5 w-1.5 rounded-full",
                        RISK_DOT[txn.risk_level]
                      )}
                    />
                    {txn.risk_level}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-3 text-right text-xs text-gray-500 dark:text-gray-400">
                  {new Date(txn.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});
