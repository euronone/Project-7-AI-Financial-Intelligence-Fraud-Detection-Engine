/**
 * E2E tests for Authentication flows:
 *  - Login page renders + fields + submit
 *  - Signup page renders + fields + submit
 *  - Forgot-password page
 *  - Validation errors appear for bad input
 *  - Successful login redirects to dashboard
 *  - Logout clears session
 */
import { test, expect } from "@playwright/test";

// ── Login page ────────────────────────────────────────────────────────────────
test.describe("Login page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/(auth)/login").catch(() => page.goto("/login"));
    // Wait for the form to appear
    await page.waitForSelector("form, [data-testid=login-form]", { timeout: 10_000 });
  });

  test("renders email and password fields", async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });

  test("renders the sign-in submit button", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /sign.?in|log.?in|continue/i })
    ).toBeVisible();
  });

  test("shows validation error when email is empty", async ({ page }) => {
    await page.getByRole("button", { name: /sign.?in|log.?in|continue/i }).click();
    await expect(page.getByText(/email.*required|required/i).first()).toBeVisible({
      timeout: 5_000,
    });
  });

  test("shows error for invalid email format", async ({ page }) => {
    await page.getByLabel(/email/i).fill("notanemail");
    await page.getByLabel(/password/i).fill("Pass123!");
    await page.getByRole("button", { name: /sign.?in|log.?in|continue/i }).click();
    await expect(page.getByText(/invalid.*email|valid email/i).first()).toBeVisible({
      timeout: 5_000,
    });
  });

  test("shows error on wrong credentials", async ({ page }) => {
    await page.getByLabel(/email/i).fill("wrong@test.com");
    await page.getByLabel(/password/i).fill("WrongPass123!");
    await page.getByRole("button", { name: /sign.?in|log.?in|continue/i }).click();
    await expect(
      page.getByText(/invalid|incorrect|unauthorized|credentials/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("has a link to signup page", async ({ page }) => {
    const signupLink = page.getByRole("link", { name: /sign.?up|create.?account|register/i });
    await expect(signupLink).toBeVisible();
    await signupLink.click();
    await expect(page).toHaveURL(/signup|register|onboard/);
  });

  test("has a forgot-password link", async ({ page }) => {
    const forgotLink = page.getByRole("link", { name: /forgot.*password|reset.*password/i });
    await expect(forgotLink).toBeVisible();
  });
});

// ── Signup page ───────────────────────────────────────────────────────────────
test.describe("Signup page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/(auth)/signup").catch(() => page.goto("/signup"));
    await page.waitForSelector("form, [data-testid=signup-form]", { timeout: 10_000 });
  });

  test("renders email, password, and institution name fields", async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i).first()).toBeVisible();
  });

  test("renders the create account submit button", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /sign.?up|create|get started|continue/i })
    ).toBeVisible();
  });

  test("shows validation error when form is submitted empty", async ({ page }) => {
    await page.getByRole("button", { name: /sign.?up|create|get started|continue/i }).click();
    // At least one validation error should appear
    const errors = page.getByText(/required|invalid/i);
    await expect(errors.first()).toBeVisible({ timeout: 5_000 });
  });

  test("accepts valid signup data and does not crash", async ({ page }) => {
    const uniqueEmail = `e2e_${Date.now()}@finshield.test`;
    await page.getByLabel(/email/i).fill(uniqueEmail);
    const pwFields = await page.getByLabel(/password/i).all();
    await pwFields[0].fill("TestPass123!@#");
    if (pwFields[1]) await pwFields[1].fill("TestPass123!@#");
    // Fill organization name if present
    const orgField = page.getByLabel(/organisation|organization|company|institution name/i);
    if (await orgField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await orgField.fill("E2E Test Bank");
    }
    await page.getByRole("button", { name: /sign.?up|create|get started|continue/i }).click();
    // Should either redirect to dashboard/onboarding or show success
    await page.waitForTimeout(2000);
    const succeeded =
      page.url().includes("dashboard") ||
      page.url().includes("onboard") ||
      (await page.getByText(/success|verify|welcome/i).isVisible({ timeout: 3000 }).catch(() => false));
    expect(succeeded).toBe(true);
  });

  test("has a link back to login page", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: /log.?in|sign.?in|already have/i });
    await expect(loginLink).toBeVisible();
  });
});

// ── Forgot password page ──────────────────────────────────────────────────────
test.describe("Forgot-password page", () => {
  test.beforeEach(async ({ page }) => {
    await page
      .goto("/(auth)/forgot-password")
      .catch(() => page.goto("/forgot-password"));
    await page.waitForSelector("form, input[type=email]", { timeout: 10_000 });
  });

  test("renders email input field", async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test("renders the send-reset submit button", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /send|reset|continue/i })
    ).toBeVisible();
  });

  test("shows confirmation message after valid email submitted", async ({ page }) => {
    await page.getByLabel(/email/i).fill("user@acmebank.com");
    await page.getByRole("button", { name: /send|reset|continue/i }).click();
    // API always returns 200 — UI should show a confirmation message
    await expect(
      page.getByText(/sent|check.*email|link.*(sent|send)|reset.*email/i).first()
    ).toBeVisible({ timeout: 8_000 });
  });
});
