"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { FraudTrendPoint } from "@/types/analytics";

interface FraudTrendChartProps {
  data: FraudTrendPoint[];
  height?: number;
}

interface TooltipEntry {
  value: number;
  dataKey: string;
  color: string;
  payload: FraudTrendPoint;
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  const point = payload[0]?.payload;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      <p className="mb-2 text-sm font-medium text-gray-900">{label}</p>
      <div className="space-y-1 text-sm">
        <p className="text-blue-600">
          Count: <span className="font-semibold">{point?.count ?? 0}</span>
        </p>
        <p className="text-orange-500">
          Amount: <span className="font-semibold">${(point?.amount ?? 0).toLocaleString()}</span>
        </p>
        <p className="text-gray-500">
          Avg Score: <span className="font-semibold">{((point?.avg_score ?? 0) * 100).toFixed(1)}%</span>
        </p>
      </div>
    </div>
  );
}

export function FraudTrendChart({ data, height = 350 }: FraudTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          label={{ value: "Count", angle: -90, position: "insideLeft", style: { fontSize: 12, fill: "#6b7280" } }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          label={{ value: "Amount", angle: 90, position: "insideRight", style: { fontSize: 12, fill: "#6b7280" } }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="count"
          name="Fraud Count"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: "#3b82f6", r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="amount"
          name="Fraud Amount"
          stroke="#f97316"
          strokeWidth={2}
          dot={{ fill: "#f97316", r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
