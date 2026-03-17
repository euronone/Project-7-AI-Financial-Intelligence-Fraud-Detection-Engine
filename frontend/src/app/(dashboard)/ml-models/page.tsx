"use client";

// Phase 3 — #15: ML Model Registry Dashboard (F2.7 / F2.8 / F2.9)

import { useState } from "react";
import {
  useModels,
  usePromoteModel,
  useRetireModel,
  useRetrain,
  useInference,
} from "@/hooks/use-ml-models";
import type {
  RegisteredModel,
  ModelType,
  ModelStatus,
  RetrainResponse,
  InferenceResponse,
} from "@/types/ml-models";
import {
  MODEL_TYPE_LABELS,
  MODEL_STATUS_CONFIG,
  KEY_METRICS,
} from "@/types/ml-models";

// ── Helpers ───────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: ModelStatus }) {
  const cfg = MODEL_STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${cfg.color} ${cfg.bg}`}
    >
      {cfg.label}
    </span>
  );
}

function MetricBar({
  value,
  label,
}: {
  value: number | undefined;
  label: string;
}) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color =
    pct >= 90 ? "bg-green-500" : pct >= 75 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between text-xs mb-0.5">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium">{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-gray-200 rounded-full">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Model Card ────────────────────────────────────────────────────────────────

function ModelCard({
  model,
  onSelect,
  isSelected,
}: {
  model: RegisteredModel;
  onSelect: (m: RegisteredModel) => void;
  isSelected: boolean;
}) {
  const promote = usePromoteModel();
  const retire = useRetireModel();

  return (
    <div
      onClick={() => onSelect(model)}
      className={`bg-white rounded-lg border p-5 cursor-pointer transition-shadow hover:shadow-md ${
        isSelected ? "border-blue-500 ring-1 ring-blue-500" : "border-gray-200"
      }`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 leading-snug">
            {model.name}
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {MODEL_TYPE_LABELS[model.model_type]} · {model.version}
          </p>
        </div>
        <StatusBadge status={model.status} />
      </div>

      <div className="space-y-2 mb-4">
        {KEY_METRICS.slice(0, 3).map(({ key, label }) => (
          <MetricBar key={key} value={model.metrics[key]} label={label} />
        ))}
      </div>

      <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
        {model.status === "validating" && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              promote.mutate(model.id);
            }}
            disabled={promote.isPending}
            className="flex-1 text-xs bg-green-50 hover:bg-green-100 text-green-700 font-medium py-1.5 rounded transition-colors disabled:opacity-50"
          >
            {promote.isPending ? "Promoting…" : "Promote"}
          </button>
        )}
        {(model.status === "active" || model.status === "validating") && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              retire.mutate(model.id);
            }}
            disabled={retire.isPending}
            className="flex-1 text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 font-medium py-1.5 rounded transition-colors disabled:opacity-50"
          >
            {retire.isPending ? "Retiring…" : "Retire"}
          </button>
        )}
        {model.status === "retired" && (
          <span className="text-xs text-gray-400 italic">Retired</span>
        )}
      </div>
    </div>
  );
}

// ── Metrics Table ─────────────────────────────────────────────────────────────

function MetricsTable({ model }: { model: RegisteredModel }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Performance Metrics</h3>
      <div className="grid grid-cols-2 gap-4">
        {KEY_METRICS.map(({ key, label }) => {
          const val = model.metrics[key];
          return (
            <div
              key={key}
              className="bg-gray-50 rounded-lg p-3 flex flex-col gap-1"
            >
              <span className="text-xs text-gray-500">{label}</span>
              <span className="text-xl font-bold text-gray-900">
                {val != null ? `${(val * 100).toFixed(1)}%` : "—"}
              </span>
            </div>
          );
        })}
        {model.metrics.n_train_samples != null && (
          <div className="bg-gray-50 rounded-lg p-3 flex flex-col gap-1 col-span-2">
            <span className="text-xs text-gray-500">Training Samples</span>
            <span className="text-xl font-bold text-gray-900">
              {model.metrics.n_train_samples.toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Retrain Panel ─────────────────────────────────────────────────────────────

function RetrainPanel() {
  const [modelType, setModelType] = useState<ModelType>("fraud_classifier");
  const [nSamples, setNSamples] = useState(10000);
  const [reason, setReason] = useState("");
  const retrain = useRetrain();
  const [result, setResult] = useState<RetrainResponse | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    retrain.mutate(
      { model_type: modelType, n_samples: nSamples, reason },
      {
        onSuccess: (data) => setResult(data),
      }
    );
  };

  const modelTypeOptions: { value: ModelType; label: string }[] = [
    { value: "fraud_classifier", label: MODEL_TYPE_LABELS.fraud_classifier },
    { value: "anomaly_detector", label: MODEL_TYPE_LABELS.anomaly_detector },
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">
        Trigger Retraining (F2.8)
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Model Type</label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value as ModelType)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {modelTypeOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">
            Training Samples
          </label>
          <input
            type="number"
            min={1000}
            max={200000}
            step={1000}
            value={nSamples}
            onChange={(e) => setNSamples(Number(e.target.value))}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">
            Reason (optional)
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Monthly scheduled retraining"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={retrain.isPending}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-md transition-colors disabled:opacity-50"
        >
          {retrain.isPending ? "Training…" : "Start Retraining"}
        </button>
      </form>

      {retrain.isError && (
        <p className="mt-3 text-sm text-red-600">
          Error: {retrain.error?.message}
        </p>
      )}

      {result && (
        <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm font-medium text-green-800">{result.status}</p>
          <p className="text-xs text-green-700 mt-1">{result.message}</p>
          {Object.keys(result.metrics).length > 0 && (
            <div className="mt-2 grid grid-cols-3 gap-2">
              {Object.entries(result.metrics)
                .filter(([, v]) => typeof v === "number")
                .slice(0, 6)
                .map(([k, v]) => (
                  <div key={k} className="text-center">
                    <div className="text-xs text-gray-500">{k}</div>
                    <div className="text-sm font-bold text-gray-800">
                      {typeof v === "number" ? (v * 100).toFixed(1) + "%" : String(v)}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Inference Panel ───────────────────────────────────────────────────────────

function InferencePanel({ selectedModel }: { selectedModel: RegisteredModel | null }) {
  const [featuresRaw, setFeaturesRaw] = useState(
    "[[0.5, 0.3, 0.8, 0.1, 0.6, 0.9, 0.2, 0.4, 0.7, 0.3, 0.5, 0.6, 0.1, 0.8, 0.4, 0.9, 0.2, 0.7, 0.3, 0.5]]"
  );
  const inference = useInference();
  const [result, setResult] = useState<InferenceResponse | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setParseError(null);
    if (!selectedModel) return;

    let features: number[][];
    try {
      features = JSON.parse(featuresRaw);
      if (!Array.isArray(features) || !Array.isArray(features[0])) {
        throw new Error("Must be a 2-D array: [[f1, f2, ...], ...]");
      }
    } catch (err) {
      setParseError(String(err));
      return;
    }

    inference.mutate(
      { modelId: selectedModel.id, features },
      { onSuccess: (data) => setResult(data) }
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-1">
        Run Inference (F2.9)
      </h3>
      {!selectedModel ? (
        <p className="text-sm text-gray-400 mt-2">
          Select a model from the list to run inference.
        </p>
      ) : (
        <>
          <p className="text-xs text-gray-400 mb-4">
            Model: <span className="font-medium text-gray-600">{selectedModel.name}</span> ·{" "}
            {selectedModel.version}
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Features (JSON 2-D array)
              </label>
              <textarea
                rows={4}
                value={featuresRaw}
                onChange={(e) => setFeaturesRaw(e.target.value)}
                className="w-full font-mono text-xs border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {parseError && (
                <p className="text-xs text-red-600 mt-1">{parseError}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={inference.isPending}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium py-2 rounded-md transition-colors disabled:opacity-50"
            >
              {inference.isPending ? "Running…" : "Run Inference"}
            </button>
          </form>

          {inference.isError && (
            <p className="mt-3 text-sm text-red-600">
              Error: {inference.error?.message}
            </p>
          )}

          {result && (
            <div className="mt-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Backend</span>
                <span className="font-medium">{result.backend}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Latency</span>
                <span className="font-medium">{result.latency_ms.toFixed(2)} ms</span>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Probabilities</p>
                <div className="flex flex-wrap gap-1">
                  {result.probabilities.map((p, i) => (
                    <span
                      key={i}
                      className={`text-xs font-mono px-2 py-0.5 rounded ${
                        result.predictions[i]
                          ? "bg-red-100 text-red-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {p.toFixed(4)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Summary Stats ─────────────────────────────────────────────────────────────

function SummaryStats({ models }: { models: RegisteredModel[] }) {
  const counts = models.reduce(
    (acc, m) => {
      acc[m.status] = (acc[m.status] ?? 0) + 1;
      return acc;
    },
    {} as Record<ModelStatus, number>
  );

  const statuses: Array<{ key: ModelStatus; label: string; color: string }> = [
    { key: "active", label: "Active", color: "text-green-700" },
    { key: "validating", label: "Validating", color: "text-blue-700" },
    { key: "training", label: "Training", color: "text-yellow-700" },
    { key: "retired", label: "Retired", color: "text-gray-500" },
    { key: "failed", label: "Failed", color: "text-red-700" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      {statuses.map(({ key, label, color }) => (
        <div
          key={key}
          className="bg-white rounded-lg border border-gray-200 p-4 text-center"
        >
          <p className={`text-2xl font-bold ${color}`}>{counts[key] ?? 0}</p>
          <p className="text-xs text-gray-500 mt-0.5">{label}</p>
        </div>
      ))}
    </div>
  );
}

// ── Filter Bar ────────────────────────────────────────────────────────────────

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "All Statuses" },
  { value: "active", label: "Active" },
  { value: "validating", label: "Validating" },
  { value: "training", label: "Training" },
  { value: "retired", label: "Retired" },
  { value: "failed", label: "Failed" },
];

