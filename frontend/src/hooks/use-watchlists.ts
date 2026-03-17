import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ScreeningResponse, WatchlistFilters, WatchlistListResponse } from "@/types/watchlist";

export function useWatchlists(page: number, pageSize: number, filters?: WatchlistFilters) {
  const params: Record<string, string | number | boolean | undefined> = {
    page,
    page_size: pageSize,
    ...filters,
  };

  return useQuery<WatchlistListResponse>({
    queryKey: ["watchlists", page, pageSize, filters],
    queryFn: () => api.get<WatchlistListResponse>("/watchlists", { params }),
  });
}

export function useScreenEntity() {
  return useMutation<ScreeningResponse, Error, { entity_name: string }>({
    mutationFn: (data) => api.post<ScreeningResponse>("/watchlists/screen", data),
  });
}

export function useDeleteWatchlistEntry() {
  const queryClient = useQueryClient();
  return useMutation<unknown, Error, string>({
    mutationFn: (id) => api.delete(`/watchlists/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["watchlists"] }),
  });
}
