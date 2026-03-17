/**
 * F5 — Risk Scoring Dashboard: Frontend tests
 *
 * Framework: Vitest + React Testing Library
 * Coverage: components, hooks, and integration rendering
 *
 * Run:
 *   cd frontend
 *   npx vitest run src/app/\(dashboard\)/risk-scoring/__tests__/page.test.tsx
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// Mock the hooks so tests are isolated from the API
vi.mock("@/hooks/use-risk-scoring", () => ({
  useRiskDistribution: vi.fn(),
  useTopRiskEntities: vi.fn(),
  useCalculateRisk: vi.fn(),
  useEntityRiskProfile: vi.fn(),
  useRiskHistory: vi.fn(),
  useAutoUpdateRisk: vi.fn(),
  riskScoringKeys: {
    all: ["risk-scoring"],
    profile: (id: string) => ["risk-scoring", "profile", id],
    history: (id: string) => ["risk-scoring", "history", id],
    distribution: () => ["risk-scoring", "distribution"],
    topRisk: (n?: number) => ["risk-scoring", "top-risk", n],
  },
}));

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock("recharts", () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div />,
  Cell: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div />,
  Legend: () => <div />,
}));

import * as hooks from "@/hooks/use-risk-scoring";
import RiskScoringPage from "../page";
import { RiskDistributionChart } from "@/components/charts/risk-distribution-chart";
import { RISK_LEVEL_CONFIG, RISK_CHART_COLORS } from "@/types/risk-scoring";
import type {
  RiskDistribution,
  TopRiskEntities,
  CalculateRiskResponse,
  EntityRiskProfile,
  RiskScoreHistory,
  AutoUpdateResponse,
} from "@/types/risk-scoring";

// ── Test fixtures ─────────────────────────────────────────────────────────────

const mockDistribution: RiskDistribution = {
  total_entities: 8,
  tiers: [
    { risk_level: "low", count: 2, percentage: 25.0 },
    { risk_level: "medium", count: 2, percentage: 25.0 },
    { risk_level: "high", count: 2, percentage: 25.0 },
    { risk_level: "critical", count: 2, percentage: 25.0 },
  ],
  thresholds: { low_max: 0.3, medium_max: 0.6, high_max: 0.8, critical_max: 1.0 },
};

const mockTopRisk: TopRiskEntities = {
  total_returned: 3,
  entities: [
    {
      rank: 1,
      entity_id: "ent-005",
      overall_score: 0.92,
      risk_level: "critical",
      risk_factors: ["Watchlist match"],
      last_updated: new Date().toISOString(),
    },
    {
      rank: 2,
      entity_id: "ent-001",
      overall_score: 0.82,
      risk_level: "critical",
      risk_factors: ["High ML fraud probability"],
      last_updated: new Date().toISOString(),
    },
    {
      rank: 3,
      entity_id: "ent-008",
      overall_score: 0.78,
      risk_level: "high",
      risk_factors: ["Rules engine triggered"],
      last_updated: new Date().toISOString(),
    },
  ],
};

const mockCalcResponse: CalculateRiskResponse = {
  entity_id: "test-ent",
  overall_score: 0.75,
  risk_level: "high",
  component_scores: {
    ml_score: 0.8,
    rule_score: 0.7,
    velocity_score: 0.5,
    behavioral_score: 0.6,
    network_score: 0.3,
  },
  risk_factors: ["High ML fraud probability", "Rules engine triggered"],
  explanation: "Composite risk score 0.7500 (HIGH). Primary driver: ML model output.",
  model_version: "risk_scorer_v1.0.0",
  record_id: "rec-123",
};

const mockProfile: EntityRiskProfile = {
  entity_id: "ent-001",
  current_score: 0.82,
  risk_level: "critical",
  component_scores: {
    ml_score: 0.82,
    rule_score: 0.75,
    velocity_score: 0.60,
    behavioral_score: 0.70,
    network_score: 0.50,
  },
  risk_factors: ["High ML fraud probability", "Watchlist match"],
  model_version: "risk_scorer_v1.0.0",
  explanation: "Critical risk entity.",
  last_updated: new Date().toISOString(),
  score_trend: [0.7, 0.75, 0.78, 0.80, 0.82],
};

const mockHistory: RiskScoreHistory = {
  entity_id: "ent-001",
  total: 2,
  history: [
    {
      id: "h1",
      overall_score: 0.80,
      risk_level: "critical",
      component_scores: mockProfile.component_scores,
      risk_factors: ["High ML fraud probability"],
      transaction_id: null,
      created_at: new Date().toISOString(),
    },
    {
      id: "h2",
      overall_score: 0.82,
      risk_level: "critical",
      component_scores: mockProfile.component_scores,
      risk_factors: ["High ML fraud probability"],
      transaction_id: null,
      created_at: new Date().toISOString(),
    },
  ],
};

const mockAutoUpdate: AutoUpdateResponse = {
  entity_id: "ent-001",
  trigger: "new_transaction",
  previous_score: 0.80,
  new_score: 0.85,
  risk_level: "critical",
  updated: true,
};

// ── Wrapper ───────────────────────────────────────────────────────────────────

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
  );
}

// ── Setup default hook mocks ──────────────────────────────────────────────────

function setupDefaultMocks() {
  vi.mocked(hooks.useRiskDistribution).mockReturnValue({
    data: mockDistribution,
    isLoading: false,
    refetch: vi.fn(),
  } as never);

  vi.mocked(hooks.useTopRiskEntities).mockReturnValue({
    data: mockTopRisk,
    isLoading: false,
  } as never);

  vi.mocked(hooks.useCalculateRisk).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    data: undefined,
    error: null,
  } as never);

  vi.mocked(hooks.useEntityRiskProfile).mockReturnValue({
    data: undefined,
    isLoading: false,
  } as never);

  vi.mocked(hooks.useRiskHistory).mockReturnValue({
    data: undefined,
  } as never);

  vi.mocked(hooks.useAutoUpdateRisk).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    data: undefined,
  } as never);
}

// ═══════════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe("RiskScoringPage", () => {
  beforeEach(() => {
    setupDefaultMocks();
  });

  // ── Page structure ──────────────────────────────────────────────────────────

  it("renders the page heading", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Risk Scoring")).toBeInTheDocument();
  });

  it("renders all four stat cards", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Total Entities")).toBeInTheDocument();
    expect(screen.getByText("Critical Risk")).toBeInTheDocument();
    expect(screen.getByText("High Risk")).toBeInTheDocument();
    expect(screen.getByText("Top Score")).toBeInTheDocument();
  });

  // ── F5.5: Distribution chart ────────────────────────────────────────────────

  it("renders the risk distribution chart when data is available", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Risk Distribution")).toBeInTheDocument();
    expect(screen.getByText("8 entities tracked")).toBeInTheDocument();
  });

  it("shows loading spinner when distribution is loading", () => {
    vi.mocked(hooks.useRiskDistribution).mockReturnValue({
      data: undefined,
      isLoading: true,
      refetch: vi.fn(),
    } as never);
    renderWithQuery(<RiskScoringPage />);
    // Spinner rendered — no distribution chart
    expect(screen.queryByText("Risk Distribution")).not.toBeInTheDocument();
  });

  it("shows stat card values from distribution", () => {
    renderWithQuery(<RiskScoringPage />);
    // Total entities
    expect(screen.getByText("8")).toBeInTheDocument();
    // Critical count = 2, high count = 2
    const twos = screen.getAllByText("2");
    expect(twos.length).toBeGreaterThanOrEqual(2);
  });

  // ── F5.6: Top-N leaderboard ─────────────────────────────────────────────────

  it("renders top risk entities leaderboard", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Top Risk Entities")).toBeInTheDocument();
    expect(screen.getByText("ent-005")).toBeInTheDocument();
    expect(screen.getByText("ent-001")).toBeInTheDocument();
    expect(screen.getByText("ent-008")).toBeInTheDocument();
  });

  it("shows rank numbers for entities", () => {
    renderWithQuery(<RiskScoringPage />);
    // Rank badges are <span> elements; use getAllByText to handle ambiguity
    const ones = screen.getAllByText("1");
    const twos = screen.getAllByText("2");
    const threes = screen.getAllByText("3");
    expect(ones.some((el) => el.tagName === "SPAN")).toBe(true);
    expect(twos.some((el) => el.tagName === "SPAN")).toBe(true);
    expect(threes.some((el) => el.tagName === "SPAN")).toBe(true);
  });

  it("shows loading spinner for top risk when loading", () => {
    vi.mocked(hooks.useTopRiskEntities).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as never);
    renderWithQuery(<RiskScoringPage />);
    expect(screen.queryByText("ent-005")).not.toBeInTheDocument();
  });

  // ── F5.1: Calculate form ────────────────────────────────────────────────────

  it("renders the calculate form", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Calculate Risk Score")).toBeInTheDocument();
    // Two inputs share this placeholder (calculate form + auto-update form)
    expect(screen.getAllByPlaceholderText("e.g. ent-001").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: "Calculate" })).toBeInTheDocument();
  });

  it("calculate button is disabled when entity ID is empty", () => {
    renderWithQuery(<RiskScoringPage />);
    const btn = screen.getByRole("button", { name: "Calculate" });
    expect(btn).toBeDisabled();
  });

  it("calculate button enabled after entering entity ID", () => {
    renderWithQuery(<RiskScoringPage />);
    // First placeholder match is the calculate-form input
    const input = screen.getAllByPlaceholderText("e.g. ent-001")[0];
    fireEvent.change(input, { target: { value: "ent-test" } });
    expect(screen.getByRole("button", { name: "Calculate" })).not.toBeDisabled();
  });

  it("calls calculateMutation.mutate on form submit", async () => {
    const mutate = vi.fn();
    vi.mocked(hooks.useCalculateRisk).mockReturnValue({
      mutate,
      isPending: false,
      isError: false,
      data: undefined,
    } as never);
    renderWithQuery(<RiskScoringPage />);
    // First placeholder match is the calculate-form input
    fireEvent.change(screen.getAllByPlaceholderText("e.g. ent-001")[0], {
      target: { value: "ent-test" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Calculate" }));
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ entity_id: "ent-test" })
    );
  });

  it("shows calculation result when data is available", () => {
    vi.mocked(hooks.useCalculateRisk).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: mockCalcResponse,
    } as never);
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Overall Score")).toBeInTheDocument();
    expect(screen.getByText("0.7500")).toBeInTheDocument();
  });

  it("shows error message on calculation failure", () => {
    vi.mocked(hooks.useCalculateRisk).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: true,
      data: undefined,
      error: new Error("API error"),
    } as never);
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("API error")).toBeInTheDocument();
  });

  // ── F5.3: Entity profile / component breakdown ──────────────────────────────

  it("shows entity profile when a profile is loaded", () => {
    vi.mocked(hooks.useEntityRiskProfile).mockReturnValue({
      data: mockProfile,
      isLoading: false,
    } as never);
    vi.mocked(hooks.useRiskHistory).mockReturnValue({
      data: mockHistory,
    } as never);
    renderWithQuery(<RiskScoringPage />);
    // "0.8200" appears in the large score <p> AND the ml_score ScoreBar <span>
    expect(screen.getAllByText("0.8200").some((el) => el.tagName === "P")).toBe(true);
    expect(screen.getByText("ML Score")).toBeInTheDocument();
    expect(screen.getByText("Rule Score")).toBeInTheDocument();
    expect(screen.getByText("Velocity Score")).toBeInTheDocument();
    expect(screen.getByText("Behavioral Score")).toBeInTheDocument();
    expect(screen.getByText("Network Score")).toBeInTheDocument();
  });

  it("shows prompt when no entity is selected", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(
      screen.getByText(/Select an entity from the leaderboard/)
    ).toBeInTheDocument();
  });

  // ── F5.7: Auto-update panel ─────────────────────────────────────────────────

  it("renders auto-update section", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Auto-Update Risk Score (F5.7)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trigger Update" })).toBeInTheDocument();
  });

  it("auto-update button disabled when no entity ID", () => {
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByRole("button", { name: "Trigger Update" })).toBeDisabled();
  });

  it("shows auto-update result after success", () => {
    vi.mocked(hooks.useAutoUpdateRisk).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: mockAutoUpdate,
    } as never);
    renderWithQuery(<RiskScoringPage />);
    expect(screen.getByText("Updated")).toBeInTheDocument();
    expect(screen.getByText("0.8500")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// RiskDistributionChart Component Tests (F5.5)
// ═══════════════════════════════════════════════════════════════════════════════

describe("RiskDistributionChart", () => {
  it("renders chart heading", () => {
    render(<RiskDistributionChart data={mockDistribution} />);
    expect(screen.getByText("Risk Distribution")).toBeInTheDocument();
  });

  it("renders entity count", () => {
    render(<RiskDistributionChart data={mockDistribution} />);
    expect(screen.getByText("8 entities tracked")).toBeInTheDocument();
  });

  it("renders all four tier cards", () => {
    render(<RiskDistributionChart data={mockDistribution} />);
    expect(screen.getAllByText("Low").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Medium").length).toBeGreaterThan(0);
    expect(screen.getAllByText("High").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Critical").length).toBeGreaterThan(0);
  });

  it("renders percentage values in tier cards", () => {
    render(<RiskDistributionChart data={mockDistribution} />);
    const pcts = screen.getAllByText("25%");
    expect(pcts.length).toBe(4);
  });

  it("renders the bar chart element", () => {
    render(<RiskDistributionChart data={mockDistribution} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Type / Config Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe("RISK_LEVEL_CONFIG", () => {
  it("has entries for all four risk levels", () => {
    expect(RISK_LEVEL_CONFIG.low).toBeDefined();
    expect(RISK_LEVEL_CONFIG.medium).toBeDefined();
    expect(RISK_LEVEL_CONFIG.high).toBeDefined();
    expect(RISK_LEVEL_CONFIG.critical).toBeDefined();
  });

  it("each entry has label, color, bg, border", () => {
    for (const cfg of Object.values(RISK_LEVEL_CONFIG)) {
      expect(cfg.label).toBeTruthy();
      expect(cfg.color).toBeTruthy();
      expect(cfg.bg).toBeTruthy();
      expect(cfg.border).toBeTruthy();
    }
  });
});

describe("RISK_CHART_COLORS", () => {
  it("has a hex color for all four levels", () => {
    for (const color of Object.values(RISK_CHART_COLORS)) {
      expect(color).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Hook key factory Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe("riskScoringKeys", () => {
  const { riskScoringKeys: keys } = hooks;

  it("profile key includes entity id", () => {
    expect(keys.profile("ent-001")).toContain("ent-001");
  });

  it("history key includes entity id", () => {
    expect(keys.history("ent-001")).toContain("ent-001");
  });

  it("all keys start with risk-scoring", () => {
    expect(keys.all[0]).toBe("risk-scoring");
    expect(keys.distribution()[0]).toBe("risk-scoring");
    expect(keys.topRisk()[0]).toBe("risk-scoring");
  });
});
