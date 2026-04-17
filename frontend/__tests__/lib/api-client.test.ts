/**
 * Unit tests for lib/api-client
 *
 * Uses vi.stubGlobal to mock fetch, so no real network calls are made.
 * Tests verify that:
 *  - Correct HTTP methods are used
 *  - Authorization header is attached when token is provided
 *  - Errors are thrown with the detail message from the API
 *  - Response data is returned correctly
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, isBackendAvailable } from "@/lib/api-client";

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockFetch(body: object, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    statusText: status === 200 ? "OK" : "Error",
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch({ status: "ok" }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ── Health ────────────────────────────────────────────────────────────────────

describe("apiClient.health()", () => {
  it("calls the /health endpoint via GET", async () => {
    const fakeFetch = mockFetch({ status: "ok" });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.health();
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/health");
    expect(opts?.method).toBeUndefined(); // default is GET
  });

  it("returns the response body", async () => {
    vi.stubGlobal("fetch", mockFetch({ status: "healthy" }));
    const result = await apiClient.health();
    expect(result).toEqual({ status: "healthy" });
  });
});

// ── isBackendAvailable ────────────────────────────────────────────────────────

describe("isBackendAvailable()", () => {
  it("returns true when health check succeeds", async () => {
    vi.stubGlobal("fetch", mockFetch({ status: "ok" }));
    expect(await isBackendAvailable()).toBe(true);
  });

  it("returns false when health check throws", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    expect(await isBackendAvailable()).toBe(false);
  });

  it("returns false when API returns 500", async () => {
    vi.stubGlobal("fetch", mockFetch({ detail: "Server error" }, 500));
    expect(await isBackendAvailable()).toBe(false);
  });
});

// ── Auth ──────────────────────────────────────────────────────────────────────

describe("apiClient.login()", () => {
  it("sends POST with email and password", async () => {
    const fakeFetch = mockFetch({ access_token: "tok", refresh_token: "ref", user: {} });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.login("user@test.com", "Pass123!");
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/auth/login");
    expect(opts.method).toBe("POST");
    const body = JSON.parse(opts.body as string);
    expect(body.email).toBe("user@test.com");
    expect(body.password).toBe("Pass123!");
  });

  it("does NOT set Authorization header (no token at login)", async () => {
    const fakeFetch = mockFetch({ access_token: "tok", refresh_token: "ref", user: {} });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.login("user@test.com", "Pass123!");
    const [, opts] = fakeFetch.mock.calls[0];
    expect((opts.headers as Record<string, string>)?.Authorization).toBeUndefined();
  });

  it("throws with the API detail message on 401", async () => {
    vi.stubGlobal("fetch", mockFetch({ detail: "Invalid credentials" }, 401));
    await expect(apiClient.login("bad@test.com", "wrong")).rejects.toThrow("Invalid credentials");
  });
});

describe("apiClient.signup()", () => {
  it("sends POST to /auth/signup", async () => {
    const fakeFetch = mockFetch({ access_token: "tok", refresh_token: "ref", user: {} });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.signup({ email: "new@test.com", password: "Pass123!" });
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/auth/signup");
    expect(opts.method).toBe("POST");
  });
});

describe("apiClient.getMe()", () => {
  it("attaches Authorization header with token", async () => {
    const fakeFetch = mockFetch({ id: "user-1", email: "user@test.com" });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.getMe("my-token");
    const [, opts] = fakeFetch.mock.calls[0];
    expect((opts.headers as Record<string, string>).Authorization).toBe("Bearer my-token");
  });

  it("sends GET to /auth/me", async () => {
    const fakeFetch = mockFetch({ id: "user-1" });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.getMe("tok");
    const [url] = fakeFetch.mock.calls[0];
    expect(url).toContain("/auth/me");
  });
});

// ── Analytics ────────────────────────────────────────────────────────────────

describe("apiClient.getOverview()", () => {
  it("calls /analytics/overview with token", async () => {
    const fakeFetch = mockFetch({ transactions_today: 42, fraud_count: 2 });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.getOverview("my-token");
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/analytics/overview");
    expect((opts.headers as Record<string, string>).Authorization).toBe("Bearer my-token");
  });

  it("returns the overview payload", async () => {
    const payload = { transactions_today: 100, fraud_count: 5, fraud_rate_percent: 5.0 };
    vi.stubGlobal("fetch", mockFetch(payload));
    const result = await apiClient.getOverview("tok");
    expect(result).toMatchObject(payload);
  });
});

// ── Transactions ──────────────────────────────────────────────────────────────

describe("apiClient.getTransactions()", () => {
  it("calls /transactions without params", async () => {
    const fakeFetch = mockFetch({ items: [], total: 0 });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.getTransactions("tok");
    const [url] = fakeFetch.mock.calls[0];
    expect(url).toContain("/transactions");
    expect(url).not.toContain("?");
  });

  it("appends query params", async () => {
    const fakeFetch = mockFetch({ items: [], total: 0 });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.getTransactions("tok", { fraud_category: "fraudulent", limit: "10" });
    const [url] = fakeFetch.mock.calls[0];
    expect(url).toContain("fraud_category=fraudulent");
    expect(url).toContain("limit=10");
  });
});

describe("apiClient.createTransaction()", () => {
  it("sends POST to /transactions", async () => {
    const fakeFetch = mockFetch({ id: "txn-001", fraud_score: 0.05 });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.createTransaction({ amount: 500 }, "tok");
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/transactions");
    expect(opts.method).toBe("POST");
  });
});

// ── Simulator ────────────────────────────────────────────────────────────────

describe("apiClient.simulatorPredict()", () => {
  it("sends POST to /simulator/predict", async () => {
    const fakeFetch = mockFetch({ fraud_score: 0.91, risk_level: "critical" });
    vi.stubGlobal("fetch", fakeFetch);
    await apiClient.simulatorPredict({ amount: 50000 }, "tok");
    const [url, opts] = fakeFetch.mock.calls[0];
    expect(url).toContain("/simulator/predict");
    expect(opts.method).toBe("POST");
  });
});

// ── Error handling ────────────────────────────────────────────────────────────

describe("error handling", () => {
  it("throws with detail message from 4xx API response", async () => {
    vi.stubGlobal("fetch", mockFetch({ detail: "Not found" }, 404));
    await expect(apiClient.getAlerts("tok")).rejects.toThrow("Not found");
  });

  it("throws with HTTP status text when no detail present", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      json: async () => ({}),
    }));
    await expect(apiClient.health()).rejects.toThrow("Service Unavailable");
  });
});
