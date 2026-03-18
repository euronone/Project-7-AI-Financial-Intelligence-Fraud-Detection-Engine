/**
 * Common API response types shared across all resources.
 */

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}

export type SortOrder = "asc" | "desc";
