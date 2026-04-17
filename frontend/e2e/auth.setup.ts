/**
 * Playwright global-setup: creates a saved authentication state (cookies +
 * localStorage) that dashboard tests consume via storageState.
 *
 * Requires a seeded test user to exist in the backend DB.
 * In CI the backend conftest.py seeds: analyst@finshield.test / TestPass123!@#
 */
import { test as setup, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const AUTH_FILE = path.join(__dirname, ".auth", "user.json");

setup("authenticate", async ({ page }) => {
  // Ensure .auth directory exists
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // Navigate to login page
  await page.goto("/");

  // If already on the landing page look for the login link
  const loginLink = page.getByRole("link", { name: /log.?in|sign.?in/i }).first();
  if (await loginLink.isVisible({ timeout: 5000 }).catch(() => false)) {
    await loginLink.click();
  } else {
    await page.goto("/(auth)/login");
  }

  // Wait for the login form
  await page.waitForURL(/login/);
  await expect(page.getByRole("heading", { name: /sign.?in|log.?in|welcome/i })).toBeVisible({
    timeout: 10_000,
  });

  // Fill credentials
  await page.getByLabel(/email/i).fill("analyst@finshield.test");
  await page.getByLabel(/password/i).fill("TestPass123!@#");
  await page.getByRole("button", { name: /sign.?in|log.?in|continue/i }).click();

  // Wait until redirected to dashboard
  await page.waitForURL(/dashboard/, { timeout: 15_000 });

  // Save authentication state
  await page.context().storageState({ path: AUTH_FILE });
});
