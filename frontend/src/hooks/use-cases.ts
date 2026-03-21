import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Case, CaseListResponse, CaseStatistics } from "@/types/case";

export function useCases(page: number, pageSize: number, filters?: { status?: string; priority?: string }) {
  return useQuery<CaseListResponse>({
    queryKey: ["cases", page, pageSize, filters],
    queryFn: () => api.get<CaseListResponse>("/cases", { params: { page, page_size: pageSize, ...filters } }),
  });
}

export function useCase(id: string | undefined) {
  return useQuery<Case>({
    queryKey: ["cases", id],
    queryFn: () => api.get<Case>(`/cases/${id}`),
    enabled: !!id,
  });
}

export function useCaseStatistics() {
  return useQuery<CaseStatistics>({
    queryKey: ["cases", "statistics"],
    queryFn: () => api.get<CaseStatistics>("/cases/statistics"),
  });
}

export function useCreateCase() {
  const qc = useQueryClient();
  return useMutation<Case, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<Case>("/cases", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });
}

export function useUpdateCaseStatus() {
  const qc = useQueryClient();
  return useMutation<Case, Error, { id: string; status: string; notes?: string }>({
    mutationFn: ({ id, ...body }) => api.patch<Case>(`/cases/${id}/status`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });
}

export function useAssignCase() {
  const qc = useQueryClient();
  return useMutation<Case, Error, { id: string; assigned_to: string }>({
    mutationFn: ({ id, assigned_to }) => api.patch<Case>(`/cases/${id}/assign`, { assigned_to }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });
}
