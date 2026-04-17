/**
 * Unit tests for shared/Badge — covers variants, sizes, text, and custom className.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Badge from "@/components/shared/Badge";

describe("Badge", () => {
  // ── Rendering ────────────────────────────────────────────────────────────────
  it("renders children text", () => {
    render(<Badge>FRAUD</Badge>);
    expect(screen.getByText("FRAUD")).toBeInTheDocument();
  });

  it("renders as an inline element", () => {
    render(<Badge>Test</Badge>);
    const el = screen.getByText("Test");
    expect(el.tagName).toBe("SPAN");
  });

  // ── Variants ─────────────────────────────────────────────────────────────────
  it.each(["success", "warning", "danger", "info", "neutral"] as const)(
    "renders %s variant without error",
    (variant) => {
      render(<Badge variant={variant}>Label</Badge>);
      expect(screen.getByText("Label")).toBeInTheDocument();
    }
  );

  it("success variant has green colour class", () => {
    render(<Badge variant="success">OK</Badge>);
    expect(screen.getByText("OK").className).toContain("text-[#00FF87]");
  });

  it("danger variant has red colour class", () => {
    render(<Badge variant="danger">ERR</Badge>);
    expect(screen.getByText("ERR").className).toContain("text-[#EF4444]");
  });

  it("warning variant has amber colour class", () => {
    render(<Badge variant="warning">WARN</Badge>);
    expect(screen.getByText("WARN").className).toContain("text-[#F59E0B]");
  });

  it("info variant has blue colour class", () => {
    render(<Badge variant="info">INFO</Badge>);
    expect(screen.getByText("INFO").className).toContain("text-[#3B82F6]");
  });

  it("defaults to neutral variant", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default").className).toContain("text-[#9CA3AF]");
  });

  // ── Sizes ─────────────────────────────────────────────────────────────────────
  it.each(["sm", "md"] as const)("renders size=%s without error", (size) => {
    render(<Badge size={size}>Sized</Badge>);
    expect(screen.getByText("Sized")).toBeInTheDocument();
  });

  it("sm size has smaller padding class", () => {
    render(<Badge size="sm">S</Badge>);
    expect(screen.getByText("S").className).toContain("px-2");
  });

  it("md size has larger padding class", () => {
    render(<Badge size="md">M</Badge>);
    expect(screen.getByText("M").className).toContain("px-3");
  });

  // ── Custom className ──────────────────────────────────────────────────────────
  it("applies extra className", () => {
    render(<Badge className="extra-badge">Ext</Badge>);
    expect(screen.getByText("Ext").className).toContain("extra-badge");
  });

  // ── Fraud-domain specific usage ───────────────────────────────────────────────
  it("renders fraud risk labels correctly", () => {
    const risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
    const variants = ["danger", "danger", "warning", "success"] as const;
    risks.forEach((label, i) => {
      const { unmount } = render(<Badge variant={variants[i]}>{label}</Badge>);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    });
  });
});
