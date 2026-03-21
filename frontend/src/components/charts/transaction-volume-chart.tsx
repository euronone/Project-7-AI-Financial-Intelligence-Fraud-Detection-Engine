"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { TransactionVolumePoint } from "@/types/analytics";

interface TransactionVolumeChartProps {
  data: TransactionVolumePoint[];
  height?: number;
}

const CHANNEL_CONFIG: Record<string, { color: string; label: string }> = {
  online: { color: "#3b82f6", label: "Online" },
  pos: { color: "#10b981", label: "POS" },
  atm: { color: "#f59e0b", label: "ATM" },
  mobile: { color: "#8b5cf6", label: "Mobile" },
  wire: { color: "#ef4444", label: "Wire" },
  ach: { color: "#06b6d4", label: "ACH" },
};

function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: { value: number; dataKey: string; name: string; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      <p className="mb-2 text-sm font-medium text-gray-900">{label}</p>
      <div className="space-y-1 text-sm">
        {payload.map((entry) => (
          <p key={entry.dataKey} style={{ color: entry.color }}>
            {entry.name}: <span className="font-semibold">{entry.value.toLocaleString()}</span>
          </p>
        ))}
      </div>
    </div>
  );
}

export function TransactionVolumeChart({ data, height = 350 }: TransactionVolumeChartProps) {
  const channels = new Set<string>();
  data.forEach((point) => {
    Object.keys(point.by_channel).forEach((ch) => channels.add(ch));
  });

  const chartData = data.map((point) => ({
    date: point.date,
    ...point.by_channel,
  }));

  const sortedChannels = Array.from(channels).sort();

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => v.toLocaleString()}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          iconType="square"
          iconSize={10}
        />
        {sortedChannels.map((channel) => {
          const config = CHANNEL_CONFIG[channel] ?? { color: "#9ca3af", label: channel };
          return (
            <Bar
              key={channel}
              dataKey={channel}
              name={config.label}
              stackId="channels"
              fill={config.color}
              radius={channel === sortedChannels[sortedChannels.length - 1] ? [2, 2, 0, 0] : undefined}
            />
          );
        })}
      </BarChart>
    </ResponsiveContainer>
  );
}
