"use client";

import { useCallback, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { GraphCanvas } from "@/components/network/graph-canvas";
import { GraphControls } from "@/components/network/graph-controls";
import { useNetworkGraph, useEntityConnections } from "@/hooks/use-network";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { NetworkNode, ConnectionDetail } from "@/types/network";

const DEFAULT_MIN_TX = 2;
const DEFAULT_LIMIT = 100;

export default function NetworkGraphPage() {
  const [minTransactions, setMinTransactions] = useState(DEFAULT_MIN_TX);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);

  const { data, isLoading, isError } = useNetworkGraph(minTransactions, limit);
  const { data: connectionData, isLoading: connectionsLoading } =
    useEntityConnections(selectedNode?.id ?? null);

  const handleNodeClick = useCallback((node: NetworkNode) => {
    setSelectedNode((prev) => (prev?.id === node.id ? null : node));
  }, []);

  const handleReset = useCallback(() => {
    setMinTransactions(DEFAULT_MIN_TX);
    setLimit(DEFAULT_LIMIT);
    setSelectedNode(null);
  }, []);

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      {/* Stats bar */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))
        ) : (
          <>
            <StatCard label="Nodes" value={formatNumber(data?.stats.node_count ?? 0)} />
            <StatCard label="Edges" value={formatNumber(data?.stats.edge_count ?? 0)} />
            <StatCard label="Clusters" value={formatNumber(data?.stats.cluster_count ?? 0)} />
            <StatCard
              label="Avg Connections"
              value={(data?.stats.avg_connections ?? 0).toFixed(1)}
            />
          </>
        )}
      </div>

      {/* Main content */}
      <div className="flex min-h-0 flex-1 gap-4">
        {/* Left sidebar */}
        <aside className="hidden w-64 shrink-0 flex-col gap-4 overflow-y-auto lg:flex">
          <GraphControls
            minTransactions={minTransactions}
            onMinTransactionsChange={setMinTransactions}
            limit={limit}
            onLimitChange={setLimit}
            onReset={handleReset}
            stats={data?.stats}
          />
        </aside>

        {/* Canvas */}
        <Card padding={false} className="relative flex-1 overflow-hidden">
          {isLoading && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600" />
                <p className="text-sm text-gray-500">Loading network graph&hellip;</p>
              </div>
            </div>
          )}

          {isError && (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-red-600">
                Failed to load network graph. Please try again.
              </p>
            </div>
          )}

          {!isLoading && !isError && data && (
            <GraphCanvas
              nodes={data.nodes}
              edges={data.edges}
              onNodeClick={handleNodeClick}
            />
          )}
        </Card>

        {/* Right panel — entity connections */}
        {selectedNode && (
          <aside className="w-72 shrink-0 overflow-y-auto">
            <Card className="flex flex-col gap-4">
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold text-gray-900">
                    {selectedNode.label}
                  </h3>
                  <p className="text-xs capitalize text-gray-500">
                    {selectedNode.entity_type}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  aria-label="Close panel"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
                <dt className="text-gray-500">Risk Score</dt>
                <dd className="text-right font-medium">
                  {(selectedNode.risk_score * 100).toFixed(0)}%
                </dd>
                <dt className="text-gray-500">Risk Level</dt>
                <dd className="text-right">
                  <RiskBadge level={selectedNode.risk_level} />
                </dd>
                <dt className="text-gray-500">Alerts</dt>
                <dd className="text-right font-medium">{selectedNode.alert_count}</dd>
                <dt className="text-gray-500">Transactions</dt>
                <dd className="text-right font-medium">{selectedNode.transaction_count}</dd>
                {selectedNode.country_code && (
                  <>
                    <dt className="text-gray-500">Country</dt>
                    <dd className="text-right font-medium">{selectedNode.country_code}</dd>
                  </>
                )}
              </dl>

              <div className="border-t pt-3">
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Connections
                </h4>

                {connectionsLoading && (
                  <div className="space-y-2">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <Skeleton key={i} className="h-14 rounded-lg" />
                    ))}
                  </div>
                )}

                {!connectionsLoading && connectionData?.connections.length === 0 && (
                  <p className="text-xs text-gray-400">No connections found.</p>
                )}

                {!connectionsLoading &&
                  connectionData?.connections.map((c: ConnectionDetail) => (
                    <div
                      key={c.connected_entity_id}
                      className="mb-2 rounded-lg border border-gray-100 p-2.5 last:mb-0"
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate text-xs font-medium text-gray-900">
                          {c.name}
                        </span>
                        <DirectionBadge direction={c.direction} />
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-[11px] text-gray-500">
                        <span>{c.transaction_count} txns</span>
                        <span>{formatCurrency(c.total_amount)}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </Card>
          </aside>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-lg font-semibold text-gray-900">{value}</span>
    </Card>
  );
}

function RiskBadge({ level }: { level: string }) {
  const variantMap: Record<string, "success" | "warning" | "danger" | "default"> = {
    low: "success",
    medium: "warning",
    high: "danger",
    critical: "danger",
  };
  return (
    <Badge variant={variantMap[level] ?? "default"} size="sm">
      {level}
    </Badge>
  );
}

function DirectionBadge({ direction }: { direction: string }) {
  return (
    <Badge variant="outline" size="sm">
      {direction === "both" ? "\u2194" : direction === "inbound" ? "\u2190" : "\u2192"}{" "}
      {direction}
    </Badge>
  );
}
