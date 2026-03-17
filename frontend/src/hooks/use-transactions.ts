import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Transaction, TransactionFilters, TransactionListResponse } from "@/types/transaction";

export function useTransactions(page: number, pageSize: number, filters?: TransactionFilters) {
  const params: Record<string, string | number | boolean | undefined> = {
    page,
    page_size: pageSize,
    ...filters,
  };

  return useQuery<TransactionListResponse>({
    queryKey: ["transactions", page, pageSize, filters],
    queryFn: () => api.get<TransactionListResponse>("/transactions", { params }),
  });
}

export function useTransaction(id: string | undefined) {
  return useQuery<Transaction>({
    queryKey: ["transactions", id],
    queryFn: () => api.get<Transaction>(`/transactions/${id}`),
    enabled: !!id,
  });
}
