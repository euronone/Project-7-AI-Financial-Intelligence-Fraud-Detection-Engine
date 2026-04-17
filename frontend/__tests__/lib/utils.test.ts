/**
 * Unit tests for lib/utils — cn() class-name helper.
 * The cn() function wraps clsx + tailwind-merge; tests verify
 * that conflicting Tailwind classes are correctly resolved.
 */
import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

describe("cn() — class name utility", () => {
  it("returns a plain class string", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("ignores falsy values", () => {
    expect(cn("foo", false, null, undefined, "bar")).toBe("foo bar");
  });

  it("deduplicates conflicting Tailwind padding classes (last wins)", () => {
    const result = cn("p-4", "p-8");
    expect(result).toBe("p-8");
    expect(result).not.toContain("p-4");
  });

  it("deduplicates conflicting bg colours", () => {
    const result = cn("bg-red-500", "bg-blue-500");
    expect(result).toBe("bg-blue-500");
    expect(result).not.toContain("bg-red-500");
  });

  it("merges non-conflicting classes", () => {
    const result = cn("text-white", "font-bold", "p-4");
    expect(result).toContain("text-white");
    expect(result).toContain("font-bold");
    expect(result).toContain("p-4");
  });

  it("handles conditional objects from clsx", () => {
    const result = cn({ "text-red-500": true, "text-green-500": false });
    expect(result).toContain("text-red-500");
    expect(result).not.toContain("text-green-500");
  });

  it("handles array of classes", () => {
    expect(cn(["foo", "bar", "baz"])).toBe("foo bar baz");
  });

  it("returns empty string for no arguments", () => {
    expect(cn()).toBe("");
  });

  it("returns empty string for all falsy arguments", () => {
    expect(cn(false, null, undefined)).toBe("");
  });

  it("handles FinShield custom colour classes without stripping them", () => {
    const result = cn("bg-[#0A0A0F]", "text-[#00FF87]", "border-[#1E1E2E]");
    expect(result).toContain("bg-[#0A0A0F]");
    expect(result).toContain("text-[#00FF87]");
    expect(result).toContain("border-[#1E1E2E]");
  });
});
