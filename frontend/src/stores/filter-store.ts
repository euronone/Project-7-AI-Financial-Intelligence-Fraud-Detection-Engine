"use client";

/**
 * Zustand store for active transaction filter state.
 *
 * Shared between the transaction list page, export button, and URL sync.
 */
import { create } from "zustand";

import type { TransactionFilters } from "@/types/transaction";

interface FilterStore {
  filters: TransactionFilters;
  setFilters: (partial: Partial<TransactionFilters>) => void;
  resetFilters: () => void;
}

const DEFAULT_FILTERS: TransactionFilters = {
  sort_by: "processed_at",
  sort_order: "desc",
  page: 1,
  page_size: 20,
};

export const useFilterStore = create<FilterStore>((set) => ({
  filters: DEFAULT_FILTERS,

  setFilters: (partial) =>
    set((state) => ({
      filters: {
        ...state.filters,
        ...partial,
        page: partial.page ?? 1, // reset to page 1 on any filter change
      },
    })),

  resetFilters: () => set({ filters: DEFAULT_FILTERS }),
}));
