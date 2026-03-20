import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  SystemSettings,
  TeamListResponse,
  WebhookConfig,
  ApiKey,
} from "@/types/settings";

export function useSystemSettings() {
  return useQuery<SystemSettings>({
    queryKey: ["settings", "system"],
    queryFn: () => api.get<SystemSettings>("/settings/system"),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation<SystemSettings, Error, Partial<SystemSettings>>({
    mutationFn: (body) => api.put<SystemSettings>("/settings/system", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "system"] }),
  });
}

export function useTeamMembers() {
  return useQuery<TeamListResponse>({
    queryKey: ["settings", "team"],
    queryFn: () => api.get<TeamListResponse>("/settings/team"),
  });
}

export function useWebhooks() {
  return useQuery<WebhookConfig[]>({
    queryKey: ["webhooks"],
    queryFn: () => api.get<WebhookConfig[]>("/webhooks"),
  });
}

export function useCreateWebhook() {
  const qc = useQueryClient();
  return useMutation<WebhookConfig, Error, { name: string; url: string; events: string[]; secret: string }>({
    mutationFn: (body) => api.post<WebhookConfig>("/webhooks", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useDeleteWebhook() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (id) => api.delete<void>(`/webhooks/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useApiKeys() {
  return useQuery<ApiKey[]>({
    queryKey: ["settings", "api-keys"],
    queryFn: () => api.get<ApiKey[]>("/settings/api-keys"),
  });
}

export function useCreateApiKey() {
  const qc = useQueryClient();
  return useMutation<ApiKey & { full_key?: string }, Error, { name: string; expires_in_days: number }>({
    mutationFn: (body) => api.post<ApiKey & { full_key?: string }>("/settings/api-keys", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "api-keys"] }),
  });
}
