# API Specification

Base URL: `/api/v1`

## Authentication
- `POST /auth/login` - Login with email/password → JWT
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Revoke refresh token
- `GET /auth/me` - Get current user profile
- `POST /auth/mfa/enable` - Enable MFA
- `POST /auth/mfa/verify` - Verify MFA token

## Transactions
- `GET /transactions` - List transactions (paginated, filtered, sorted)
- `GET /transactions/{id}` - Get transaction detail with fraud analysis
- `POST /transactions` - Ingest a new transaction
- `POST /transactions/batch` - Batch ingest transactions
- `POST /transactions/search` - Advanced search with complex filters

## Fraud Alerts
- `GET /fraud-alerts` - List alerts (paginated, filtered)
- `GET /fraud-alerts/{id}` - Get alert detail with evidence
- `PUT /fraud-alerts/{id}/status` - Update alert status
- `POST /fraud-alerts/{id}/resolve` - Resolve alert with notes
- `POST /fraud-alerts/{id}/create-case` - Create case from alert

## Risk Scoring
- `GET /risk-scoring/entity/{entity_id}` - Get entity risk profile
- `POST /risk-scoring/calculate` - On-demand risk calculation
- `GET /risk-scoring/top-risk` - Top N highest risk entities

## Rules Engine
- `GET /rules` - List all rules
- `POST /rules` - Create a new rule
- `POST /rules/{id}/test` - Test rule against sample transaction

## Case Management
- `GET /cases` - List cases
- `POST /cases` - Create a new case
- `PUT /cases/{id}/close` - Close case with findings

## Analytics & Reporting
- `GET /analytics/overview` - Dashboard overview metrics
- `GET /analytics/fraud-trends` - Fraud trend data
- `POST /analytics/reports/generate` - Generate a custom report

## Entities
- `GET /entities` - List entities
- `GET /entities/{id}/transactions` - Entity transaction history
- `GET /entities/{id}/network` - Entity relationship network

## ML Models
- `GET /models` - List all models
- `POST /models/{id}/promote` - Promote model to active
- `POST /models/retrain` - Trigger model retraining

## Watchlists
- `GET /watchlists` - List watchlist entries
- `POST /watchlists/screen` - Screen entity against all lists

## System & Webhooks
- `GET /health` - Health check
- `GET /settings` - Get system settings
- `POST /webhooks` - Create webhook
