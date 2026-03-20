"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ZAxis,
} from "recharts";

interface AnomalyPoint {
  x: number;
  y: number;
  risk: string;
  label?: string;
}

interface AnomalyScatterPlotProps {
  data: AnomalyPoint[];
  height?: number;
}

const RISK_CONFIG: Record<string, { color: string; label: string }> = {
  low: { color: "#22c55e", label: "Low" },
  medium: { color: "#eab308", label: "Medium" },
  high: { color: "#f97316", label: "High" },
  critical: { color: "#ef4444", label: "Critical" },
};

function CustomTooltip({ active, payload }: {
  active?: boolean;
  payload?: { payload: AnomalyPoint }[];
}) {
  if (!active || !payload?.length) return null;

  const point = payload[0].payload;
  const config = RISK_CONFIG[point.risk] ?? RISK_CONFIG.low;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      {point.label && (
        <p className="mb-1 text-sm font-medium text-gray-900">{point.label}</p>
      )}
      <div className="space-y-1 text-sm">
        <p className="text-gray-600">
          Amount: <span className="font-semibold">${point.x.toLocaleString()}</span>
        </p>
        <p className="text-gray-600">
          Fraud Score: <span className="font-semibold">{(point.y * 100).toFixed(1)}%</span>
        </p>
        <p style={{ color: config.color }}>
          Risk: <span className="font-semibold">{config.label}</span>
        </p>
      </div>
    </div>
  );
}

export function AnomalyScatterPlot({ data, height = 350 }: AnomalyScatterPlotProps) {
  const grouped = Object.entries(RISK_CONFIG).reduce(
    (acc, [risk]) => {
      acc[risk] = data.filter((d) => d.risk === risk);
      return acc;
    },
    {} as Record<string, AnomalyPoint[]>,
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          type="number"
          dataKey="x"
          name="Amount"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          label={{ value: "Transaction Amount", position: "insideBottom", offset: -5, style: { fontSize: 12, fill: "#6b7280" } }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="Fraud Score"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          domain={[0, 1]}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          label={{ value: "Fraud Score", angle: -90, position: "insideLeft", style: { fontSize: 12, fill: "#6b7280" } }}
        />
        <ZAxis range={[40, 80]} />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        {Object.entries(RISK_CONFIG).map(([risk, config]) =>
          (grouped[risk]?.length ?? 0) > 0 ? (
            <Scatter
              key={risk}
              name={config.label}
              data={grouped[risk]}
              fill={config.color}
              opacity={0.7}
            />
          ) : null,
        )}
      </ScatterChart>
    </ResponsiveContainer>
  );
}
