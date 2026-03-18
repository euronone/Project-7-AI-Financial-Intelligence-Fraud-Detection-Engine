"use client";

import { useState } from "react";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";

export interface PaginationState {
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  reset: () => void;
}

/**
 * Simple pagination state hook.
 * Reset to page 1 whenever filters change.
 */
export function usePagination(initialPageSize = DEFAULT_PAGE_SIZE): PaginationState {
  const [page, setPageRaw] = useState(1);
  const [pageSize, setPageSizeRaw] = useState(initialPageSize);

  function setPage(p: number) {
    setPageRaw(p);
  }

  function setPageSize(size: number) {
    setPageSizeRaw(size);
    setPageRaw(1); // reset to first page when size changes
  }

  function reset() {
    setPageRaw(1);
  }

  return { page, pageSize, setPage, setPageSize, reset };
}
