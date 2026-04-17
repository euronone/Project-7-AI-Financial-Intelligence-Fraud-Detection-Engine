/**
 * Unit tests for shared/Button — covers every variant, size, state, and click.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Button from "@/components/shared/Button";

describe("Button", () => {
  // ── Rendering ───────────────────────────────────────────────────────────────
  it("renders children text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("renders as a <button> element", () => {
    render(<Button>Test</Button>);
    expect(screen.getByRole("button")).toBeInstanceOf(HTMLButtonElement);
  });

  // ── Variants ────────────────────────────────────────────────────────────────
  it.each(["primary", "secondary", "ghost", "outline"] as const)(
    "applies %s variant without error",
    (variant) => {
      render(<Button variant={variant}>Btn</Button>);
      expect(screen.getByRole("button")).toBeInTheDocument();
    }
  );

  it("defaults to primary variant (green background)", () => {
    render(<Button>Go</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-[#00FF87]");
  });

  it("secondary variant has blue background", () => {
    render(<Button variant="secondary">Go</Button>);
    expect(screen.getByRole("button").className).toContain("bg-[#3B82F6]");
  });

  it("outline variant has border class", () => {
    render(<Button variant="outline">Go</Button>);
    expect(screen.getByRole("button").className).toContain("border");
  });

  // ── Sizes ───────────────────────────────────────────────────────────────────
  it.each(["sm", "md", "lg"] as const)("renders size=%s without error", (size) => {
    render(<Button size={size}>Btn</Button>);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("lg size includes font-bold class", () => {
    render(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button").className).toContain("font-bold");
  });

  // ── Loading state ────────────────────────────────────────────────────────────
  it("shows 'Loading...' text when isLoading=true", () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("hides original children text when loading", () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.queryByText("Submit")).not.toBeInTheDocument();
  });

  it("is disabled when isLoading=true", () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Submit</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("renders spinner icon when loading (animate-spin class)", () => {
    const { container } = render(<Button isLoading>Submit</Button>);
    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  // ── Icon prop ────────────────────────────────────────────────────────────────
  it("renders icon when not loading", () => {
    const icon = <span data-testid="custom-icon">★</span>;
    render(<Button icon={icon}>Action</Button>);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });

  it("hides icon when loading", () => {
    const icon = <span data-testid="custom-icon">★</span>;
    render(<Button icon={icon} isLoading>Action</Button>);
    expect(screen.queryByTestId("custom-icon")).not.toBeInTheDocument();
  });

  // ── Click interactions ───────────────────────────────────────────────────────
  it("calls onClick handler when clicked", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does NOT fire onClick when disabled", () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("does NOT fire onClick when isLoading", () => {
    const handleClick = vi.fn();
    render(<Button isLoading onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).not.toHaveBeenCalled();
  });

  // ── Extra className forwarding ───────────────────────────────────────────────
  it("forwards extra className to the button element", () => {
    render(<Button className="extra-test-class">Btn</Button>);
    expect(screen.getByRole("button").className).toContain("extra-test-class");
  });

  // ── HTML attribute passthrough ───────────────────────────────────────────────
  it("forwards aria-label attribute", () => {
    render(<Button aria-label="close dialog">×</Button>);
    expect(screen.getByRole("button", { name: "close dialog" })).toBeInTheDocument();
  });

  it("forwards type=submit", () => {
    render(<Button type="submit">Submit</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit");
  });
});
