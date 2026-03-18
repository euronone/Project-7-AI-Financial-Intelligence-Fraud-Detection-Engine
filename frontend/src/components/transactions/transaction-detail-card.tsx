"use client";

/**
 * Full transaction detail card (F1.6).
 *
 * Shows raw fields, fraud score breakdown, entity summaries, and geography.
 */
import { FraudScoreIndicator } from "./fraud-score-indicator";
import { RiskBadge } from "@/components/shared/risk-badge";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { formatCurrency, formatDateTime } from "@/lib/formatters";
import { CHANNEL_LABELS, DECISION_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { TransactionDetail } from "@/types/transaction";

interface TransactionDetailCardProps {
  transaction: TransactionDetail;
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm text-gray-900 font-medium text-right max-w-[60%] break-all">
        {value ?? "—"}
      </span>
    </div>
  );
}

export function TransactionDetailCard({ transaction: txn }: TransactionDetailCardProps) {
  const breakdown = txn.fraud_score_breakdown;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {formatCurrency(txn.amount, txn.currency)}
            </h2>
            <p className="text-sm text-gray-500 font-mono">{txn.external_id}</p>
          </div>
          <div className="flex gap-2">
            <StatusIndicator status={txn.status} />
            <RiskBadge level={txn.risk_level} />
          </div>
        </div>

        {/* Core fields */}
        <div>
          <InfoRow label="Transaction ID" value={txn.id} />
          <InfoRow label="Date / Time" value={formatDateTime(txn.processed_at)} />
          <InfoRow label="Type" value={<span className="capitalize">{txn.transaction_type}</span>} />
          <InfoRow label="Channel" value={CHANNEL_LABELS[txn.channel] ?? txn.channel} />
          <InfoRow label="Currency" value={txn.currency} />
          <InfoRow label="Country" value={txn.country_code} />
          <InfoRow label="Card Present" value={txn.card_present != null ? String(txn.card_present) : null} />
          <InfoRow label="Merchant Category" value={txn.merchant_category_code} />
          <InfoRow label="Description" value={txn.description} />
          {txn.ip_address && <InfoRow label="IP Address" value={txn.ip_address} />}
          {txn.device_fingerprint && (
            <InfoRow label="Device Fingerprint" value={txn.device_fingerprint} />
          )}
          {txn.geolocation_lat && (
            <InfoRow
              label="Geolocation"
              value={`${txn.geolocation_lat}, ${txn.geolocation_lng}`}
            />
          )}
        </div>
      </div>

      {/* Fraud Score Breakdown */}
      {breakdown && (
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Fraud Score Breakdown
          </h3>

          <div className="mb-4 flex items-center gap-3">
            <FraudScoreIndicator
              score={breakdown.composite_score}
              className="flex-1"
            />
            <span
              className={cn(
                "px-2 py-0.5 rounded text-xs font-bold",
                DECISION_COLORS[breakdown.decision]
              )}
            >
              {breakdown.decision}
            </span>
          </div>

          <div className="space-y-2">
            {[
              { label: "ML Score", value: breakdown.ml_score },
              { label: "Anomaly Score", value: breakdown.anomaly_score },
              { label: "Behavioral Score", value: breakdown.behavioral_score },
              { label: "Network Score", value: breakdown.network_score },
              { label: "Rule Score", value: breakdown.rule_score },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-36">{label}</span>
                <FraudScoreIndicator score={value} className="flex-1" />
              </div>
            ))}
          </div>

          {breakdown.triggered_rules.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium text-gray-700 mb-1">
                Triggered Rules
              </p>
              <div className="flex flex-wrap gap-1">
                {breakdown.triggered_rules.map((rule) => (
                  <span
                    key={rule}
                    className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded"
                  >
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Entity context */}
      {(txn.source_entity || txn.destination_entity) && (
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Entity Context
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {txn.source_entity && (
              <div className="border rounded p-3">
                <p className="text-xs text-gray-500 mb-1">Source Entity</p>
                <p className="text-sm font-medium">{txn.source_entity.name}</p>
                <p className="text-xs text-gray-500 capitalize">
                  {txn.source_entity.entity_type}
                </p>
                <div className="mt-2 flex gap-2">
                  <RiskBadge level={txn.source_entity.risk_level} />
                  {txn.source_entity.is_watchlisted && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                      Watchlisted
                    </span>
                  )}
                </div>
              </div>
            )}
            {txn.destination_entity && (
              <div className="border rounded p-3">
                <p className="text-xs text-gray-500 mb-1">Destination Entity</p>
                <p className="text-sm font-medium">{txn.destination_entity.name}</p>
                <p className="text-xs text-gray-500 capitalize">
                  {txn.destination_entity.entity_type}
                </p>
                <div className="mt-2 flex gap-2">
                  <RiskBadge level={txn.destination_entity.risk_level} />
                  {txn.destination_entity.is_watchlisted && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                      Watchlisted
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
