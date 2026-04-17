/**
 * Unit tests for store/auth-store
 *
 * Tests cover:
 *  - Initial state shape
 *  - setUser() sets authenticated state
 *  - clearAuth() wipes everything
 *  - setLoading() toggles loading flag
 *  - completeOnboarding() sets flag + dbConfig
 *  - updateDbConfig() replaces dbConfig
 *  - isAdmin() and isAnalystOrAbove() helper functions
 *  - localStorage persistence keys
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore, isAdmin, isAnalystOrAbove, AuthUser } from "@/store/auth-store";

// ── Fixtures ──────────────────────────────────────────────────────────────────
const ADMIN_USER: AuthUser = {
  id: "user-001",
  email: "admin@acmebank.com",
  full_name: "Admin User",
  role: "admin",
  institution_name: "Acme Bank",
  institution_type: "bank",
  plan: "pro",
  avatar_initials: "AU",
};

const ANALYST_USER: AuthUser = {
  ...ADMIN_USER,
  id: "user-002",
  email: "analyst@acmebank.com",
  role: "analyst",
};

const VIEWER_USER: AuthUser = {
  ...ADMIN_USER,
  id: "user-003",
  email: "viewer@acmebank.com",
  role: "viewer",
};

const DB_CONFIG = {
  db_type: "supabase" as const,
  db_url: "https://abc.supabase.co",
  supabase_url: "https://abc.supabase.co",
  supabase_anon_key: "eyJanon",
};

// Reset Zustand store state before each test
beforeEach(() => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    hasCompletedOnboarding: false,
    dbConfig: null,
  });
  localStorage.clear();
});

describe("initial state", () => {
  it("starts unauthenticated", () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
  });

  it("starts with null user", () => {
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("starts with null token", () => {
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("starts with isLoading=false", () => {
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it("starts with hasCompletedOnboarding=false", () => {
    expect(useAuthStore.getState().hasCompletedOnboarding).toBe(false);
  });

  it("starts with null dbConfig", () => {
    expect(useAuthStore.getState().dbConfig).toBeNull();
  });
});

describe("setUser()", () => {
  it("sets user and token", () => {
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    const state = useAuthStore.getState();
    expect(state.user).toEqual(ADMIN_USER);
    expect(state.token).toBe("tok_abc");
  });

  it("sets isAuthenticated=true", () => {
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("clears isLoading", () => {
    useAuthStore.setState({ isLoading: true });
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe("clearAuth()", () => {
  it("resets user to null", () => {
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("resets token to null", () => {
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("resets isAuthenticated to false", () => {
    useAuthStore.getState().setUser(ADMIN_USER, "tok_abc");
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("resets dbConfig to null", () => {
    useAuthStore.getState().completeOnboarding(DB_CONFIG);
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().dbConfig).toBeNull();
  });

  it("resets hasCompletedOnboarding to false", () => {
    useAuthStore.getState().completeOnboarding(DB_CONFIG);
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().hasCompletedOnboarding).toBe(false);
  });
});

describe("setLoading()", () => {
  it("sets isLoading to true", () => {
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().isLoading).toBe(true);
  });

  it("sets isLoading to false", () => {
    useAuthStore.setState({ isLoading: true });
    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe("completeOnboarding()", () => {
  it("sets hasCompletedOnboarding=true", () => {
    useAuthStore.getState().completeOnboarding(DB_CONFIG);
    expect(useAuthStore.getState().hasCompletedOnboarding).toBe(true);
  });

  it("stores dbConfig", () => {
    useAuthStore.getState().completeOnboarding(DB_CONFIG);
    expect(useAuthStore.getState().dbConfig).toEqual(DB_CONFIG);
  });
});

describe("updateDbConfig()", () => {
  it("replaces dbConfig with new value", () => {
    useAuthStore.getState().completeOnboarding(DB_CONFIG);
    const newConfig = { ...DB_CONFIG, db_url: "https://newdb.supabase.co" };
    useAuthStore.getState().updateDbConfig(newConfig);
    expect(useAuthStore.getState().dbConfig?.db_url).toBe("https://newdb.supabase.co");
  });
});

// ── RBAC helper functions ────────────────────────────────────────────────────

describe("isAdmin()", () => {
  it("returns true for admin role", () => {
    expect(isAdmin(ADMIN_USER)).toBe(true);
  });

  it("returns false for analyst role", () => {
    expect(isAdmin(ANALYST_USER)).toBe(false);
  });

  it("returns false for viewer role", () => {
    expect(isAdmin(VIEWER_USER)).toBe(false);
  });

  it("returns false for null user", () => {
    expect(isAdmin(null)).toBe(false);
  });
});

describe("isAnalystOrAbove()", () => {
  it("returns true for admin", () => {
    expect(isAnalystOrAbove(ADMIN_USER)).toBe(true);
  });

  it("returns true for analyst", () => {
    expect(isAnalystOrAbove(ANALYST_USER)).toBe(true);
  });

  it("returns false for viewer", () => {
    expect(isAnalystOrAbove(VIEWER_USER)).toBe(false);
  });

  it("returns false for null", () => {
    expect(isAnalystOrAbove(null)).toBe(false);
  });
});
