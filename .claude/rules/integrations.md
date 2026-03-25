# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Integration Rules

Apply these rules when editing CRM, helpdesk, messaging, or third-party service integrations.

## Architecture
- All integrations must use the adapter/gateway pattern.
- Define a common interface per integration category (CRM, helpdesk, messaging).
- Never hardcode external API endpoints or credentials.
- Keep integration credentials in a secrets manager.

## Resilience
- Add circuit breakers for all external API calls.
- Implement retry logic with exponential backoff and jitter.
- Set explicit timeouts on all outbound requests.
- Queue outbound operations when the external service is unavailable.
- Log all outbound API calls with status, latency, and error details.

## Specific integrations
- **CRM (Salesforce, HubSpot)**: Sync customer data bidirectionally; handle field mapping explicitly.
- **Helpdesk (Zendesk)**: Map ticket states to internal lifecycle; handle webhook events.
- **Project management (Jira)**: Create issues from escalated tickets; sync status updates.
- **Messaging (Slack, Teams)**: Use proper bot scoping; handle rate limits per workspace.
- **Payment systems**: Never log payment details; use tokenized references only.
- **ERP**: Read-only access by default; write access requires explicit configuration.

## Webhook handling
- Validate webhook signatures on all inbound webhooks.
- Idempotently process webhook events — handle duplicates gracefully.
- Log webhook processing with event type, source, and outcome.
- Use dead-letter queues for failed webhook processing.

## Testing
- Mock all external APIs in tests — never call real services in CI.
- Add contract tests for critical integration points.
- Test error scenarios: timeouts, rate limits, auth failures, malformed responses.
