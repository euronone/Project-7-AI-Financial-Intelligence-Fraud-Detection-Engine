import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  OverviewStats,
  FraudTrendsResponse,
  TransactionVolumeResponse,
  RiskDistributionResponse,
  TopPatternsResponse,
  GeoResponse,
  ModelPerformanceResponse,
} from "@/types/analytics";

export function useOverviewStats() {
  return useQuery<OverviewStats>({
    queryKey: ["analytics", "overview"],
    queryFn: () => api.get<OverviewStats>("/analytics/overview"),
  });
}

export function useFraudTrends(period: string = "30d") {
  return useQuery<FraudTrendsResponse>({
    queryKey: ["analytics", "fraud-trends", period],
    queryFn: () =>
      api.get<FraudTrendsResponse>("/analytics/fraud-trends", {
        params: { period },
      }),
  });
}

export function useTransactionVolume(period: string = "30d") {
  return useQuery<TransactionVolumeResponse>({
    queryKey: ["analytics", "transaction-volume", period],
    queryFn: () =>
      api.get<TransactionVolumeResponse>("/analytics/transaction-volume", {
        params: { period },
      }),
  });
}

export function useRiskDistribution() {
  return useQuery<RiskDistributionResponse>({
    queryKey: ["analytics", "risk-distribution"],
    queryFn: () =>
      api.get<RiskDistributionResponse>("/analytics/risk-distribution"),
  });
}

export function useTopPatterns() {
  return useQuery<TopPatternsResponse>({
    queryKey: ["analytics", "top-patterns"],
    queryFn: () =>
      api.get<TopPatternsResponse>("/analytics/top-patterns"),
  });
}

export function useGeoData() {
  return useQuery<GeoResponse>({
    queryKey: ["analytics", "geographic"],
    queryFn: () => api.get<GeoResponse>("/analytics/geographic"),
  });
}

export function useModelPerformance() {
  return useQuery<ModelPerformanceResponse>({
    queryKey: ["analytics", "model-performance"],
    queryFn: () =>
      api.get<ModelPerformanceResponse>("/analytics/model-performance"),
  });
}
