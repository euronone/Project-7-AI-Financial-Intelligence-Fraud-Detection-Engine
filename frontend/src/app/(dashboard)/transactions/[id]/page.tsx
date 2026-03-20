"use client";

import { useParams, useRouter } from "next/navigation";
import { useTransaction } from "@/hooks/use-transactions";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";

export default function TransactionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { data: txn, isLoading } = useTransaction(params.id as string);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!txn) return null;

  const details = [
    { label: "External ID", value: txn.external_id },
    { label: "Amount", value: formatCurrency(txn.amount, txn.currency) },
    { label: "Currency", value: txn.currency },
    { label: "Type", value: txn.transaction_type },
    { label: "Channel", value: txn.channel },
    { label: "MCC", value: txn.merchant_category_code || "—" },
    { label: "IP Address", value: txn.ip_address || "—" },
    { label: "Country", value: txn.country_code || "—" },
    { label: "Card Present", value: txn.card_present === null ? "—" : txn.card_present ? "Yes" : "No" },
    { label: "Processed At", value: new Date(txn.processed_at).toLocaleString() },
    { label: "Created At", value: new Date(txn.created_at).toLocaleString() },
  ];

  return (
    <div className="space-y-6">
      <Breadcrumbs />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transaction Detail</h1>
          <p className="mt-1 font-mono text-sm text-gray-500">{txn.external_id}</p>
        </div>
        <Button variant="secondary" onClick={() => router.back()}>
          Back
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Status + Risk */}
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Status</span>
              <StatusIndicator status={txn.status} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Risk Level</span>
              {txn.risk_level ? (
                <RiskBadge level={txn.risk_level} score={txn.fraud_score ?? undefined} />
              ) : (
                <span className="text-sm text-gray-400">Not scored</span>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Fraud Score</span>
              <span className="text-lg font-bold">
                {txn.fraud_score !== null ? `${(txn.fraud_score * 100).toFixed(1)}%` : "—"}
              </span>
            </div>
          </div>
        </Card>

        {/* Amount */}
        <Card>
          <CardHeader>
            <CardTitle>Amount</CardTitle>
          </CardHeader>
          <p className="text-3xl font-bold text-gray-900">
            {formatCurrency(txn.amount, txn.currency)}
          </p>
          <div className="mt-3 flex gap-2">
            <Badge variant="outline">{txn.transaction_type}</Badge>
            <Badge variant="outline">{txn.channel}</Badge>
          </div>
        </Card>

        {/* Entities */}
        <Card>
          <CardHeader>
            <CardTitle>Entities</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-medium text-gray-500">Source Entity</p>
              <button
                onClick={() => router.push(`/entities/${txn.source_entity_id}`)}
                className="mt-0.5 font-mono text-sm text-primary-600 hover:underline"
              >
                {txn.source_entity_id}
              </button>
            </div>
            {txn.destination_entity_id && (
              <div>
                <p className="text-xs font-medium text-gray-500">Destination Entity</p>
                <button
                  onClick={() => router.push(`/entities/${txn.destination_entity_id}`)}
                  className="mt-0.5 font-mono text-sm text-primary-600 hover:underline"
                >
                  {txn.destination_entity_id}
                </button>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Detail grid */}
      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {details.map((d) => (
            <div key={d.label}>
              <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{d.label}</p>
              <p className="mt-1 text-sm text-gray-900">{d.value}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
