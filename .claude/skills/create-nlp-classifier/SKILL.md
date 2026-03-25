---
name: create-nlp-classifier
description: Build a new NLP classifier (intent, sentiment, urgency, escalation, language detection)
---

# Create NLP Classifier Skill

## Goal
Build a new NLP classification module that fits into the platform's composable NLP pipeline.

## Steps
1. Ask for: classifier type (intent/sentiment/urgency/escalation/topic/language), model backend, confidence threshold requirements.
2. Create the classifier module:
   - `nlp/{name}/classifier.py` — implements the common classifier interface
   - `nlp/{name}/preprocessing.py` — input normalization and tokenization
   - `nlp/{name}/postprocessing.py` — output formatting, threshold application
   - `nlp/{name}/config.py` — model version, thresholds, feature flags
   - `nlp/{name}/schemas.py` — input/output Pydantic models with confidence scores
3. Implement the pipeline: input > preprocessing > model inference > postprocessing > output.
4. Add confidence thresholds with configurable fallback behavior.
5. Add model versioning — track which version produced each prediction.
6. Add structured logging: input hash, model version, confidence, prediction.
7. Add tests with fixture data covering edge cases.
8. Summarize classifier capabilities and configuration.

## Quality rules
- Use explicit confidence thresholds — never silently drop low-confidence results.
- Return confidence scores alongside all predictions.
- Make thresholds configurable per use case.
- Version all models and log which version produced each prediction.
- Support swappable model backends via adapter pattern.
- Never couple NLP logic directly to route handlers.
- Never log raw customer text — use anonymized or hashed data.
