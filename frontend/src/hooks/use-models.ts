import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { MLModel, MLModelListResponse } from "@/types/model";

export function useModels(filters?: { model_type?: string; status?: string }) {
  return useQuery<MLModelListResponse>({
    queryKey: ["models", filters],
    queryFn: () => api.get<MLModelListResponse>("/models", { params: filters }),
  });
}

export function useModel(id: string | undefined) {
  return useQuery<MLModel>({
    queryKey: ["models", id],
    queryFn: () => api.get<MLModel>(`/models/${id}`),
    enabled: !!id,
  });
}

export function usePromoteModel() {
  const qc = useQueryClient();
  return useMutation<MLModel, Error, string>({
    mutationFn: (id) => api.post<MLModel>(`/models/${id}/promote`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["models"] }),
  });
}

export function useRetireModel() {
  const qc = useQueryClient();
  return useMutation<MLModel, Error, string>({
    mutationFn: (id) => api.post<MLModel>(`/models/${id}/retire`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["models"] }),
  });
}
