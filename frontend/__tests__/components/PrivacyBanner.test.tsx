/**
 * Unit tests for shared/PrivacyBanner — covers all three variants and the
 * expand-on-click interaction.
 */
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PrivacyBanner from "@/components/shared/PrivacyBanner";

describe("PrivacyBanner — footer variant", () => {
  it("renders the no-save message", () => {
    render(<PrivacyBanner variant="footer" />);
    expect(screen.getByText(/don.*t save or store/i)).toBeInTheDocument();
  });

  it("renders the real-time fraud detection sub-text", () => {
    render(<PrivacyBanner variant="footer" />);
    expect(screen.getByText(/real-time fraud detection/i)).toBeInTheDocument();
  });

  it("does not show the expand button", () => {
    render(<PrivacyBanner variant="footer" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("PrivacyBanner — modal variant", () => {
  it("renders the 'Your Privacy is Protected' heading", () => {
    render(<PrivacyBanner variant="modal" />);
    expect(screen.getByText(/your privacy is protected/i)).toBeInTheDocument();
  });

  it("renders the privacy policy link", () => {
    render(<PrivacyBanner variant="modal" />);
    expect(screen.getByRole("link", { name: /privacy policy/i })).toBeInTheDocument();
  });

  it("contains the no-save message", () => {
    render(<PrivacyBanner variant="modal" />);
    expect(screen.getByText(/don.*t save or store/i)).toBeInTheDocument();
  });
});

describe("PrivacyBanner — inline variant (default)", () => {
  it("renders 'Privacy protected' when fullMessage=false (default)", () => {
    render(<PrivacyBanner />);
    expect(screen.getByText(/privacy protected/i)).toBeInTheDocument();
  });

  it("renders full message when fullMessage=true", () => {
    render(<PrivacyBanner fullMessage />);
    expect(screen.getByText(/we don.*t save your data/i)).toBeInTheDocument();
  });

  it("is clickable (has click handler region)", () => {
    const { container } = render(<PrivacyBanner />);
    // The outer motion.div has onClick — just check it exists
    const clickable = container.querySelector("[class*=cursor-pointer]");
    expect(clickable).toBeInTheDocument();
    // Should not throw on click
    fireEvent.click(clickable!);
  });

  it("contains a Lock icon (svg) by default", () => {
    const { container } = render(<PrivacyBanner />);
    const svgs = container.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThan(0);
  });
});
