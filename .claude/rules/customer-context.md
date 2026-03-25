# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Customer Context Engine Rules

Apply these rules when editing customer history, personalization, or account data features.

## Data access
- Use repository pattern for all customer data access.
- Cache frequently accessed customer profiles in Redis with TTL.
- Support lazy loading of full customer history — don't fetch everything upfront.
- Use pagination for large data sets (ticket history, purchase history).

## Context assembly
- Assemble customer context from multiple sources: profile, tickets, purchases, interactions.
- Keep context assembly in a dedicated service — never inline in handlers.
- Apply PII filtering before passing context to AI models.
- Track which context fields are used by AI and which are for agent display only.

## Personalization
- Keep personalization rules configurable per tenant/customer tier.
- Log personalization decisions for analysis and debugging.
- Support A/B testing of personalization strategies.
- Never make irrevocable actions based solely on personalization signals.

## Privacy and compliance
- Respect data access permissions — agents see only what their role allows.
- Support GDPR data export and deletion requests.
- Track all customer data access in audit logs.
- Apply data retention policies per data category.
