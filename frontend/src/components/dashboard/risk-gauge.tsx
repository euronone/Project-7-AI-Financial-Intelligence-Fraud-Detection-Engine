"use client";

import { memo, useMemo } from "react";

interface RiskGaugeProps {
  score: number;
  label: string;
}

function scoreToColor(score: number): string {
  if (score <= 30) return "#22c55e";
  if (score <= 60) return "#eab308";
  if (score <= 80) return "#f97316";
  return "#ef4444";
}

function scoreToLabel(score: number): string {
  if (score <= 30) return "Low";
  if (score <= 60) return "Medium";
  if (score <= 80) return "High";
  return "Critical";
}

export const RiskGauge = memo(function RiskGauge({
  score,
  label,
}: RiskGaugeProps) {
  const clampedScore = Math.max(0, Math.min(100, score));

  const { arcPath, needlePath, color, riskLabel } = useMemo(() => {
    const cx = 100;
    const cy = 90;
    const r = 70;

    const startAngle = Math.PI;
    const endAngle = 0;

    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy - r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy - r * Math.sin(endAngle);

    const arc = `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;

    const needleAngle = Math.PI - (clampedScore / 100) * Math.PI;
    const needleLen = r - 12;
    const nx = cx + needleLen * Math.cos(needleAngle);
    const ny = cy - needleLen * Math.sin(needleAngle);
    const needle = `M ${cx} ${cy} L ${nx} ${ny}`;

    return {
      arcPath: arc,
      needlePath: needle,
      color: scoreToColor(clampedScore),
      riskLabel: scoreToLabel(clampedScore),
    };
  }, [clampedScore]);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
        {label}
      </h3>

      <div className="mt-2 flex items-center justify-center">
        <svg viewBox="0 0 200 110" className="h-36 w-56" aria-hidden="true">
          <defs>
            <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="40%" stopColor="#eab308" />
              <stop offset="70%" stopColor="#f97316" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          <path
            d={arcPath}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={12}
            strokeLinecap="round"
            className="dark:stroke-gray-700"
          />

          <path
            d={arcPath}
            fill="none"
            stroke="url(#gaugeGrad)"
            strokeWidth={12}
            strokeLinecap="round"
            strokeDasharray={`${(clampedScore / 100) * 220} 220`}
          />

          <path
            d={needlePath}
            fill="none"
            stroke={color}
            strokeWidth={2.5}
            strokeLinecap="round"
          />

          <circle cx={100} cy={90} r={4} fill={color} />

          <text
            x={100}
            y={78}
            textAnchor="middle"
            className="fill-gray-900 text-2xl font-bold dark:fill-white"
            style={{ fontSize: "24px", fontWeight: 700 }}
          >
            {clampedScore}
          </text>

          <text
            x={100}
            y={106}
            textAnchor="middle"
            className="fill-gray-500 dark:fill-gray-400"
            style={{ fontSize: "11px", fontWeight: 500 }}
          >
            {riskLabel} Risk
          </text>
        </svg>
      </div>
    </div>
  );
});
