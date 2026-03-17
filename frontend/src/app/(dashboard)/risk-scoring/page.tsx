"use client";

/**
 * F5 — Risk Scoring Dashboard
 *
 * Covers:
 *   F5.1  On-demand risk calculation form
 *   F5.2  Risk level badge (Low / Medium / High / Critical)
 *   F5.3  Component score breakdown panel
 *   F5.4  Risk score history (entity selector)
 *   F5.5  Risk distribution chart
 *   F5.6  Top-N highest risk entities leaderboard
 *   F5.7  Auto-update trigger panel
 */

import React, { useState } from "react";
import { RefreshCw, AlertTriangle, TrendingUp, Users, Zap } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { RiskDistributionChart } from "@/components/charts/risk-distribution-chart";
import {
  useRiskDistribution,
  useTopRiskEntities,
  useCalculateRisk,
  useEntityRiskProfile,
  useRiskHistory,
  useAutoUpdateRisk,
} from "@/hooks/use-risk-scoring";
import {
  RISK_LEVEL_CONFIG,
  RISK_CHART_COLORS,
  type RiskLevel,
  type UpdateTrigger,
} from "@/types/risk-scoring";

// ── Small helpers ─────────────────────────────────────────────────────────────

function RiskBadge({ level }: { level: RiskLevel }) {
  const cfg = RISK_LEVEL_CONFIG[level];
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.color} border ${cfg.border}`}
    >
      {cfg.label}
    </span>
  );
}

function ScoreBar({ score, level }: { score: number; level: RiskLevel }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{
            width: `${score * 100}%`,
            backgroundColor: RISK_CHART_COLORS[level],
          }}
        />
      </div>
      <span className="text-sm font-mono font-medium text-gray-700 w-12 text-right">
        {score.toFixed(4)}
      </span>
    </div>
  );
}

// ── Component Score Breakdown (F5.3) ─────────────────────────────────────────

function ComponentBreakdown({
  scores,
  level,
}: {
  scores: Record<string, number>;
  level: RiskLevel;
}) {
  const labels: Record<string, string> = {
    ml_score: "ML Score",
    rule_score: "Rule Score",
    velocity_score: "Velocity Score",
    behavioral_score: "Behavioral Score",
    network_score: "Network Score",
  };

  return (
    <div className="space-y-3">
      {Object.entries(scores).map(([key, value]) => (
        <div key={key}>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>{labels[key] ?? key}</span>
          </div>
          <ScoreBar score={value} level={level} />
        </div>
      ))}
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  icon: Icon,
  sub,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  sub?: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{title}</span>
        <Icon className="w-4 h-4 text-gray-400" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function RiskScoringPage() {
  // F5.5 — distribution
  const { data: distribution, isLoading: distLoading, refetch: refetchDist } =
    useRiskDistribution();

  // F5.6 — top N
  const [topN, setTopN] = useState(8);
  const { data: topRisk, isLoading: topLoading } = useTopRiskEntities(topN);

  // F5.1 — calculate form state
  const [entityId, setEntityId] = useState("");
  const [amount, setAmount] = useState("");
  const [watchlist, setWatchlist] = useState(false);
  const calculateMutation = useCalculateRisk();

  // F5.3 / F5.4 — entity profile lookup
  const [profileEntityId, setProfileEntityId] = useState<string | null>(null);
  const { data: profile, isLoading: profileLoading } =
    useEntityRiskProfile(profileEntityId);
  const { data: history } = useRiskHistory(profileEntityId, 15);

  // F5.7 — auto-update
  const [autoEntityId, setAutoEntityId] = useState("");
  const [trigger, setTrigger] = useState<UpdateTrigger>("new_transaction");
  const autoUpdateMutation = useAutoUpdateRisk();

  // Summary stats derived from distribution
  const criticalCount =
    distribution?.tiers.find((t) => t.risk_level === "critical")?.count ?? 0;
  const highCount =
    distribution?.tiers.find((t) => t.risk_level === "high")?.count ?? 0;
  const topScore = topRisk?.entities[0]?.overall_score ?? 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Risk Scoring</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            F5 — Composite risk scoring across all entities
          </p>
        </div>
        <button
          onClick={() => refetchDist()}
          className="flex items-center gap-2 text-sm bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-3 py-1.5 rounded-md transition-colors shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${distLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Entities"
          value={distribution?.total_entities ?? "—"}
          icon={Users}
          sub="tracked entities"
        />
        <StatCard
          title="Critical Risk"
          value={criticalCount}
          icon={AlertTriangle}
          sub="score > 0.8"
        />
        <StatCard
          title="High Risk"
          value={highCount}
          icon={TrendingUp}
          sub="score 0.6–0.8"
        />
        <StatCard
          title="Top Score"
          value={topScore.toFixed(4)}
          icon={Zap}
          sub="highest entity score"
        />
      </div>

      {/* Row 1: Distribution chart + Calculate form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* F5.5 — Distribution chart */}
        <div className="lg:col-span-2">
          {distLoading ? (
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 h-80 flex items-center justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : distribution ? (
            <RiskDistributionChart data={distribution} />
          ) : (
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 text-center text-gray-400">
              No distribution data
            </div>
          )}
        </div>

        {/* F5.1 — On-demand calculate */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Calculate Risk Score
          </h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">
                Entity ID
              </label>
              <input
                type="text"
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                placeholder="e.g. ent-001"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">
                Transaction Amount
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={watchlist}
                onChange={(e) => setWatchlist(e.target.checked)}
                className="rounded border-gray-300"
              />
              Watchlist match
            </label>
            <button
              disabled={!entityId || calculateMutation.isPending}
              onClick={() =>
                calculateMutation.mutate({
                  entity_id: entityId,
                  transaction_data: {
                    id: crypto.randomUUID(),
                    amount: parseFloat(amount) || 0,
                  },
                  watchlist_match: watchlist,
                })
              }
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors"
            >
              {calculateMutation.isPending ? "Calculating…" : "Calculate"}
            </button>

            {/* Result */}
            {calculateMutation.data && (
              <div className="mt-3 p-3 rounded-md bg-gray-50 border border-gray-200 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    Overall Score
                  </span>
                  <RiskBadge
                    level={calculateMutation.data.risk_level as RiskLevel}
                  />
                </div>
                <ScoreBar
                  score={calculateMutation.data.overall_score}
                  level={calculateMutation.data.risk_level as RiskLevel}
                />
                <p className="text-xs text-gray-500 leading-relaxed">
                  {calculateMutation.data.explanation}
                </p>
                {/* F5.3 component breakdown */}
                <details className="text-xs">
                  <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                    Component breakdown
                  </summary>
                  <div className="mt-2">
                    <ComponentBreakdown
                      scores={calculateMutation.data.component_scores as unknown as Record<string, number>}
                      level={calculateMutation.data.risk_level as RiskLevel}
                    />
                  </div>
                </details>
              </div>
            )}
            {calculateMutation.isError && (
              <p className="text-xs text-red-600 mt-2">
                {calculateMutation.error.message}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Top-N leaderboard + Entity profile / history */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* F5.6 — Top-N leaderboard */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">
              Top Risk Entities
            </h2>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {[5, 8, 10, 20].map((n) => (
                <option key={n} value={n}>
                  Top {n}
                </option>
              ))}
            </select>
          </div>

          {topLoading ? (
            <div className="flex justify-center py-12">
              <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="space-y-2">
              {topRisk?.entities.map((entity) => (
                <button
                  key={entity.entity_id}
                  onClick={() => setProfileEntityId(entity.entity_id)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all text-left"
                >
                  <span className="w-6 h-6 flex-shrink-0 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-600">
                    {entity.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-800 truncate">
                        {entity.entity_id}
                      </span>
                      <RiskBadge level={entity.risk_level as RiskLevel} />
                    </div>
                    <ScoreBar
                      score={entity.overall_score}
                      level={entity.risk_level as RiskLevel}
                    />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* F5.3 / F5.4 — Entity profile + history */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Entity Risk Profile
          </h2>

          {/* Lookup input */}
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="Enter entity ID…"
              onKeyDown={(e) => {
                if (e.key === "Enter")
                  setProfileEntityId(
                    (e.target as HTMLInputElement).value.trim() || null
                  );
              }}
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={(e) => {
                const input = (e.currentTarget.previousSibling as HTMLInputElement);
                setProfileEntityId(input.value.trim() || null);
              }}
              className="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
            >
              Load
            </button>
          </div>

          {profileLoading && (
            <div className="flex justify-center py-12">
              <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            </div>
          )}

          {!profileEntityId && !profileLoading && (
            <p className="text-sm text-gray-400 text-center py-8">
              Select an entity from the leaderboard or enter an ID above.
            </p>
          )}

          {profile && (
            <div className="space-y-4">
              {/* Score + level */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-gray-900">
                    {profile.current_score.toFixed(4)}
                  </p>
                  <p className="text-xs text-gray-500">
                    Updated{" "}
                    {new Date(profile.last_updated).toLocaleDateString()}
                  </p>
                </div>
                <RiskBadge level={profile.risk_level as RiskLevel} />
              </div>

              {/* F5.3 — Component breakdown */}
              <ComponentBreakdown
                scores={profile.component_scores as unknown as Record<string, number>}
                level={profile.risk_level as RiskLevel}
              />

              {/* Risk factors */}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">
                  Risk Factors
                </p>
                <ul className="space-y-1">
                  {profile.risk_factors.map((f, i) => (
                    <li
                      key={i}
                      className="text-xs text-gray-700 flex items-start gap-1"
                    >
                      <span className="text-orange-400 mt-0.5">•</span> {f}
                    </li>
                  ))}
                </ul>
              </div>

              {/* F5.4 — Score trend chart */}
              {history && history.history.length > 1 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">
                    Score Trend
                  </p>
                  <div style={{ height: 120 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={history.history.map((h, i) => ({
                          i: i + 1,
                          score: h.overall_score,
                        }))}
                        margin={{ top: 4, right: 8, left: -24, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="2 2" stroke="#f0f0f0" />
                        <XAxis dataKey="i" tick={{ fontSize: 10 }} />
                        <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
                        <Tooltip
                          formatter={(v: number) => v.toFixed(4)}
                          labelFormatter={(l) => `Entry ${l}`}
                        />
                        <Line
                          type="monotone"
                          dataKey="score"
                          stroke={RISK_CHART_COLORS[profile.risk_level as RiskLevel]}
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}

          {profileEntityId && !profile && !profileLoading && (
            <p className="text-sm text-red-500 text-center py-8">
              No risk profile found for &quot;{profileEntityId}&quot;
            </p>
          )}
        </div>
      </div>

      {/* F5.7 — Auto-update trigger panel */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Auto-Update Risk Score (F5.7)
        </h2>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs font-medium text-gray-600 mb-1 block">
              Entity ID
            </label>
            <input
              type="text"
              value={autoEntityId}
              onChange={(e) => setAutoEntityId(e.target.value)}
              placeholder="e.g. ent-001"
              className="border border-gray-300 rounded-md px-3 py-2 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 mb-1 block">
              Trigger
            </label>
            <select
              value={trigger}
              onChange={(e) => setTrigger(e.target.value as UpdateTrigger)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="new_transaction">New Transaction</option>
              <option value="alert_resolution">Alert Resolution</option>
              <option value="watchlist_match">Watchlist Match</option>
            </select>
          </div>
          <button
            disabled={!autoEntityId || autoUpdateMutation.isPending}
            onClick={() =>
              autoUpdateMutation.mutate({
                entity_id: autoEntityId,
                trigger,
                context: {},
              })
            }
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium rounded-md transition-colors"
          >
            {autoUpdateMutation.isPending ? "Updating…" : "Trigger Update"}
          </button>

          {autoUpdateMutation.data && (
            <div className="flex items-center gap-4 ml-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
              <span className="text-green-700 font-medium">Updated</span>
              <span className="text-gray-600">
                {autoUpdateMutation.data.previous_score.toFixed(4)}
                {" → "}
                <span className="font-semibold text-gray-900">
                  {autoUpdateMutation.data.new_score.toFixed(4)}
                </span>
              </span>
              <RiskBadge level={autoUpdateMutation.data.risk_level as RiskLevel} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
