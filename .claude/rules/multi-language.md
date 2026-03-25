# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Multi-Language Support Rules

Apply these rules when editing language detection, translation, or localized response features.

## Language detection
- Detect language early in the pipeline — before NLP processing and AI generation.
- Use the detected language to route to the appropriate model and prompt template.
- Handle mixed-language messages gracefully — default to the dominant language.
- Log detected language with confidence for monitoring.

## Translation
- Keep translation as a separate service/adapter — never inline in business logic.
- Support both real-time (chat) and batch (ticket/email) translation.
- Preserve formatting, links, and structured content through translation.
- Show original message alongside translation for agent review.

## Localization
- Keep all user-facing strings in localization files — never hardcode text.
- Support locale-specific formatting (dates, numbers, currencies).
- Test AI responses in supported languages for quality.
- Track language distribution across channels for capacity planning.
