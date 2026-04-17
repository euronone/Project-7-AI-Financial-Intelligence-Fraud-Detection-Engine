/**
 * Global Vitest setup — imported before every test suite.
 *
 * 1. Extends the `expect` API with @testing-library/jest-dom matchers
 *    so we can write: expect(el).toBeInTheDocument()
 * 2. Stubs browser globals that jsdom doesn't implement (matchMedia,
 *    ResizeObserver, IntersectionObserver) to avoid noise in component tests.
 * 3. Clears all mocks between tests so spy state never leaks.
 */

import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Automatically unmount React trees after each test
afterEach(() => {
  cleanup();
});

// ── Browser API stubs ────────────────────────────────────────────────────────

// next/navigation uses matchMedia in some components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Framer-motion and some layout-detecting hooks use ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Used by intersection-observer-based lazy loaders
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Zustand's `persist` middleware uses localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (i: number) => Object.keys(store)[i] ?? null,
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });
