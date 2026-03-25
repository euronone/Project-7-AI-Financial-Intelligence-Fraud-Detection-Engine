# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Automation Rules

Apply these rules when editing auto-reply, auto-escalation, workflow automation, or SLA alerting features.

## Auto-reply
- Auto-replies must be clearly labeled as AI-generated.
- Apply confidence thresholds — only auto-reply when confidence is high.
- Make auto-reply rules configurable per channel and ticket category.
- Track auto-reply resolution rates and customer satisfaction.
- Support opt-out: customers can request human-only support.

## Auto-escalation
- Define escalation triggers: sentiment drop, repeated contact, SLA risk, explicit request.
- Log escalation reason, source signal, and destination.
- Allow supervisors to configure escalation rules without code changes.
- Never auto-escalate silently — notify both the agent and the supervisor.

## Workflow automation
- Use a declarative workflow engine — avoid hardcoded if/else chains.
- Keep workflow definitions inspectable and versionable.
- Support conditional branching, parallel steps, and human-in-the-loop gates.
- Log every workflow execution with step-by-step status.

## Auto-closing
- Auto-close only after a configurable inactivity period.
- Send a warning message before auto-closing.
- Allow customers to reopen auto-closed tickets within a grace period.
- Track auto-close rates and reopen rates for tuning.

## SLA alerts
- Trigger warnings before breach, not only after.
- Support multiple notification channels: in-app, email, Slack.
- Make alert thresholds configurable per SLA policy.
- Deduplicate alerts — never spam the same alert repeatedly.
