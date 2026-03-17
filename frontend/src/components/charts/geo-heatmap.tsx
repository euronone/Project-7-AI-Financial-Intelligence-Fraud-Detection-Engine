"use client";

import { cn } from "@/lib/utils";
import type { GeoDataPoint } from "@/types/analytics";

interface GeoHeatmapProps {
  data: GeoDataPoint[];
}

export function GeoHeatmap({ data }: GeoHeatmapProps) {
  const sorted = [...data].sort((a, b) => b.fraud_rate - a.fraud_rate);
  const maxFraudRate = Math.max(...data.map((d) => d.fraud_rate), 1);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="py-3 pr-4">Country</th>
            <th className="px-4 py-3 text-right">Transactions</th>
            <th className="px-4 py-3 text-right">Fraud</th>
            <th className="px-4 py-3">Fraud Rate</th>
            <th className="px-4 py-3 text-right">Total Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.map((row) => {
            const isHighRisk = row.fraud_rate > 0.05;
            const barWidth = (row.fraud_rate / maxFraudRate) * 100;

            return (
              <tr
                key={row.country_code}
                className={cn(
                  "transition-colors hover:bg-gray-50",
                  isHighRisk && "bg-red-50/50 hover:bg-red-50",
                )}
              >
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-gray-700">
                      {row.country_code}
                    </span>
                    {isHighRisk && (
                      <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">
                        HIGH RISK
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  {row.count.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-medium text-red-600">
                  {row.fraud_count.toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-100">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          isHighRisk ? "bg-red-500" : row.fraud_rate > 0.03 ? "bg-orange-400" : "bg-green-400",
                        )}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                    <span
                      className={cn(
                        "text-xs font-semibold",
                        isHighRisk ? "text-red-700" : "text-gray-600",
                      )}
                    >
                      {(row.fraud_rate * 100).toFixed(2)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  ${row.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {data.length === 0 && (
        <div className="py-12 text-center text-sm text-gray-400">
          No geographic data available
        </div>
      )}
    </div>
  );
}
