# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:19Z)

**Source:** CLAUDE.md

# Backend Python Rules - FinShield AI

Apply these rules when editing Python files.

## Architecture
- Use FastAPI with async/await.
- Follow dependency injection with `Depends()`.
- Keep business logic in services.
- Use Pydantic v2 models.
- Separate concerns: routes → services → repositories → models.
- Implement multi-tenant architecture with RLS.

## Database
- Use SQLAlchemy 2.0 async.
- Implement RLS for tenant isolation.
- Prefer explicit joins.
- Add indexes for fraud queries.
- Use transactions for consistency.
- Implement connection pooling.
- Support multiple backends.

## ML & Fraud Detection
- Use scikit-learn, XGBoost, PyTorch.
- Export neural networks to ONNX.
- Implement 200+ feature pipeline.
- Multi-layer detection: Rules → Unsupervised → Supervised → Ensemble.
- Support model drift detection.
- Implement SMOTE for class imbalance.
- Use SHAP for explainability.

## Fraud Engine
- Implement 20+ rules with YAML DSL.
- Support custom rule creation.
- Real-time scoring <100ms.
- Decision engine: PASS/FLAG/ALERT/BLOCK.
- Post-settlement detection.
- Fraud score write-back.

## Security
- Validate inputs with Pydantic v2.
- Use JWT 15-min access tokens.
- Hash passwords with bcrypt.
- Encrypt credentials with AES-256.
- Implement rate limiting per tenant.
- Log security events with correlation IDs.
- Follow ISO 27001, SOC 2, PCI-DSS.

## Data Integration
- Implement 20+ connectors.
- Schema normalization.
- Real-time streaming via Kafka, Event Hubs.
- Batch ingestion via CSV, SFTP.
- CDC for low-latency polling.
- Graceful degradation.

## Notifications
- Multi-channel: email, SMS, push.
- Webhook support.
- Real-time WebSocket.
- Graceful fallback.
- Alert escalation.

## Caching
- Use Redis for sessions and caching.
- Implement LRU cache.
- Connection pooling.
- Optimize queries.
- Monitor API response times.

## Task Queue
- Use Celery with Redis.
- Background model retraining.
- Batch processing.
- Retry mechanisms.
- Monitor queue health.

## API Design
- RESTful endpoints.
- OpenAPI documentation.
- Rate limiting per plan.
- Pagination for large sets.
- Filtering and sorting.
- WebSocket endpoints.

## Testing
- Unit tests with pytest.
- Integration tests with httpx.
- Load testing with Locust.
- Security testing.
- ML model validation.
- End-to-end testing.

## Monitoring
- Structured logging.
- Custom metrics.
- Model accuracy monitoring.
- API performance metrics.
- Real-time dashboard.
- Alerting for issues.

## Deployment
- Docker multi-stage builds.
- Environment configuration.
- Health checks.
- Database migrations.
- CI/CD pipeline.
- Blue-green deployment.
