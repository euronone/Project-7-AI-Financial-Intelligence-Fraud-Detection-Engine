---
name: create-ticket-workflow
description: Create or extend a ticket automation workflow (routing, escalation, SLA, auto-close)
---

# Create Ticket Workflow Skill

## Goal
Build or extend a ticket automation workflow within the smart ticketing system.

## Steps
1. Ask for: workflow type (routing rule, escalation trigger, SLA policy, auto-close rule, categorization), trigger conditions, and actions.
2. Define the workflow as a declarative configuration:
   - Trigger conditions (ticket created, SLA approaching, sentiment drop, etc.)
   - Evaluation logic (rule-based, AI-based, or hybrid)
   - Actions (route, escalate, notify, categorize, close)
   - Fallback behavior when conditions are ambiguous
3. Implement the workflow in the automation engine.
4. Add configurable parameters exposed via admin panel.
5. Add logging: trigger reason, evaluation result, action taken, confidence (if AI-based).
6. Add tests covering: happy path, edge cases, fallback scenarios.
7. Summarize the workflow behavior and configuration options.

## Quality rules
- Use declarative workflow definitions — avoid hardcoded if/else chains.
- All AI-assigned values (category, priority, routing) must be overridable by agents.
- SLA calculations must respect business hours and timezone.
- Never auto-escalate silently — always notify agent and supervisor.
- Log every state transition with timestamp, actor, and reason.
- Make all thresholds and rules configurable without code changes.
- Deduplicate alerts — never spam the same notification repeatedly.
