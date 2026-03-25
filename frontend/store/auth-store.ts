"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserRole = "admin" | "analyst" | "viewer";
export type SubscriptionPlan = "free" | "pro" | "advanced";
export type DbType = "supabase" | "postgresql" | "mysql" | "mongodb" | "rest_api";

export interface DbConfig {
  db_type: DbType;
  db_url: string;
  db_name?: string;
  db_user?: string;
  db_password?: string;
  api_key?: string;
  // Supabase-specific
  supabase_url?: string;
  supabase_anon_key?: string;
  supabase_service_key?: string;
  // Labels
  label?: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution_name: string;
  institution_type: string;
  plan: SubscriptionPlan;
  avatar_initials: string;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasCompletedOnboarding: boolean;
  dbConfig: DbConfig | null;
  setUser: (user: AuthUser, token: string) => void;
  clearAuth: () => void;
  setLoading: (v: boolean) => void;
  completeOnboarding: (config: DbConfig) => void;
  updateDbConfig: (config: DbConfig) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      hasCompletedOnboarding: false,
      dbConfig: null,
      setUser: (user, token) =>
        set({ user, token, isAuthenticated: true, isLoading: false }),
      clearAuth: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          hasCompletedOnboarding: false,
          dbConfig: null,
        }),
      setLoading: (v) => set({ isLoading: v }),
      completeOnboarding: (config) =>
        set({ hasCompletedOnboarding: true, dbConfig: config }),
      updateDbConfig: (config) => set({ dbConfig: config }),
    }),
    {
      name: "finshield-auth",
      partialize: (s) => ({
        user: s.user,
        token: s.token,
        isAuthenticated: s.isAuthenticated,
        hasCompletedOnboarding: s.hasCompletedOnboarding,
        dbConfig: s.dbConfig,
      }),
    }
  )
);
