# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

# Real-Time Infrastructure Rules

Apply these rules when editing WebSocket handlers, Kafka producers/consumers, event streaming, or async task processing.

## WebSockets
- Keep WebSocket handlers stateless — persist all state in Redis.
- Implement heartbeat/ping-pong to detect stale connections.
- Handle reconnection gracefully on both client and server.
- Authenticate WebSocket connections on handshake — not after.
- Apply per-connection and per-user rate limiting.
- Never block the event loop in WebSocket handlers.

## Kafka event streaming
- Define explicit Avro or JSON schemas for all Kafka topics.
- Use consumer groups for horizontal scaling of event processing.
- Implement idempotent consumers — handle duplicate events gracefully.
- Set appropriate retention policies per topic.
- Use dead-letter topics for failed event processing.
- Log event production and consumption with correlation IDs.

## Async task processing
- Use Celery for background tasks: embeddings, transcription, report generation.
- Set explicit timeouts and retries on all async tasks.
- Use task result backends (Redis) for status tracking.
- Implement task deduplication for expensive operations.
- Monitor queue depth and worker health.

## Performance
- Target sub-100ms latency for WebSocket message delivery.
- Batch Kafka messages where throughput matters more than latency.
- Use connection pooling for Redis and database connections.
- Profile and optimize hot paths regularly.

## Resilience
- Handle backpressure: slow consumers must not crash producers.
- Gracefully handle service restarts without losing in-flight messages.
- Use distributed locks (Redis) for operations that must not run concurrently.
