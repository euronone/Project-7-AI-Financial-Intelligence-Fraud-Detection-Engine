---
name: create-channel-adapter
description: Add a new communication channel adapter (WhatsApp, SMS, Slack, email, etc.)
---

# Create Channel Adapter Skill

## Goal
Add a new omni-channel adapter that integrates with the unified conversation system.

## Steps
1. Ask for: channel name, provider API docs/reference, message types supported.
2. Create the adapter implementing the common channel interface:
   - `channels/{name}/adapter.py` — implements `ChannelAdapter` interface
   - `channels/{name}/schemas.py` — channel-specific message schemas
   - `channels/{name}/webhook.py` — inbound webhook handler (if applicable)
   - `channels/{name}/config.py` — channel-specific configuration
3. Implement message normalization: convert channel-specific format to internal schema.
4. Implement outbound message delivery with retry and error handling.
5. Add webhook signature validation for inbound events.
6. Register the channel in the channel registry.
7. Add tests: unit tests for normalization, integration tests for webhook handling.
8. Summarize changes.

## Quality rules
- Implement the common `ChannelAdapter` interface — no channel-specific logic in core services.
- Normalize all messages to the internal unified schema.
- Add retry logic with exponential backoff for outbound delivery.
- Validate webhook signatures on all inbound requests.
- Handle rate limits per provider's requirements.
- Queue messages when the channel is temporarily unavailable.
- Never hardcode API keys or endpoints — use config.
- Log all delivery attempts with status and latency.
