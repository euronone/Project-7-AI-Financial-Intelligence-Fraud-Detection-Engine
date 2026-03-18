/**
 * Centralised Axios API client for communicating with the FastAPI backend.
 *
 * - Base URL from NEXT_PUBLIC_API_URL env variable
 * - Attaches Authorization header if a JWT is present in session storage
 * - Transforms error responses into typed ApiError objects
 * - Handles 401 → trigger re-authentication
 */
import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
} from "axios";

import type { ApiError } from "@/types/api";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
    timeout: 30_000, // 30s — long enough for batch ingest
  });

  // ── Request interceptor — attach auth token ──────────────────────────────
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = sessionStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  });

  // ── Response interceptor — normalise errors ──────────────────────────────
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      const apiError: ApiError = {
        error: "UNKNOWN_ERROR",
        message: "An unexpected error occurred.",
      };

      if (axios.isAxiosError(error)) {
        const data = error.response?.data;
        if (data?.error) {
          apiError.error = data.error;
          apiError.message = data.message ?? apiError.message;
          apiError.detail = data.detail;
        } else if (error.response?.status === 401) {
          apiError.error = "UNAUTHORIZED";
          apiError.message = "Your session has expired. Please log in again.";
          // In the full auth flow (F11) we'll trigger a redirect here.
        } else if (error.response?.status === 429) {
          apiError.error = "RATE_LIMITED";
          apiError.message = "Too many requests. Please slow down.";
        }
      }

      return Promise.reject(apiError);
    }
  );

  return client;
}

export const apiClient = createApiClient();

// ── Typed helper wrappers ─────────────────────────────────────────────────────

export async function apiGet<T>(
  path: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const res = await apiClient.get<T>(path, config);
  return res.data;
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const res = await apiClient.post<T>(path, body, config);
  return res.data;
}

export async function apiPut<T>(
  path: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const res = await apiClient.put<T>(path, body, config);
  return res.data;
}

export async function apiDelete<T>(
  path: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const res = await apiClient.delete<T>(path, config);
  return res.data;
}
