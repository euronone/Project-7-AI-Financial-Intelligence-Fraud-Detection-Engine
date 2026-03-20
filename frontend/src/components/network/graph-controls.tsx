"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { NetworkGraphStats } from "@/types/network";

interface GraphControlsProps {
  minTransactions: number;
  onMinTransactionsChange: (n: number) => void;
  limit: number;
  onLimitChange: (n: number) => void;
  onReset: () => void;
  stats?: NetworkGraphStats | null;
}

export function GraphControls({
  minTransactions,
  onMinTransactionsChange,
  limit,
  onLimitChange,
  onReset,
  stats,
}: GraphControlsProps) {
  return (
    <Card className="flex flex-col gap-5">
      <h3 className="text-sm font-semibold text-gray-900">Graph Controls</h3>

      <div className="space-y-1.5">
        <label className="flex items-center justify-between text-xs text-gray-600">
          <span>Min Transactions</span>
          <span className="font-medium text-gray-900">{minTransactions}</span>
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={minTransactions}
          onChange={(e) => onMinTransactionsChange(Number(e.target.value))}
          className="w-full accent-primary-600"
        />
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>1</span>
          <span>10</span>
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="flex items-center justify-between text-xs text-gray-600">
          <span>Node Limit</span>
          <span className="font-medium text-gray-900">{limit}</span>
        </label>
        <input
          type="range"
          min={10}
          max={500}
          step={10}
          value={limit}
          onChange={(e) => onLimitChange(Number(e.target.value))}
          className="w-full accent-primary-600"
        />
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>10</span>
          <span>500</span>
        </div>
      </div>

      <Button variant="secondary" size="sm" onClick={onReset} className="w-full">
        Reset Defaults
      </Button>

      {stats && (
        <div className="space-y-2 border-t pt-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Graph Stats
          </h4>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <dt className="text-gray-500">Nodes</dt>
            <dd className="text-right font-medium text-gray-900">{stats.node_count}</dd>
            <dt className="text-gray-500">Edges</dt>
            <dd className="text-right font-medium text-gray-900">{stats.edge_count}</dd>
            <dt className="text-gray-500">Clusters</dt>
            <dd className="text-right font-medium text-gray-900">{stats.cluster_count}</dd>
            <dt className="text-gray-500">Avg Connections</dt>
            <dd className="text-right font-medium text-gray-900">
              {stats.avg_connections.toFixed(1)}
            </dd>
          </dl>
        </div>
      )}

      <div className="space-y-2 border-t pt-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Legend
        </h4>
        <div className="space-y-1.5 text-xs">
          {[
            { label: "Low Risk", color: "bg-emerald-500" },
            { label: "Medium Risk", color: "bg-amber-500" },
            { label: "High Risk", color: "bg-orange-500" },
            { label: "Critical Risk", color: "bg-red-500" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${item.color}`} />
              <span className="text-gray-600">{item.label}</span>
            </div>
          ))}
          <div className="mt-2 flex items-center gap-2">
            <span className="inline-block w-5 border-t-2 border-dashed border-red-400" />
            <span className="text-gray-600">Suspicious Link</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
