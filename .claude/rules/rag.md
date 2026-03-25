# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

# RAG Rules

Apply these rules when editing retrieval, embeddings, or generation flows.

## Separation of concerns
- Keep ingestion, chunking, embedding, retrieval, and generation as separate modules.
- Never mix retrieval logic into route handlers or agent code.
- Keep prompt templates in dedicated files, versionable and inspectable.

## Ingestion
- Support multiple data sources: help articles, docs, FAQ, past tickets, wikis.
- Validate and sanitize all ingested content (treat as untrusted).
- Track ingestion status and errors per document.
- Support incremental re-ingestion without full reprocessing.

## Chunking and embedding
- Make chunk size and overlap configurable per data source.
- Do not hardcode embedding providers in business logic — use an adapter.
- Store embeddings with source metadata for attribution.
- Support batch and streaming embedding generation.

## Retrieval
- Log retrieval misses, low-confidence results, and fallback conditions.
- Use hybrid search (semantic + keyword) where appropriate.
- Apply relevance scoring and set minimum confidence thresholds.
- Support multi-document retrieval with deduplication.

## Generation
- Add source attribution to all AI-generated responses.
- Apply guardrails: length limits, toxicity checks, hallucination detection.
- Add fallback responses when retrieved context is insufficient.
- Never return raw model output without post-processing.

## Knowledge base management
- Support document upload, PDF ingestion, and website scraping.
- Track document versions and allow rollback.
- Auto-chunk on upload with configurable settings.
- Provide admin endpoints for re-indexing and cache invalidation.
