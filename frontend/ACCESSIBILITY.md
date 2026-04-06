# Frontend Accessibility Guide - FinShield AI

> **WCAG 2.1 AA Compliance Target**
> This document outlines accessibility standards and best practices for all frontend code.

## 🎯 Accessibility Standards

### WCAG 2.1 Level AA Compliance
- **Perceivable**: Information and user interface components are perceivable
- **Operable**: Interface components and navigation are operable
- **Understandable**: Information and operation are understandable
- **Robust**: Content is compatible with assistive technologies

## 🔍 Implemented Accessibility Features

### 1. Semantic HTML
- Use proper heading hierarchy (h1 → h6)
- Use semantic elements: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`
- Use `<button>` for buttons, `<a>` for links (never use `<div>` for interactive elements)
- Use `<form>`, `<label>`, `<input>` properly grouped

### 2. ARIA Attributes
- Add `aria-label` to icon-only buttons
- Add `aria-describedby` for complex instructions
- Add `aria-live="polite"` to status messages
- Add `aria-busy="true"` during loading states
- Add `role="alert"` to error messages

### 3. Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order should be logical (use `tabIndex` only when necessary)
- Focus styles must be visible (minimum 2px border or outline)
- Escape key should close modals/dropdowns

### 4. Color Contrast
- Text contrast ratio minimum 4.5:1 for normal text
- Text contrast ratio minimum 3:1 for large text (18pt+)
- Don't rely on color alone to convey information
- Test with WCAG Contrast Checker or similar tool

### 5. Form Accessibility
- Every input must have an associated label
- Required fields should be marked with `aria-required="true"`
- Error messages should be linked with `aria-describedby`
- Help text should be associated with inputs

### 6. Images and Icons
- All images must have descriptive `alt` text
- Icon-only buttons must have `aria-label`
- Decorative images use `alt=""`
- Use `title` attribute for additional context

### 7. Motion & Animations
- Respect `prefers-reduced-motion` media query
- Don't auto-play animations longer than 5 seconds
- Provide controls to pause/stop animations
- Avoid flashing content (>3 flashes/sec)

### 8. Language
- Set `lang` attribute on `<html>` element
- Mark language changes with `lang` attribute

## 📋 Checklist for New Components

Before submitting a component, verify:

- [ ] Uses semantic HTML elements
- [ ] All interactive elements are keyboard accessible
- [ ] Focus styles are visible
- [ ] Text contrast passes WCAG AA (4.5:1)
- [ ] Images have descriptive alt text
- [ ] Form inputs have labels
- [ ] Error messages are announced
- [ ] Loading states use aria-busy
- [ ] Icons have aria-labels (if icon-only)
- [ ] Mobile friendly (touch targets ≥44px)

## 🧪 Testing Tools

### Automated Testing
- **axe DevTools**: Chrome/Firefox browser extension
- **Lighthouse**: Built into Chrome DevTools
- **WAVE**: Web accessibility evaluation tool
- **WebAIM Contrast Checker**: Check color contrast

### Manual Testing
- Keyboard-only navigation (no mouse)
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Font size increase to 200%
- Zoom to 200%
- Disable CSS and check readability

### Testing Commands
```bash
# Install axe testing library
npm install --save-dev @axe-core/react

# Run axe checks in tests
import { axe, toHaveNoViolations } from 'jest-axe'
expect(await axe(container)).toHaveNoViolations()
```

## 🎨 Dark Theme Accessibility Notes

For our dark theme (#0A0A0F background):
- Primary text: White (#FFFFFF)
- Secondary text: Gray (#9CA3AF)
- Accent colors must still meet 4.5:1 contrast
- Green (#00FF87): Excellent contrast on dark background
- Blue (#3B82F6): Good contrast on dark background
- Red (#EF4444): Good contrast on dark background

## 📱 Mobile Accessibility

- Touch targets minimum 44×44 pixels
- Use tap-friendly spacing (minimum 8px gaps)
- Support zoom up to 200%
- Ensure scroll direction matches expectation
- Test with screen reader (TalkBack, VoiceOver)

## 🔗 Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [Web Accessibility by Google](https://www.udacity.com/course/web-accessibility--ud891)
- [Deque University](https://dequeuniversity.com/)

## 🚀 Continuous Improvement

- Run accessibility audits on every build
- Fix Level A/AA violations before merge
- Level AAA compliance for critical paths
- Document accessibility decisions
- Train team on accessibility best practices
