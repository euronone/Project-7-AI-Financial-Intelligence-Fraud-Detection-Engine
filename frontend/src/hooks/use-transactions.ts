"use client";

/**
 * TanStack Query v5 hooks for the Transaction resource.
 *
 * Covers F1.1, F1.4, F1.5, F1.6, F1.7:
 * - useTransactions    — paginated list with filters (F1.5)
 * - useTransaction     — single transaction detail (F1.6)
 * - useIngestTransaction — single ingest mutation (F1.1)
 * - useBatchIngest     — batch ingest mutation (F1.4)
 * - useExportTransactions — download export (F1.7)
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiGet, apiPost } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type {
  BatchIngestRequest,
  BatchIngestResponse,
  TransactionCreate,
  TransactionDetail,
  TransactionFilters,
  TransactionResponse,
} from "@/types/transaction";

// ── Query keys ────────────────────────────────────────────────────────────────

export const transactionKeys = {
  all: ["transactions"] as const,
  lists: () => [...transactionKeys.all, "list"] as const,
  list: (filters: TransactionFilters) =>
    [...transactionKeys.lists(), filters] as const,
  details: () => [...transactionKeys.all, "detail"] as const,
  detail: (id: string) => [...transactionKeys.details(), id] as const,
  similar: (id: string) => [...transactionKeys.all, "similar", id] as const,
};

// ── List / search (F1.5) ──────────────────────────────────────────────────────

export function useTransactions(
  filters: TransactionFilters = {}
): UseQueryResult<PaginatedResponse<TransactionResponse>> {
  return useQuery({
    queryKey: transactionKeys.list(filters),
    queryFn: () => apiPost<PaginatedResponse<TransactionResponse>>("/transactions/search", {
      ...filters,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 20,
    }),
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

// ── Detail (F1.6) ─────────────────────────────────────────────────────────────

export function useTransaction(id: string): UseQueryResult<TransactionDetail> {
  return useQuery({
    queryKey: transactionKeys.detail(id),
    queryFn: () => apiGet<TransactionDetail>(`/transactions/${id}`),
    enabled: Boolean(id),
    staleTime: 60_000,
  });
}

// ── Similar transactions (F1.6) ───────────────────────────────────────────────

export function useSimilarTransactions(
  id: string,
  limit = 10
): UseQueryResult<TransactionResponse[]> {
  return useQuery({
    queryKey: transactionKeys.similar(id),
    queryFn: () =>
      apiGet<TransactionResponse[]>(`/transactions/${id}/similar?limit=${limit}`),
    enabled: Boolean(id),
    staleTime: 120_000,
  });
}

// ── Ingest mutation (F1.1) ────────────────────────────────────────────────────

export function useIngestTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TransactionCreate) =>
      apiPost<TransactionDetail>("/transactions", data),
    onSuccess: () => {
      // Invalidate list queries so the new transaction appears
      queryClient.invalidateQueries({ queryKey: transactionKeys.lists() });
    },
  });
}

// ── Batch ingest mutation (F1.4) ──────────────────────────────────────────────

export function useBatchIngest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchIngestRequest) =>
      apiPost<BatchIngestResponse>("/transactions/batch", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: transactionKeys.lists() });
    },
  });
}

// ── Export (F1.7) ─────────────────────────────────────────────────────────────

interface ExportOptions {
  filters: TransactionFilters;
  format: "csv" | "json";
}

export function useExportTransactions() {
  return useMutation({
    mutationFn: async ({ filters, format }: ExportOptions) => {
      const params = new URLSearchParams();
      params.set("fmt", format);
      if (filters.status?.length) params.set("status", filters.status.join(","));
      if (filters.risk_level?.length) params.set("risk_level", filters.risk_level.join(","));
      if (filters.channel?.length) params.set("channel", filters.channel.join(","));
      if (filters.min_amount != null) params.set("min_amount", String(filters.min_amount));
      if (filters.max_amount != null) params.set("max_amount", String(filters.max_amount));
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.entity_id) params.set("entity_id", filters.entity_id);
      if (filters.country_code) params.set("country_code", filters.country_code);
      if (filters.query) params.set("query", filters.query);

      // Use fetch directly to handle binary blob download
      const token = typeof window !== "undefined"
        ? sessionStorage.getItem("access_token")
        : null;
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
      const res = await fetch(`${baseUrl}/transactions/export?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `transactions_export.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });
}
