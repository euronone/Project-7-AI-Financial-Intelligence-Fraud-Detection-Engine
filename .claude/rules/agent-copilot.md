# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:18Z)

**Source:** CLAUDE.md

# Agent Copilot Rules

Apply these rules when editing the AI assistant features for human support agents.

## Suggested replies
- Generate reply suggestions based on conversation context and knowledge base.
- Show confidence scores alongside suggestions.
- Allow agents to edit, accept, or dismiss suggestions with one click.
- Never auto-send suggestions — always require agent confirmation.
- Track acceptance/edit/dismiss rates for model improvement.

## Knowledge retrieval
- Surface relevant knowledge base articles inline during conversations.
- Rank results by relevance to the current conversation context.
- Support agent feedback on article relevance (thumbs up/down).
- Cache frequently accessed articles in Redis.

## Drafting and summarization
- Auto-draft email responses based on conversation context.
- Generate ticket summaries on demand and on resolution.
- Provide recommended troubleshooting steps based on issue classification.
- Keep all drafts editable — never lock agent into AI-generated content.

## Performance
- Copilot suggestions must load within 2 seconds — optimize aggressively.
- Use streaming responses for long-form drafts.
- Prefetch likely-needed context when a ticket is opened.
- Never block the agent UI waiting for AI responses — show loading states.

## Learning loop
- Log which suggestions agents accept, edit, or dismiss.
- Feed agent corrections into the RAG and NLP improvement pipelines.
- Track copilot usage metrics per agent for training and optimization.
- Never use individual agent data for punitive purposes — aggregate only.
