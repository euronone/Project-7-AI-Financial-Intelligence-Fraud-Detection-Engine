/**
 * E2E tests for the Landing Page (public, unauthenticated)
 *
 * Covers:
 *  - Page loads and all ribbon sections are visible
 *  - Project Guide section exists
 *  - Subscription plans cards are visible
 *  - CTA buttons navigate to signup/login
 *  - Navigation links work
 *  - Accessibility: page title and lang attribute
 */
import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  // ── Page meta ──────────────────────────────────────────────────────────────
  test("has a page title containing FinShield", async ({ page }) => {
    await expect(page).toHaveTitle(/finshield/i);
  });

  test("html lang attribute is set", async ({ page }) => {
    const lang = await page.getAttribute("html", "lang");
    expect(lang).toBeTruthy();
  });

  // ── Hero section ───────────────────────────────────────────────────────────
  test("hero headline mentions FinShield", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /finshield/i }).first()).toBeVisible();
  });

  test("Get Started CTA button is visible", async ({ page }) => {
    const cta = page
      .getByRole("link", { name: /get started/i })
      .or(page.getByRole("button", { name: /get started/i }))
      .first();
    await expect(cta).toBeVisible();
  });

  test("View Demo CTA button is visible", async ({ page }) => {
    const demo = page
      .getByRole("link", { name: /demo/i })
      .or(page.getByRole("button", { name: /demo/i }))
      .first();
    await expect(demo).toBeVisible({ timeout: 10_000 });
  });

  // ── Project Guide section ──────────────────────────────────────────────────
  test("Project Guide section is present", async ({ page }) => {
    const guide = page
      .getByText(/what is finshield/i)
      .or(page.getByText(/project guide/i))
      .first();
    await expect(guide).toBeVisible({ timeout: 10_000 });
  });

  test("Project Guide explains who it is for", async ({ page }) => {
    const whoText = page.getByText(/who is it for/i).or(page.getByText(/banks.*fintech/i)).first();
    await expect(whoText).toBeVisible({ timeout: 10_000 });
  });

  // ── Features section ───────────────────────────────────────────────────────
  test("features section mentions real-time detection", async ({ page }) => {
    await expect(page.getByText(/real.?time/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test("features section mentions ML", async ({ page }) => {
    await expect(page.getByText(/ml|machine learning/i).first()).toBeVisible({
      timeout: 10_000,
    });
  });

  // ── Pricing section ────────────────────────────────────────────────────────
  test("pricing section shows Free plan", async ({ page }) => {
    await expect(page.getByText(/free/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test("pricing section shows Pro plan", async ({ page }) => {
    await expect(page.getByText(/pro/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test("pricing section shows Advanced plan", async ({ page }) => {
    await expect(page.getByText(/advanced/i).first()).toBeVisible({ timeout: 10_000 });
  });

  // ── Navigation ─────────────────────────────────────────────────────────────
  test("Get Started button navigates to signup page", async ({ page }) => {
    const cta = page
      .getByRole("link", { name: /get started/i })
      .or(page.getByRole("button", { name: /get started/i }))
      .first();
    await cta.click();
    // Either the URL changes or a signup form appears
    await page.waitForTimeout(500);
    const isSignupPage =
      page.url().includes("signup") ||
      (await page.getByRole("heading", { name: /sign.?up|create.?account/i }).isVisible({ timeout: 5000 }).catch(() => false));
    expect(isSignupPage).toBe(true);
  });

  test("Login link navigates to login page", async ({ page }) => {
    const loginLink = page
      .getByRole("link", { name: /log.?in|sign.?in/i })
      .first();
    await loginLink.click();
    await page.waitForTimeout(500);
    const isLoginPage =
      page.url().includes("login") ||
      (await page.getByRole("heading", { name: /sign.?in|log.?in|welcome/i }).isVisible({ timeout: 5000 }).catch(() => false));
    expect(isLoginPage).toBe(true);
  });
});
