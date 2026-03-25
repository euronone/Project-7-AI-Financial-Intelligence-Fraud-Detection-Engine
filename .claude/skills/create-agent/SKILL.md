---
name: create-agent
description: Create a new AI agent (chatbot, voice bot, classifier, copilot assistant)
---

# Create Agent Skill

## Goal
Build a new AI agent with single responsibility, explicit tool access, and guardrails.

## Steps
1. Ask for: agent purpose, input/output format, tools it needs access to, and guardrail requirements.
2. Create the agent module:
   - `agents/{name}/agent.py` — core agent logic with tool orchestration
   - `agents/{name}/tools.py` — explicit tool definitions the agent can use
   - `agents/{name}/prompts.py` — versioned prompt templates
   - `agents/{name}/guardrails.py` — input/output validation and safety checks
   - `agents/{name}/schemas.py` — agent input/output Pydantic models
3. Implement the agent loop: input validation > context assembly > model call > output guardrails > response.
4. Add confidence scoring to agent outputs.
5. Add fallback responses for low-confidence or error scenarios.
6. Add structured logging for key decisions (tool use, confidence, fallback triggers).
7. Add unit tests with fixture-based assertions (not exact match).
8. Summarize the agent's capabilities and limitations.

## Quality rules
- Single responsibility — one agent, one job.
- Tool access must be explicit and minimal.
- Add guardrails: input sanitization, output length limits, toxicity checks.
- Never expose raw model output to end users without post-processing.
- Rate-limit AI calls per customer/session.
- Log agent decisions for debugging and audit.
- Keep prompt templates in separate files, not inline strings.
- Prefer deterministic helpers around fragile model behavior.
