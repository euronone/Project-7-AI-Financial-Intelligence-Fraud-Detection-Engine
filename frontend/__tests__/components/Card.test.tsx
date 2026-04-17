/**
 * Unit tests for shared/Card — covers props: hoverable, glow, className, children.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Card from "@/components/shared/Card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card><p>Card content</p></Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders a <div> container", () => {
    const { container } = render(<Card>Test</Card>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("always has base bg and border classes", () => {
    const { container } = render(<Card>Test</Card>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-[#111118]");
    expect(el.className).toContain("border-[#1E1E2E]");
    expect(el.className).toContain("rounded-xl");
  });

  // ── hoverable ────────────────────────────────────────────────────────────────
  it("includes card-hover class by default (hoverable=true)", () => {
    const { container } = render(<Card>Hover</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("card-hover");
  });

  it("omits card-hover class when hoverable=false", () => {
    const { container } = render(<Card hoverable={false}>Static</Card>);
    expect((container.firstChild as HTMLElement).className).not.toContain("card-hover");
  });

  // ── glow ─────────────────────────────────────────────────────────────────────
  it("glow=none (default) adds no glow shadow", () => {
    const { container } = render(<Card>Test</Card>);
    expect((container.firstChild as HTMLElement).className).not.toContain("shadow-[");
  });

  it("glow=green adds green hover shadow", () => {
    const { container } = render(<Card glow="green">G</Card>);
    const cls = (container.firstChild as HTMLElement).className;
    expect(cls).toContain("hover:border-[#00FF87]");
  });

  it("glow=blue adds blue hover shadow", () => {
    const { container } = render(<Card glow="blue">B</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("hover:border-[#3B82F6]");
  });

  it("glow=purple adds purple hover shadow", () => {
    const { container } = render(<Card glow="purple">P</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("hover:border-[#8B5CF6]");
  });

  // ── custom className ─────────────────────────────────────────────────────────
  it("merges extra className prop", () => {
    const { container } = render(<Card className="p-8 custom">Test</Card>);
    const cls = (container.firstChild as HTMLElement).className;
    expect(cls).toContain("p-8");
    expect(cls).toContain("custom");
  });

  // ── Slot composition ─────────────────────────────────────────────────────────
  it("renders nested components", () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Body text</p>
        <button>Action</button>
      </Card>
    );
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Body text")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
  });
});
