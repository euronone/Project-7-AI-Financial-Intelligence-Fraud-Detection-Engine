// F5 — Risk Scoring: TanStack Query hooks

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from "@tanstack/react-query";
import type {
  AutoUpdateRequest,
  AutoUpdateResponse,
  CalculateRiskRequest,
  CalculateRiskResponse,
  EntityRiskProfile,
  RiskDistribution,
  RiskScoreHistory,
  TopRiskEntities,
} from "@/types/risk-scoring";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? "API error");
  }
  return res.json() as Promise<T>;
}

// ── Query keys ───────────────────────────────────────────────────────────────

export const riskScoringKeys = {
  all: ["risk-scoring"] as const,
  profile: (entityId: string) =>
    [...riskScoringKeys.all, "profile", entityId] as const,
  history: (entityId: string, limit?: number, offset?: number) =>
    [...riskScoringKeys.all, "history", entityId, limit, offset] as const,
  distribution: () => [...riskScoringKeys.all, "distribution"] as const,
  topRisk: (n?: number) => [...riskScoringKeys.all, "top-risk", n] as const,
};

// ── F5.1 / F5.3: Entity risk profile ────────────────────────────────────────

export function useEntityRiskProfile(
  entityId: string | null
): UseQueryResult<EntityRiskProfile> {
  return useQuery({
    queryKey: riskScoringKeys.profile(entityId ?? ""),
    queryFn: () =>
      apiFetch<EntityRiskProfile>(
        `${API_BASE}/risk-scoring/entity/${entityId}`
      ),
    enabled: Boolean(entityId),
    staleTime: 30_000,
  });
}

// ── F5.4: Risk score history ─────────────────────────────────────────────────

export function useRiskHistory(
  entityId: string | null,
  limit = 30,
  offset = 0
): UseQueryResult<RiskScoreHistory> {
  return useQuery({
    queryKey: riskScoringKeys.history(entityId ?? "", limit, offset),
    queryFn: () =>
      apiFetch<RiskScoreHistory>(
        `${API_BASE}/risk-scoring/entity/${entityId}/history?limit=${limit}&offset=${offset}`
      ),
    enabled: Boolean(entityId),
    staleTime: 30_000,
  });
}

// ── F5.1: On-demand risk calculation ────────────────────────────────────────

export function useCalculateRisk(): UseMutationResult<
  CalculateRiskResponse,
  Error,
  CalculateRiskRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CalculateRiskRequest) =>
      apiFetch<CalculateRiskResponse>(`${API_BASE}/risk-scoring/calculate`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      // Invalidate profile + history for the scored entity
      qc.invalidateQueries({
        queryKey: riskScoringKeys.profile(data.entity_id),
      });
      qc.invalidateQueries({
        queryKey: riskScoringKeys.history(data.entity_id),
      });
      qc.invalidateQueries({ queryKey: riskScoringKeys.distribution() });
      qc.invalidateQueries({ queryKey: riskScoringKeys.topRisk() });
    },
  });
}

// ── F5.5: Risk distribution ──────────────────────────────────────────────────

export function useRiskDistribution(): UseQueryResult<RiskDistribution> {
  return useQuery({
    queryKey: riskScoringKeys.distribution(),
    queryFn: () =>
      apiFetch<RiskDistribution>(`${API_BASE}/risk-scoring/distribution`),
    staleTime: 60_000,
  });
}

// ── F5.6: Top-N highest risk entities ───────────────────────────────────────

export function useTopRiskEntities(n = 10): UseQueryResult<TopRiskEntities> {
  return useQuery({
    queryKey: riskScoringKeys.topRisk(n),
    queryFn: () =>
      apiFetch<TopRiskEntities>(
        `${API_BASE}/risk-scoring/top-risk?n=${n}`
      ),
    staleTime: 30_000,
  });
}

// ── F5.7: Auto-update on event ───────────────────────────────────────────────

export function useAutoUpdateRisk(): UseMutationResult<
  AutoUpdateResponse,
  Error,
  AutoUpdateRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AutoUpdateRequest) =>
      apiFetch<AutoUpdateResponse>(`${API_BASE}/risk-scoring/auto-update`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({
        queryKey: riskScoringKeys.profile(data.entity_id),
      });
      qc.invalidateQueries({
        queryKey: riskScoringKeys.history(data.entity_id),
      });
      qc.invalidateQueries({ queryKey: riskScoringKeys.distribution() });
      qc.invalidateQueries({ queryKey: riskScoringKeys.topRisk() });
    },
  });
}
