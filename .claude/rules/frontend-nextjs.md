# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Frontend Next.js Rules - FinShield AI

Apply these rules when editing Next.js and TypeScript files.

## Architecture
- Use Next.js 14 App Router with strict TypeScript.
- Keep presentational and data-fetching separate.
- Avoid oversized pages; split into focused components.
- Reuse shared UI primitives.
- Keep API calls centralized.
- Follow dark theme: #0A0A0F background, #111118 cards.

## Landing Page
- Implement 10 ribbon sections.
- Use gradient animations for hero.
- Include Project Guide section.
- Show subscription plans: Free/Pro/Advanced.
- Display 6-layer architecture diagram.
- Include 5 fraud signal categories.
- Add security/compliance section.

## Dashboard
- Use WebSocket hooks for live streams.
- Handle WebSocket reconnection.
- Show real-time fraud score updates.
- Display live KPI cards.
- Implement transaction feed with risk levels.
- Add alert queue with severity sorting.

## States
- Add loading, empty, error states.
- Show skeleton loaders.
- Add optimistic updates.
- Handle offline/reconnection.
- Implement smooth transitions.

## Test Me Tab
- Create transaction journey simulator.
- Include customer lookup.
- Show step-by-step results.
- Display SHAP explanation.
- Add test scenarios.
- Allow custom data testing.

## Settings
- Build dynamic settings page.
- Support optional integrations.
- Include connection testing.
- Show configuration status.
- Allow custom schema mapping.

## Authentication
- Implement JWT-based auth.
- Show institution-specific data.
- Support demo accounts.
- Include role-based access.
- Display institution branding.

## ML Integration
- Display model performance.
- Show feature importance charts.
- Include model version history.
- Allow manual retraining.
- Display drift detection.

## Performance
- Optimize for 60fps animations.
- Ensure WCAG AA compliance.
- Implement responsive design.
- Use lazy loading.
- Minimize bundle size.

## Security
- Never expose sensitive data.
- Use environment variables.
- Implement proper error handling.
- Follow security best practices.
- Display compliance badges.
