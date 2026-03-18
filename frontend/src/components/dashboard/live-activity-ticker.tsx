"use client";

/**
 * Live activity ticker — real-time transaction feed strip (F1.3).
 *
 * Connects to Socket.IO /transactions namespace and displays the last N
 * transactions received in real time, newest at the top.
 */
import { useTransactionSocket } from "@/hooks/use-socket";
import { FraudScoreIndicator } from "@/components/transactions/fraud-score-indicator";
import { StatusIndicator } from "@/components/shared/status-indicator";
import { formatCurrency, formatDateTime } from "@/lib/formatters";
import { CHANNEL_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function LiveActivityTicker() {
  const { liveTransactions, isConnected, clearFeed } = useTransactionSocket();

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              isConnected ? "bg-green-500 animate-pulse" : "bg-gray-400"
            )}
          />
          <span className="text-sm font-medium text-gray-700">
            Live Transaction Feed
          </span>
          {isConnected && (
            <span className="text-xs text-green-600">Connected</span>
          )}
        </div>
        {liveTransactions.length > 0 && (
          <button
            onClick={clearFeed}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Clear
          </button>
        )}
      </div>

      {/* Feed */}
      <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
        {liveTransactions.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-gray-400">
            {isConnected
              ? "Waiting for transactions…"
              : "Connecting to live feed…"}
          </div>
        ) : (
          liveTransactions.map((txn) => (
            <div
              key={txn.id}
              className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 truncate">
                    {formatCurrency(txn.amount, txn.currency)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {CHANNEL_LABELS[txn.channel] ?? txn.channel}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  {formatDateTime(txn.processed_at)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <FraudScoreIndicator
                  score={txn.fraud_score}
                  showLabel={false}
                  className="w-16"
                />
                <StatusIndicator status={txn.status} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