const TYPE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "All Types" },
  { value: "fraud_classifier", label: MODEL_TYPE_LABELS.fraud_classifier },
  { value: "anomaly_detector", label: MODEL_TYPE_LABELS.anomaly_detector },
  { value: "risk_scorer", label: MODEL_TYPE_LABELS.risk_scorer },
  { value: "behavioral_profiler", label: MODEL_TYPE_LABELS.behavioral_profiler },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default function MLModelsPage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedModel, setSelectedModel] = useState<RegisteredModel | null>(null);
  const [activeTab, setActiveTab] = useState<"metrics" | "retrain" | "inference">(
    "metrics"
  );

  const { data: models, isLoading, isError, error, refetch } = useModels(
    typeFilter || undefined,
    statusFilter || undefined
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ML Model Registry</h1>
          <p className="text-sm text-gray-500 mt-1">
            F2.7 Lifecycle management · F2.8 Retraining · F2.9 ONNX Inference
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Summary stats */}
      {models && <SummaryStats models={models} />}

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        {(typeFilter || statusFilter) && (
          <button
            onClick={() => {
              setTypeFilter("");
              setStatusFilter("");
            }}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model list */}
        <div className="lg:col-span-2">
          {isLoading && (
            <div className="flex justify-center items-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          )}
          {isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              Failed to load models: {(error as Error)?.message}
            </div>
          )}
          {models && models.length === 0 && (
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center text-gray-500">
              No models match the current filters.
            </div>
          )}
          {models && models.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {models.map((m) => (
                <ModelCard
                  key={m.id}
                  model={m}
                  onSelect={setSelectedModel}
                  isSelected={selectedModel?.id === m.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Side panels */}
        <div className="space-y-4">
          {/* Tab switcher */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {(
              [
                { key: "metrics", label: "Metrics" },
                { key: "retrain", label: "Retrain" },
                { key: "inference", label: "Inference" },
              ] as const
            ).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex-1 text-xs font-medium py-2 transition-colors ${
                  activeTab === key
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {activeTab === "metrics" &&
            (selectedModel ? (
              <>
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {selectedModel.name}
                  </h3>
                  <div className="text-xs text-gray-500 space-y-0.5">
                    <p>
                      Type: {MODEL_TYPE_LABELS[selectedModel.model_type]}
                    </p>
                    <p>Version: {selectedModel.version}</p>
                    <p>
                      Created:{" "}
                      {new Date(selectedModel.created_at).toLocaleDateString()}
                    </p>
                    {selectedModel.description && (
                      <p className="mt-1 text-gray-600 italic">
                        {selectedModel.description}
                      </p>
                    )}
                  </div>
                </div>
                <MetricsTable model={selectedModel} />
              </>
            ) : (
              <div className="bg-gray-50 rounded-lg border border-gray-200 p-6 text-center text-sm text-gray-400">
                Click a model card to view its metrics.
              </div>
            ))}

          {activeTab === "retrain" && <RetrainPanel />}
          {activeTab === "inference" && (
            <InferencePanel selectedModel={selectedModel} />
          )}
        </div>
      </div>
    </div>
  );
}
