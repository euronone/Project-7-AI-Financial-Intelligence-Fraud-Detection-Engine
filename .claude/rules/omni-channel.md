# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

# Omni-Channel Communication Rules

Apply these rules when editing channel integrations, conversation threading, or multi-channel messaging.

## Channel management
- Each channel (chat, email, voice, video, WhatsApp, SMS, Slack, social) must implement a common channel interface.
- Use adapter pattern for channel-specific logic — keep core conversation logic channel-agnostic.
- Never hardcode channel-specific behavior in shared services.
- Support adding new channels without modifying core conversation logic.

## Unified conversation threading
- Maintain a single conversation thread per customer across all channels.
- Synchronize conversation history when a customer switches channels.
- Preserve full context (messages, attachments, metadata) across channel switches.
- Track channel of origin for each message in the thread.

## Message handling
- Normalize message formats across channels into a common internal schema.
- Support rich content types: text, images, files, cards, quick replies.
- Handle delivery status tracking per channel (sent, delivered, read).
- Apply rate limiting per channel according to provider limits.

## Channel-specific rules
- **WebSocket chat**: Handle reconnection, typing indicators, read receipts.
- **Email**: Parse threads correctly, handle attachments, respect reply-to chains.
- **WhatsApp/SMS**: Respect message templates and opt-in requirements.
- **Slack/Teams**: Use proper bot token scoping and slash command handling.
- **Voice/Video**: Delegate to voice-video rules — do not duplicate logic here.

## Resilience
- Queue messages when a channel is temporarily unavailable.
- Add retry logic with exponential backoff for outbound messages.
- Log channel failures with error details for monitoring.
