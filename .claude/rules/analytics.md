# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:18Z)

**Source:** CLAUDE.md

# Analytics and Monitoring Rules

Apply these rules when editing dashboards, metrics, reporting, or observability features.

## Metrics computation
- Aggregate metrics in background workers, never in request handlers.
- Use materialized views or pre-computed tables for dashboard queries.
- Keep metric definitions consistent, documented, and versioned.
- Support time-range filtering and granularity selection on all endpoints.

## Key metrics
- **CSAT**: Customer satisfaction scoring with survey integration.
- **Sentiment analytics**: Aggregate sentiment trends per channel, agent, category.
- **Resolution time**: Track mean, median, p95 for resolution and first response.
- **AI vs Human**: Track resolution rates, handoff rates, and confidence distributions.
- **Agent performance**: Handle time, resolution rate, CSAT per agent (aggregate only).
- **Call quality**: Score based on audio quality, sentiment, and resolution.

## Dashboard rules
- Use WebSocket streaming for real-time dashboard updates.
- Show skeleton loaders while data loads — never empty screens.
- Support drill-down from summary metrics to individual records.
- Apply RBAC to analytics — agents see own metrics, supervisors see team, admins see all.

## Observability
- Use structured JSON logging with correlation IDs across all services.
- Monitor AI response latency, error rates, and confidence score distributions.
- Set up alerts for: SLA breaches, error rate spikes, queue backlogs, model drift.
- Track system resource usage per service for capacity planning.

## Data integrity
- Never expose individual customer data in aggregate analytics.
- Apply PII masking in all analytics pipelines.
- Keep raw event data separate from computed metrics.
- Support data export for compliance and audit requests.
