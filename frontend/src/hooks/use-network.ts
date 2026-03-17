import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  NetworkGraphResponse,
  EntityConnectionResponse,
} from "@/types/network";

export function useNetworkGraph(minTransactions?: number, limit?: number) {
  return useQuery<NetworkGraphResponse>({
    queryKey: ["network", "graph", minTransactions, limit],
    queryFn: () =>
      api.get<NetworkGraphResponse>("/network/graph", {
        params: { min_transactions: minTransactions, limit },
      }),
  });
}

export function useEntityConnections(entityId: string | null) {
  return useQuery<EntityConnectionResponse>({
    queryKey: ["network", "entity", entityId, "connections"],
    queryFn: () =>
      api.get<EntityConnectionResponse>(
        `/network/entity/${entityId}/connections`
      ),
    enabled: !!entityId,
  });
}

export function useNetworkAnalysis() {
  return useMutation<unknown, Error>({
    mutationFn: () => api.post("/network/analyze"),
  });
}
