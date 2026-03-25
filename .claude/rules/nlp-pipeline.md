# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# NLP Pipeline Rules

Apply these rules when editing intent detection, sentiment analysis, classification, or NLP model integration.

## Architecture
- Keep intent detection, sentiment analysis, urgency classification, and topic clustering as separate composable modules.
- Never couple NLP logic directly to route handlers — use a service layer.
- Use a pipeline pattern: input > preprocessing > model inference > postprocessing > output.
- Support swappable model backends via adapter pattern.

## Confidence and thresholds
- Use explicit confidence thresholds for all classifications.
- Never silently drop low-confidence results — log them and apply fallback logic.
- Return confidence scores alongside predictions in API responses.
- Make thresholds configurable per use case (escalation detection vs topic clustering).

## Model management
- Version all NLP models and track which version produced each prediction.
- Store model performance metrics (accuracy, latency, drift).
- Support A/B testing between model versions.
- Keep model artifacts in object storage, not in the codebase.

## Logging and learning
- Log all classification outputs with input hash, model version, and confidence.
- Feed agent corrections back into the training pipeline.
- Track prediction distribution drift over time.
- Never log raw customer text in analytics — use anonymized or aggregated data.

## Specific classifiers
- **Intent detection**: Support multi-intent per message; return ranked intents.
- **Sentiment analysis**: Use a consistent scale (e.g., -1 to 1); flag rapid sentiment shifts.
- **Urgency classification**: Map to actionable priority levels tied to SLA rules.
- **Escalation detection**: Trigger alerts but never auto-escalate without human confirmation (configurable).
- **Language detection**: Detect early in the pipeline and route to appropriate language model.
