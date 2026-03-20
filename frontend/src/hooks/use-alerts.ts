import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { AlertListResponse, AlertStatistics, FraudAlert } from "@/types/alert";
import type { Case } from "@/types/case";

export function useAlerts(page: number, pageSize: number, filters?: { status?: string; severity?: string; alert_type?: string }) {
  return useQuery<AlertListResponse>({
    queryKey: ["alerts", page, pageSize, filters],
    queryFn: () => api.get<AlertListResponse>("/alerts", { params: { page, page_size: pageSize, ...filters } }),
  });
}

export function useAlert(id: string | undefined) {
  return useQuery<FraudAlert>({
    queryKey: ["alerts", id],
    queryFn: () => api.get<FraudAlert>(`/alerts/${id}`),
    enabled: !!id,
  });
}

export function useAlertStatistics() {
  return useQuery<AlertStatistics>({
    queryKey: ["alerts", "statistics"],
    queryFn: () => api.get<AlertStatistics>("/alerts/statistics"),
  });
}

export function useUpdateAlertStatus() {
  const qc = useQueryClient();
  return useMutation<FraudAlert, Error, { id: string; status: string; resolution_notes?: string }>({
    mutationFn: ({ id, ...body }) => api.patch<FraudAlert>(`/alerts/${id}/status`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useAssignAlert() {
  const qc = useQueryClient();
  return useMutation<FraudAlert, Error, { id: string; assigned_to: string }>({
    mutationFn: ({ id, assigned_to }) => api.patch<FraudAlert>(`/alerts/${id}/assign`, { assigned_to }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useEscalateAlert() {
  const qc = useQueryClient();
  return useMutation<FraudAlert, Error, string>({
    mutationFn: (id) => api.post<FraudAlert>(`/alerts/${id}/escalate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useCreateCaseFromAlert() {
  const qc = useQueryClient();
  return useMutation<Case, Error, string>({
    mutationFn: (alertId) => api.post<Case>(`/alerts/${alertId}/create-case`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
