"use client";

/**
 * Transaction detail page (F1.6).
 *
 * Shows: raw fields, fraud score breakdown, entity context, similar transactions.
 */
import { use } from "react";
import Link from "next/link";

import { TransactionDetailCard } from "@/components/transactions/transaction-detail-card";
import { TransactionTable } from "@/components/transactions/transaction-table";
import { useTransaction, useSimilarTransactions } from "@/hooks/use-transactions";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TransactionDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { data: transaction, isLoading, error } = useTransaction(id);
  const { data: similar, isLoading: similarLoading } = useSimilarTransactions(id);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !transaction) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700 font-medium">Transaction not found.</p>
        <Link
          href="/transactions"
          className="mt-3 inline-block text-sm text-blue-600 hover:underline"
        >
          ← Back to transactions
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/transactions" className="hover:text-blue-600">
          Transactions
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-mono truncate max-w-xs">
          {transaction.external_id}
        </span>
      </div>

      {/* Detail card */}
      <TransactionDetailCard transaction={transaction} />

      {/* Similar transactions (F1.6) */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Similar Transactions
        </h3>
        <div className="bg-white border rounded-lg overflow-hidden">
          <TransactionTable
            data={similar ?? []}
            isLoading={similarLoading}
          />
        </div>
      </div>
    </div>
  );
}
