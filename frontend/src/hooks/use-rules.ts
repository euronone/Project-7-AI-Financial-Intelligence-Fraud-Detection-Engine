import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Rule, RuleListResponse, RuleTemplate, RuleTestResult } from "@/types/rule";

export function useRules(page: number, pageSize: number, filters?: { is_active?: boolean; category?: string }) {
  const params: Record<string, string | number | boolean | undefined> = {
    page,
    page_size: pageSize,
    ...filters,
  };
  return useQuery<RuleListResponse>({
    queryKey: ["rules", page, pageSize, filters],
    queryFn: () => api.get<RuleListResponse>("/rules", { params }),
  });
}

export function useRule(id: string | undefined) {
  return useQuery<Rule>({
    queryKey: ["rules", id],
    queryFn: () => api.get<Rule>(`/rules/${id}`),
    enabled: !!id,
  });
}

export function useRuleTemplates() {
  return useQuery<RuleTemplate[]>({
    queryKey: ["rules", "templates"],
    queryFn: () => api.get<RuleTemplate[]>("/rules/templates"),
  });
}

export function useCreateRule() {
  const qc = useQueryClient();
  return useMutation<Rule, Error, Partial<Rule>>({
    mutationFn: (data) => api.post<Rule>("/rules", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
}

export function useUpdateRule(id: string) {
  const qc = useQueryClient();
  return useMutation<Rule, Error, Partial<Rule>>({
    mutationFn: (data) => api.put<Rule>(`/rules/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
}

export function useToggleRule() {
  const qc = useQueryClient();
  return useMutation<Rule, Error, { id: string; is_active: boolean }>({
    mutationFn: ({ id, is_active }) => api.patch<Rule>(`/rules/${id}/toggle`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
}

export function useDeleteRule() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, string>({
    mutationFn: (id) => api.delete(`/rules/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
}

export function useTestRule(id: string) {
  return useMutation<RuleTestResult, Error, Record<string, unknown>>({
    mutationFn: (transaction) => api.post<RuleTestResult>(`/rules/${id}/test`, { transaction }),
  });
}
