import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    // Use jsdom for browser-like globals (window, document, localStorage)
    environment: "jsdom",
    // Run setup file before every test suite
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    // Coverage thresholds — CI will fail below these
    coverage: {
      provider: "v8",
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 55,
        statements: 60,
      },
      exclude: [
        "node_modules/**",
        "**/*.config.*",
        "**/*.d.ts",
        ".next/**",
        "e2e/**",
        "public/**",
      ],
    },
    // Match all test files under __tests__ or co-located .test.ts(x) files
    include: ["**/__tests__/**/*.{ts,tsx}", "**/*.test.{ts,tsx}"],
    exclude: ["node_modules", ".next", "e2e"],
  },
  resolve: {
    alias: {
      // Mirror the @/* path alias in tsconfig.json
      "@": path.resolve(__dirname, "."),
    },
  },
});
