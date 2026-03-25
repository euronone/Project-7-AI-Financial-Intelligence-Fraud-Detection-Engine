# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

# Voice and Video Rules

Apply these rules when editing voice AI, video call, or media processing features.

## Voice AI
- Use streaming speech-to-text for real-time transcription — never batch-only in live calls.
- Keep voice bot response generation async and non-blocking.
- Support both real-time and post-call transcription modes.
- Apply voice activity detection (VAD) before processing.
- Store tone/sentiment analysis results as metadata, not inline.

## Call management
- Store call recordings in object storage (S3), never in the database.
- Generate signed URLs for recording access with expiry.
- Log call metadata (duration, participants, quality score) — never raw audio.
- Support call transfer, hold, and mute as first-class operations.

## Video support
- Gracefully degrade video quality on poor connections.
- Support screen sharing and file sharing within calls.
- Generate AI transcripts and summaries post-call.
- Keep chat-inside-video as a separate WebSocket channel.

## Real-time monitoring
- Stream live transcription to the monitoring dashboard.
- Detect sentiment shifts in real-time and flag escalation triggers.
- Track agent performance metrics per call.
- Apply compliance checks on live calls (forbidden phrases, required disclosures).

## Performance
- Use WebRTC for peer-to-peer media where possible.
- Offload transcription and analysis to dedicated workers.
- Buffer audio chunks efficiently — avoid excessive memory allocation.
- Set hard timeouts on all media processing operations.
