"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type { LoginRequest, SignupRequest, TokenResponse, User } from "@/types/user";

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading, setAuth, setUser, setLoading, logout: clearAuth, hydrate } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const { data: currentUser } = useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<User>("/auth/me"),
    enabled: isAuthenticated && !user,
    retry: false,
  });

  useEffect(() => {
    if (currentUser) {
      setUser(currentUser);
    }
  }, [currentUser, setUser]);

  const loginMutation = useMutation<TokenResponse, ApiError, LoginRequest>({
    mutationFn: (credentials) => api.post<TokenResponse>("/auth/login", credentials),
    onSuccess: async (tokens) => {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);

      const me = await api.get<User>("/auth/me");
      setAuth(me, tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    },
  });

  const signupMutation = useMutation<TokenResponse, ApiError, SignupRequest>({
    mutationFn: (data) => api.post<TokenResponse>("/auth/signup", data),
    onSuccess: async (tokens) => {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);

      const me = await api.get<User>("/auth/me");
      setAuth(me, tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    },
  });

  const logout = useCallback(() => {
    clearAuth();
    queryClient.clear();
    router.push("/login");
  }, [clearAuth, queryClient, router]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    loginError: loginMutation.error,
    isLoggingIn: loginMutation.isPending,
    signup: signupMutation.mutate,
    signupAsync: signupMutation.mutateAsync,
    signupError: signupMutation.error,
    isSigningUp: signupMutation.isPending,
    logout,
  };
}
