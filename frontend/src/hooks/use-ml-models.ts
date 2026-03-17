// Phase 3 — ML Model Registry: TanStack Query hooks (F2.7 / F2.8 / F2.9)

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from "@tanstack/react-query";
import type {
  RegisteredModel,
  RegisterModelRequest,
  RetrainRequest,
  RetrainResponse,
  InferenceRequest,
  InferenceResponse,
  ModelMetrics,
} from "@/types/ml-models";

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

// ── Query keys ────────────────────────────────────────────────────────────────

export const mlModelKeys = {
  all: ["ml-models"] as const,
  list: (modelType?: string, status?: string) =>
    [...mlModelKeys.all, "list", modelType, status] as const,
  detail: (id: string) => [...mlModelKeys.all, "detail", id] as const,
  metrics: (id: string) => [...mlModelKeys.all, "metrics", id] as const,
};

// ── F2.7: List models ─────────────────────────────────────────────────────────

export function useModels(
  modelType?: string,
  status?: string
): UseQueryResult<RegisteredModel[]> {
  const params = new URLSearchParams();
  if (modelType) params.set("model_type", modelType);
  if (status) params.set("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";

  return useQuery({
    queryKey: mlModelKeys.list(modelType, status),
    queryFn: () =>
      apiFetch<RegisteredModel[]>(`${API_BASE}/models${qs}`),
    staleTime: 30_000,
  });
}

// ── F2.7: Get model detail ────────────────────────────────────────────────────

export function useModel(id: string | null): UseQueryResult<RegisteredModel> {
  return useQuery({
    queryKey: mlModelKeys.detail(id ?? ""),
    queryFn: () => apiFetch<RegisteredModel>(`${API_BASE}/models/${id}`),
    enabled: Boolean(id),
    staleTime: 30_000,
  });
}

// ── F2.7: Get model metrics ───────────────────────────────────────────────────

export function useModelMetrics(
  id: string | null
): UseQueryResult<{ model_id: string; metrics: ModelMetrics }> {
  return useQuery({
    queryKey: mlModelKeys.metrics(id ?? ""),
    queryFn: () =>
      apiFetch<{ model_id: string; metrics: ModelMetrics }>(
        `${API_BASE}/models/${id}/metrics`
      ),
    enabled: Boolean(id),
    staleTime: 30_000,
  });
}

// ── F2.7: Register model ──────────────────────────────────────────────────────

export function useRegisterModel(): UseMutationResult<
  RegisteredModel,
  Error,
  RegisterModelRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RegisterModelRequest) =>
      apiFetch<RegisteredModel>(`${API_BASE}/models/register`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: mlModelKeys.list() });
    },
  });
}

// ── F2.7: Promote model ───────────────────────────────────────────────────────

export function usePromoteModel(): UseMutationResult<
  RegisteredModel,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<RegisteredModel>(`${API_BASE}/models/${id}/promote`, {
        method: "POST",
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: mlModelKeys.list() });
      qc.setQueryData(mlModelKeys.detail(data.id), data);
    },
  });
}

// ── F2.7: Retire model ────────────────────────────────────────────────────────

export function useRetireModel(): UseMutationResult<
  RegisteredModel,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<RegisteredModel>(`${API_BASE}/models/${id}/retire`, {
        method: "POST",
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: mlModelKeys.list() });
      qc.setQueryData(mlModelKeys.detail(data.id), data);
    },
  });
}

// ── F2.7: Update metrics ──────────────────────────────────────────────────────

export function useUpdateMetrics(): UseMutationResult<
  RegisteredModel,
  Error,
  { id: string; metrics: Record<string, number> }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, metrics }) =>
      apiFetch<RegisteredModel>(`${API_BASE}/models/${id}/metrics`, {
        method: "PATCH",
        body: JSON.stringify({ metrics }),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: mlModelKeys.list() });
      qc.setQueryData(mlModelKeys.detail(data.id), data);
      qc.invalidateQueries({ queryKey: mlModelKeys.metrics(data.id) });
    },
  });
}

// ── F2.8: Trigger retraining ──────────────────────────────────────────────────

export function useRetrain(): UseMutationResult<
  RetrainResponse,
  Error,
  RetrainRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RetrainRequest) =>
      apiFetch<RetrainResponse>(`${API_BASE}/models/retrain`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: mlModelKeys.list() });
    },
  });
}

// ── F2.9: Run inference ───────────────────────────────────────────────────────

export function useInference(): UseMutationResult<
  InferenceResponse,
  Error,
  { modelId: string; features: number[][] }
> {
  return useMutation({
    mutationFn: ({ modelId, features }: { modelId: string; features: number[][] }) =>
      apiFetch<InferenceResponse>(`${API_BASE}/models/${modelId}/infer`, {
        method: "POST",
        body: JSON.stringify({ features } as InferenceRequest),
      }),
  });
}
