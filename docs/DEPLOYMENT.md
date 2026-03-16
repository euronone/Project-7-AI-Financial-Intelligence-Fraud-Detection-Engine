# Deployment

## Local Development
- **Docker Compose:** Used for local infrastructure (PostgreSQL 16, Redis 7, Azure Event Hub Emulator, MailHog).
- **Backend:** Run locally via `uvicorn` and `celery`.
- **Frontend:** Run locally via `npm run dev`.

## Cloud Architecture (Azure)
- **Compute:** Azure Container Apps (Frontend, Backend API, Backend Worker, Stream Processor).
- **Database:** Azure Database for PostgreSQL Flexible Server.
- **Cache:** Azure Cache for Redis.
- **Messaging:** Azure Event Hubs.
- **Storage:** Azure Blob Storage (for ML models and reports).
- **Security:** Azure Key Vault (secrets), Managed Identities.
- **CDN/WAF:** Azure Front Door.
- **Monitoring:** Azure Monitor + Application Insights + Log Analytics Workspace.

## Environments
- **Development:** Manual / branch push.
- **Staging:** Auto-deploy on merge to `main`.
- **Production:** Manual trigger with approval gate (Blue-Green deployment).

## CI/CD Pipelines (GitHub Actions)
- `ci.yml`: Lint, type check, unit tests, E2E tests, security scans.
- `cd-staging.yml`: Build/push to ACR, deploy to staging, run integration tests.
- `cd-production.yml`: Blue-green deployment, DB migrations, cache invalidation.
- `infrastructure.yml`: Terraform plan/apply.
- `ml-pipeline.yml`: Data prep, model training, evaluation, registration to Azure ML.

## Non-Functional Goals
- **Scalable:** Auto-scaling Container Apps based on HTTP requests, Celery queue length, and Event Hub lag.
- **Secure:** VNet integration, private endpoints, WAF, and encrypted data.
- **Observable:** Distributed tracing (OpenTelemetry) and structured logging.
- **Reliable:** 99.9% uptime SLA, automated backups, and circuit breakers.