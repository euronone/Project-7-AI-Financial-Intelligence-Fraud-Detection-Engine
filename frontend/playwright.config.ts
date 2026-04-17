import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for FinShield AI frontend.
 *
 * - Runs against the Next.js dev server on port 3000
 * - Assumes the FastAPI backend is up on port 8003 (started separately in CI)
 * - Uses Chromium only by default; add firefox/webkit in full regression runs
 * - globalSetup creates a saved auth state so dashboard tests skip re-login
 */

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // serialise to avoid port conflicts on CI
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  timeout: 30_000,

  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["junit", { outputFile: "test-results/e2e-junit.xml" }],
  ],

  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    // Force a small viewport matching the FinShield dark-theme designs
    viewport: { width: 1280, height: 800 },
  },

  projects: [
    // ── Setup: create a reusable auth session ──────────────────────────────
    {
      name: "setup",
      testMatch: /e2e\/auth\.setup\.ts/,
    },
    // ── Unauthenticated tests (landing, auth pages) ────────────────────────
    {
      name: "public",
      testMatch: /e2e\/(landing|auth)\.spec\.ts/,
    },
    // ── Authenticated tests — depends on setup ─────────────────────────────
    {
      name: "dashboard",
      testMatch: /e2e\/dashboard.*\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/user.json",
      },
    },
  ],

  // Start Next.js before tests; reuse if already running
  webServer: {
    command: "npm run dev",
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
