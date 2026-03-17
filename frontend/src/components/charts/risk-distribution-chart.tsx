"use client";

// F5.5 — Risk Distribution Chart
// Shows entity count per risk tier (Low / Medium / High / Critical).

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { RiskDistribution, RiskLevel } from "@/types/risk-scoring";
import { RISK_CHART_COLORS, RISK_LEVEL_CONFIG } from "@/types/risk-scoring";

interface Props {
  data: RiskDistribution;
}

interface ChartEntry {
  name: string;
  count: number;
  percentage: number;
  level: RiskLevel;
  fill: string;
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartEntry }>;
}) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800">{d.name} Risk</p>
      <p className="text-gray-600">
        Entities: <span className="font-medium text-gray-900">{d.count}</span>
      </p>
      <p className="text-gray-600">
        Share:{" "}
        <span className="font-medium text-gray-900">{d.percentage}%</span>
      </p>
    </div>
  );
};

export function RiskDistributionChart({ data }: Props) {
  const chartData: ChartEntry[] = data.tiers.map((tier) => ({
    name: RISK_LEVEL_CONFIG[tier.risk_level].label,
    count: tier.count,
    percentage: tier.percentage,
    level: tier.risk_level,
    fill: RISK_CHART_COLORS[tier.risk_level],
  }));

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">
            Risk Distribution
          </h2>
          <p className="text-sm text-gray-500">
            {data.total_entities} entities tracked
          </p>
        </div>
        {/* Legend */}
        <div className="flex gap-3">
          {data.tiers.map((tier) => (
            <div key={tier.risk_level} className="flex items-center gap-1">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: RISK_CHART_COLORS[tier.risk_level] }}
              />
              <span className="text-xs text-gray-600">
                {RISK_LEVEL_CONFIG[tier.risk_level].label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 0, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={80}>
              {chartData.map((entry) => (
                <Cell key={entry.level} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tier summary cards */}
      <div className="grid grid-cols-4 gap-3 mt-4">
        {data.tiers.map((tier) => {
          const cfg = RISK_LEVEL_CONFIG[tier.risk_level];
          return (
            <div
              key={tier.risk_level}
              className={`rounded-lg p-3 border ${cfg.bg} ${cfg.border}`}
            >
              <p className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</p>
              <p className={`text-2xl font-bold ${cfg.color}`}>{tier.count}</p>
              <p className={`text-xs ${cfg.color} opacity-75`}>
                {tier.percentage}%
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
