export type WatchlistType = "sanctions" | "pep" | "adverse_media" | "internal_blacklist" | "custom";

export interface WatchlistEntry {
  id: string;
  list_name: string;
  list_type: WatchlistType;
  entity_name: string;
  entity_identifiers: Record<string, unknown>;
  source: string;
  match_score: number | null;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WatchlistFilters {
  list_type?: string;
  source?: string;
  is_active?: boolean;
  search?: string;
}

export interface WatchlistListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: WatchlistEntry[];
}

export interface ScreeningMatch {
  watchlist_id: string;
  list_name: string;
  list_type: WatchlistType;
  entity_name: string;
  source: string;
  match_score: number;
}

export interface ScreeningResponse {
  query: string;
  matches: ScreeningMatch[];
  total_matches: number;
}
