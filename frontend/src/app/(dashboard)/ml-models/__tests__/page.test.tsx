/**
 * Phase 3 — ML Model Registry Dashboard: Frontend tests
 *
 * Framework: Vitest + React Testing Library
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@/hooks/use-ml-models", () => ({
  useModels: vi.fn(),
  useModel: vi.fn(),
  useModelMetrics: vi.fn(),
  useRegisterModel: vi.fn(),
  usePromoteModel: vi.fn(),
  useRetireModel: vi.fn(),
  useUpdateMetrics: vi.fn(),
  useRetrain: vi.fn(),
  useInference: vi.fn(),
  mlModelKeys: {
    all: ["ml-models"],
    list: () => ["ml-models", "list"],
    detail: (id: string) => ["ml-models", "detail", id],
    metrics: (id: string) => ["ml-models", "metrics", id],
  },
}));

import * as hooks from "@/hooks/use-ml-models";
import MLModelsPage from "../page";
import type { RegisteredModel } from "@/types/ml-models";

// ── Test data ─────────────────────────────────────────────────────────────────

const MOCK_MODELS: RegisteredModel[] = [
  {
    id: "reg-xgb-001",
    name: "XGBoost Fraud Classifier",
    model_type: "fraud_classifier",
    version: "v1.2.0",
    status: "active",
    description: "XGBoost + MLP ensemble.",
    metrics: {
      accuracy: 0.9512,
      precision: 0.8734,
      recall: 0.8961,
      f1: 0.8846,
      auc_roc: 0.9721,
      auc_pr: 0.9104,
      n_train_samples: 80000,
    },
    artifact_path: "",
    training_dataset_info: {},
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "reg-iso-001",
    name: "Isolation Forest Anomaly Detector",
    model_type: "anomaly_detector",
    version: "v1.0.1",
    status: "active",
    description: "Isolation Forest ensemble.",
    metrics: {
      accuracy: 0.8923,
      precision: 0.7812,
      recall: 0.8145,
      f1: 0.7975,
      auc_roc: 0.9312,
      auc_pr: 0.8756,
    },
    artifact_path: "",
    training_dataset_info: {},
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  },
  {
    id: "reg-nn-001",
    name: "Neural Net Behavioral Profiler",
    model_type: "behavioral_profiler",
    version: "v2.0.0",
    status: "validating",
    description: "Deep learning model.",
    metrics: {
      accuracy: 0.9201,
      f1: 0.8522,
      auc_roc: 0.9567,
    },
    artifact_path: "",
    training_dataset_info: {},
    created_at: "2026-01-03T00:00:00Z",
    updated_at: "2026-01-03T00:00:00Z",
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeMutationMock(overrides: Record<string, unknown> = {}) {
  return {
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
    data: undefined,
    ...overrides,
  };
}

function makeQueryMock(data: unknown, overrides: Record<string, unknown> = {}) {
  return {
    data,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MLModelsPage />
    </QueryClientProvider>
  );
}

// ── Default mock setup ────────────────────────────────────────────────────────

function setupDefaultMocks() {
  vi.mocked(hooks.useModels).mockReturnValue(
    makeQueryMock(MOCK_MODELS) as ReturnType<typeof hooks.useModels>
  );
  vi.mocked(hooks.usePromoteModel).mockReturnValue(
    makeMutationMock() as unknown as ReturnType<typeof hooks.usePromoteModel>
  );
  vi.mocked(hooks.useRetireModel).mockReturnValue(
    makeMutationMock() as unknown as ReturnType<typeof hooks.useRetireModel>
  );
  vi.mocked(hooks.useRetrain).mockReturnValue(
    makeMutationMock() as unknown as ReturnType<typeof hooks.useRetrain>
  );
  vi.mocked(hooks.useInference).mockReturnValue(
    makeMutationMock() as unknown as ReturnType<typeof hooks.useInference>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  setupDefaultMocks();
});

// ═══════════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe("MLModelsPage", () => {
  // ── Header & title ──────────────────────────────────────────────────────────

  it("renders the page title", () => {
    renderPage();
    expect(screen.getByText("ML Model Registry")).toBeInTheDocument();
  });

  it("renders the feature description subtitle", () => {
    renderPage();
    expect(
      screen.getByText(/F2\.7 Lifecycle management/)
    ).toBeInTheDocument();
  });

  it("renders a Refresh button", () => {
    renderPage();
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });

  // ── Loading state ───────────────────────────────────────────────────────────

  it("shows loading spinner when isLoading", () => {
    vi.mocked(hooks.useModels).mockReturnValue(
      makeQueryMock(undefined, { isLoading: true }) as ReturnType<
        typeof hooks.useModels
      >
    );
    const { container } = renderPage();
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  // ── Error state ─────────────────────────────────────────────────────────────

  it("shows error message when query fails", () => {
    vi.mocked(hooks.useModels).mockReturnValue(
      makeQueryMock(undefined, {
        isError: true,
        error: new Error("Network error"),
      }) as ReturnType<typeof hooks.useModels>
    );
    renderPage();
    expect(screen.getByText(/Network error/)).toBeInTheDocument();
  });

  // ── Empty state ─────────────────────────────────────────────────────────────

  it("shows empty state message when no models match filters", () => {
    vi.mocked(hooks.useModels).mockReturnValue(
      makeQueryMock([]) as ReturnType<typeof hooks.useModels>
    );
    renderPage();
    expect(
      screen.getByText(/No models match the current filters/)
    ).toBeInTheDocument();
  });

  // ── Model cards ─────────────────────────────────────────────────────────────

  it("renders a card for each model", () => {
    renderPage();
    expect(screen.getByText("XGBoost Fraud Classifier")).toBeInTheDocument();
    expect(
      screen.getByText("Isolation Forest Anomaly Detector")
    ).toBeInTheDocument();
    expect(screen.getByText("Neural Net Behavioral Profiler")).toBeInTheDocument();
  });

  it("shows version for each model", () => {
    renderPage();
    expect(screen.getByText(/v1\.2\.0/)).toBeInTheDocument();
    expect(screen.getByText(/v1\.0\.1/)).toBeInTheDocument();
    expect(screen.getByText(/v2\.0\.0/)).toBeInTheDocument();
  });

  it("shows status badge Active for active models", () => {
    renderPage();
    const badges = screen.getAllByText("Active");
    expect(badges.length).toBeGreaterThanOrEqual(2);
  });

  it("shows Validating badge for validating model", () => {
    renderPage();
    // Multiple elements have "Validating" (stat label + option + badge span)
    const badge = screen
      .getAllByText("Validating")
      .find((el) => el.tagName === "SPAN" && el.className.includes("rounded-full"));
    expect(badge).toBeTruthy();
  });

  it("shows model type label in card subtitle", () => {
    renderPage();
    // Multiple elements contain "Fraud Classifier" (card subtitle + dropdown option)
    const subtitles = screen
      .getAllByText(/Fraud Classifier/)
      .filter((el) => el.tagName === "P");
    expect(subtitles.length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/Anomaly Detector/).some((el) => el.tagName === "P")
    ).toBe(true);
  });

  // ── Summary stats ───────────────────────────────────────────────────────────

  it("renders summary stats section with correct active count", () => {
    renderPage();
    // 2 active models in mock data
    const activeCount = screen.getAllByText("2");
    expect(activeCount.length).toBeGreaterThanOrEqual(1);
  });

  it("shows Retired stat with zero count", () => {
    renderPage();
    // Multiple "Retired" (stat label + select option) — find the stat label (small text)
    const statLabel = screen
      .getAllByText("Retired")
      .find((el) => el.tagName === "P" && el.className.includes("text-xs"));
    expect(statLabel).toBeTruthy();
  });

  // ── Filters ─────────────────────────────────────────────────────────────────

  it("renders type filter dropdown", () => {
    renderPage();
    expect(screen.getByText("All Types")).toBeInTheDocument();
  });

  it("renders status filter dropdown", () => {
    renderPage();
    expect(screen.getByText("All Statuses")).toBeInTheDocument();
  });

  it("calls useModels with type filter when type is selected", () => {
    renderPage();
    const typeSelect = screen
      .getAllByRole("combobox")
      .find((s) => s.textContent?.includes("All Types"))!;
    fireEvent.change(typeSelect, {
      target: { value: "fraud_classifier" },
    });
    expect(hooks.useModels).toHaveBeenCalledWith(
      "fraud_classifier",
      undefined
    );
  });

  it("calls useModels with status filter when status is selected", () => {
    renderPage();
    const statusSelect = screen
      .getAllByRole("combobox")
      .find((s) => s.textContent?.includes("All Statuses"))!;
    fireEvent.change(statusSelect, { target: { value: "active" } });
    expect(hooks.useModels).toHaveBeenCalledWith(undefined, "active");
  });

  it("shows Clear filters button when filter is active", () => {
    renderPage();
    const typeSelect = screen
      .getAllByRole("combobox")
      .find((s) => s.textContent?.includes("All Types"))!;
    fireEvent.change(typeSelect, { target: { value: "anomaly_detector" } });
    expect(screen.getByText("Clear filters")).toBeInTheDocument();
  });

  // ── Tab switcher ────────────────────────────────────────────────────────────

  it("renders all three tab buttons", () => {
    renderPage();
    expect(screen.getByText("Metrics")).toBeInTheDocument();
    expect(screen.getByText("Retrain")).toBeInTheDocument();
    expect(screen.getByText("Inference")).toBeInTheDocument();
  });

  it("metrics tab shows hint to click a model card", () => {
    renderPage();
    expect(
      screen.getByText(/Click a model card to view its metrics/)
    ).toBeInTheDocument();
  });

  it("switches to Retrain panel on Retrain tab click", () => {
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    expect(screen.getByText(/Trigger Retraining/)).toBeInTheDocument();
  });

  it("switches to Inference panel on Inference tab click", () => {
    renderPage();
    fireEvent.click(screen.getByText("Inference"));
    expect(screen.getByText(/Run Inference/)).toBeInTheDocument();
  });

  // ── Model selection → metrics view ─────────────────────────────────────────

  it("shows model metrics after clicking a model card", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    expect(screen.getByText("Performance Metrics")).toBeInTheDocument();
  });

  it("shows metric percentages after selecting a model", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    // Accuracy 0.9512 → 95.1%
    expect(screen.getByText("95.1%")).toBeInTheDocument();
  });

  it("shows model version in detail panel after selection", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    expect(screen.getByText(/Version: v1\.2\.0/)).toBeInTheDocument();
  });

  it("shows n_train_samples when available", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    // The Training Samples label appears when n_train_samples is present
    expect(screen.getByText("Training Samples")).toBeInTheDocument();
  });

  // ── Promote / Retire actions ────────────────────────────────────────────────

  it("shows Promote button for validating model", () => {
    renderPage();
    expect(screen.getByText("Promote")).toBeInTheDocument();
  });

  it("calls promoteModel.mutate when Promote is clicked", () => {
    const mutateMock = vi.fn();
    vi.mocked(hooks.usePromoteModel).mockReturnValue(
      makeMutationMock({ mutate: mutateMock }) as unknown as ReturnType<
        typeof hooks.usePromoteModel
      >
    );
    renderPage();
    fireEvent.click(screen.getByText("Promote"));
    expect(mutateMock).toHaveBeenCalledWith("reg-nn-001");
  });

  it("shows Retire button for active model card", () => {
    renderPage();
    const retireButtons = screen.getAllByText("Retire");
    expect(retireButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("calls retireModel.mutate when Retire is clicked", () => {
    const mutateMock = vi.fn();
    vi.mocked(hooks.useRetireModel).mockReturnValue(
      makeMutationMock({ mutate: mutateMock }) as unknown as ReturnType<
        typeof hooks.useRetireModel
      >
    );
    renderPage();
    const retireBtn = screen.getAllByText("Retire")[0];
    fireEvent.click(retireBtn);
    expect(mutateMock).toHaveBeenCalled();
  });

  it("disables Promote button while isPending", () => {
    vi.mocked(hooks.usePromoteModel).mockReturnValue(
      makeMutationMock({ isPending: true }) as unknown as ReturnType<
        typeof hooks.usePromoteModel
      >
    );
    renderPage();
    const btn = screen.getByText("Promoting…");
    expect(btn).toBeDisabled();
  });

  // ── Retrain panel ───────────────────────────────────────────────────────────

  it("retrain panel has model type select", () => {
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    expect(screen.getByText("Model Type")).toBeInTheDocument();
    // Multiple elements have "Fraud Classifier" (model card subtitle + retrain select option)
    expect(screen.getAllByText(/Fraud Classifier/).length).toBeGreaterThanOrEqual(1);
  });

  it("retrain panel has n_samples input defaulting to 10000", () => {
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    const input = screen.getByDisplayValue("10000");
    expect(input).toBeInTheDocument();
  });

  it("calls retrain.mutate on form submit", () => {
    const mutateMock = vi.fn();
    vi.mocked(hooks.useRetrain).mockReturnValue(
      makeMutationMock({ mutate: mutateMock }) as unknown as ReturnType<
        typeof hooks.useRetrain
      >
    );
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    fireEvent.click(screen.getByText("Start Retraining"));
    expect(mutateMock).toHaveBeenCalledWith(
      expect.objectContaining({ model_type: "fraud_classifier", n_samples: 10000 }),
      expect.anything()
    );
  });

  it("shows retrain error message when mutation fails", () => {
    vi.mocked(hooks.useRetrain).mockReturnValue(
      makeMutationMock({
        isError: true,
        error: new Error("Training failed"),
      }) as unknown as ReturnType<typeof hooks.useRetrain>
    );
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    expect(screen.getByText(/Training failed/)).toBeInTheDocument();
  });

  it("shows Training… when retrain is pending", () => {
    vi.mocked(hooks.useRetrain).mockReturnValue(
      makeMutationMock({ isPending: true }) as unknown as ReturnType<
        typeof hooks.useRetrain>
    );
    renderPage();
    fireEvent.click(screen.getByText("Retrain"));
    expect(screen.getByText("Training…")).toBeInTheDocument();
    expect(screen.getByText("Training…")).toBeDisabled();
  });

  // ── Inference panel ─────────────────────────────────────────────────────────

  it("inference panel shows hint when no model selected", () => {
    renderPage();
    fireEvent.click(screen.getByText("Inference"));
    expect(
      screen.getByText(/Select a model from the list to run inference/)
    ).toBeInTheDocument();
  });

  it("inference panel shows textarea after model is selected", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    fireEvent.click(screen.getByText("Inference"));
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("inference panel shows model name after selection", () => {
    renderPage();
    fireEvent.click(screen.getAllByText("XGBoost Fraud Classifier")[0]);
    fireEvent.click(screen.getByText("Inference"));
    // Both the model card and the inference panel header show the name
    expect(screen.getAllByText("XGBoost Fraud Classifier").length).toBeGreaterThanOrEqual(2);
  });

  it("calls inference.mutate with correct model id on submit", () => {
    const mutateMock = vi.fn();
    vi.mocked(hooks.useInference).mockReturnValue(
      makeMutationMock({ mutate: mutateMock }) as unknown as ReturnType<
        typeof hooks.useInference
      >
    );
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    fireEvent.click(screen.getByText("Inference"));
    fireEvent.click(screen.getByText("Run Inference"));
    expect(mutateMock).toHaveBeenCalledWith(
      expect.objectContaining({ modelId: "reg-xgb-001" }),
      expect.anything()
    );
  });

  it("shows parse error for invalid JSON features", () => {
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    fireEvent.click(screen.getByText("Inference"));
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "not valid json" } });
    fireEvent.click(screen.getByText("Run Inference"));
    expect(screen.getByText(/SyntaxError|Must be a 2-D array/i)).toBeInTheDocument();
  });

  it("shows inference error when mutation fails", () => {
    vi.mocked(hooks.useInference).mockReturnValue(
      makeMutationMock({
        isError: true,
        error: new Error("Model not active"),
      }) as unknown as ReturnType<typeof hooks.useInference>
    );
    renderPage();
    fireEvent.click(screen.getByText("XGBoost Fraud Classifier"));
    fireEvent.click(screen.getByText("Inference"));
    expect(screen.getByText(/Model not active/)).toBeInTheDocument();
  });
});
