import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { EntityDetail, EntityFilters, EntityListResponse } from "@/types/entity";
import type { TransactionListResponse } from "@/types/transaction";

export function useEntities(page: number, pageSize: number, filters?: EntityFilters) {
  const params: Record<string, string | number | boolean | undefined> = {
    page,
    page_size: pageSize,
    ...filters,
  };

  return useQuery<EntityListResponse>({
    queryKey: ["entities", page, pageSize, filters],
    queryFn: () => api.get<EntityListResponse>("/entities", { params }),
  });
}

export function useEntity(id: string | undefined) {
  return useQuery<EntityDetail>({
    queryKey: ["entities", id],
    queryFn: () => api.get<EntityDetail>(`/entities/${id}`),
    enabled: !!id,
  });
}

export function useEntityTransactions(id: string | undefined, page: number = 1) {
  return useQuery<TransactionListResponse>({
    queryKey: ["entities", id, "transactions", page],
    queryFn: () => api.get<TransactionListResponse>(`/entities/${id}/transactions`, { params: { page, page_size: 10 } }),
    enabled: !!id,
  });
}
