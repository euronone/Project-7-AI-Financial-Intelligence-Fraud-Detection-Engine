import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { PipelineResult, RiskDistribution, RiskScoreListResponse, TopRiskEntity } from "@/types/risk";

export function useScoreTransaction() {
  const qc = useQueryClient();
  return useMutation<PipelineResult, Error, string>({
    mutationFn: (txnId) => api.post<PipelineResult>(`/risk/transactions/${txnId}/score`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["risk"] }),
  });
}

export function useCalculateEntityRisk() {
  const qc = useQueryClient();
  return useMutation<PipelineResult, Error, string>({
    mutationFn: (entityId) => api.post<PipelineResult>(`/risk/entities/${entityId}/calculate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["risk"] }),
  });
}

export function useEntityRiskHistory(entityId: string | undefined, page = 1, pageSize = 25) {
  return useQuery<RiskScoreListResponse>({
    queryKey: ["risk", "history", entityId, page],
    queryFn: () => api.get<RiskScoreListResponse>(`/risk/entities/${entityId}/history`, { params: { page, page_size: pageSize } }),
    enabled: !!entityId,
  });
}

export function useRiskDistribution() {
  return useQuery<RiskDistribution>({
    queryKey: ["risk", "distribution"],
    queryFn: () => api.get<RiskDistribution>("/risk/distribution"),
  });
}

export function useTopRiskEntities(limit = 10) {
  return useQuery<TopRiskEntity[]>({
    queryKey: ["risk", "top", limit],
    queryFn: () => api.get<TopRiskEntity[]>("/risk/top-risk", { params: { limit } }),
  });
}
