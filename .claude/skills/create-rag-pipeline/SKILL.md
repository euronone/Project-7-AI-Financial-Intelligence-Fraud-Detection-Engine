---
name: create-rag-pipeline
description: Build or extend a RAG pipeline (ingestion, chunking, embedding, retrieval, generation)
---

# Create RAG Pipeline Skill

## Goal
Build or extend a RAG pipeline component following the platform's separation of concerns.

## Steps
1. Ask for: which pipeline stage (ingestion, chunking, embedding, retrieval, generation), data source type, and specific requirements.
2. For **ingestion**: create a data source connector with validation and status tracking.
3. For **chunking**: implement configurable chunking with size/overlap parameters per source type.
4. For **embedding**: create an embedding adapter (provider-agnostic) with batch support.
5. For **retrieval**: implement hybrid search (semantic + keyword) with relevance scoring and confidence thresholds.
6. For **generation**: create a generation module with prompt template, source attribution, and guardrails.
7. Add structured logging: retrieval misses, low-confidence results, fallback triggers.
8. Add tests: unit tests for each stage, integration tests for the full pipeline.
9. Summarize the pipeline configuration and data flow.

## Quality rules
- Keep each pipeline stage as a separate, composable module.
- Make chunk size, overlap, and confidence thresholds configurable.
- Do not hardcode embedding providers — use adapter pattern.
- Store embeddings with source metadata for attribution.
- Add fallback responses when retrieved context is insufficient.
- Log retrieval failures and low-confidence conditions.
- Never mix retrieval logic into route handlers.
- Keep prompt templates in dedicated, versionable files.
