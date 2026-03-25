# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

# Ticketing System Rules

Apply these rules when editing ticket management, routing, SLA, or categorization features.

## Ticket lifecycle
- Enforce clear lifecycle states: `created > assigned > in_progress > resolved > closed`.
- All state transitions must be validated — no skipping states without explicit rules.
- Log every state transition with timestamp, actor, and reason.
- Support reopening resolved tickets within a configurable window.

## Auto-categorization and routing
- Auto-categorization and priority detection must always be overridable by agents.
- Log AI-assigned categories with confidence scores.
- Routing rules must be configurable via admin panel — no hardcoded routing logic.
- Support rule-based and AI-based routing as composable strategies.
- Route tickets based on: category, priority, agent skills, current load, and SLA urgency.

## SLA management
- SLA calculations must account for business hours and timezone.
- Track first response time, resolution time, and escalation time separately.
- Trigger alerts before SLA breach (warning threshold), not only after.
- Make SLA policies configurable per customer tier and ticket category.

## Duplicate detection
- Log duplicate matches with confidence scores and matched ticket IDs.
- Never auto-merge duplicates — suggest to agent and let them confirm.
- Use both content similarity and metadata matching for detection.

## Summarization
- Auto-generate ticket summaries on resolution.
- Include key actions taken, resolution method, and time spent.
- Keep summaries concise and structured for analytics consumption.
