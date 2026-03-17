<<<<<<< HEAD
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
=======
# FinShield AI — API Specification

**Base URL:** `/api/v1`  
**Auth:** JWT (Bearer) or API key; optional Azure AD SSO.  

This document summarizes the FastAPI backend API. For full detail see OpenAPI/Swagger at `/docs`. Mobile and web clients use the same API; document mobile-specific needs (e.g. push, app version header) here or in DEPLOYMENT.

---

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with email/password → JWT |
| POST | `/auth/register` | Register new user (admin only) |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke refresh token |
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/auth/me` | Current user profile |
| PUT | `/auth/me` | Update current user profile |
| POST | `/auth/mfa/enable` | Enable MFA |
| POST | `/auth/mfa/verify` | Verify MFA token |

---

## Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | List transactions (paginated, filtered, sorted) |
| GET | `/transactions/{id}` | Transaction detail with fraud analysis |
| POST | `/transactions` | Ingest transaction (triggers fraud pipeline) |
| POST | `/transactions/batch` | Batch ingest |
| GET | `/transactions/{id}/risk-scores` | Risk score history |
| GET | `/transactions/{id}/alerts` | Alerts linked to transaction |
| GET | `/transactions/{id}/similar` | Similar transactions (ML) |
| POST | `/transactions/search` | Advanced search |
| GET | `/transactions/export` | Export (CSV/JSON) |

**GET `/transactions` query params:** `page`, `page_size`, `sort_by`, `sort_order`, `status`, `risk_level`, `min_amount`, `max_amount`, `date_from`, `date_to`, `entity_id`, `channel`, `country_code`.

---

## Fraud Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fraud-alerts` | List alerts (paginated, filtered) |
| GET | `/fraud-alerts/{id}` | Alert detail with evidence |
| PUT | `/fraud-alerts/{id}/status` | Update status |
| PUT | `/fraud-alerts/{id}/assign` | Assign to analyst |
| POST | `/fraud-alerts/{id}/escalate` | Escalate |
| POST | `/fraud-alerts/{id}/resolve` | Resolve with notes |
| GET | `/fraud-alerts/statistics` | Counts by status, severity |
| POST | `/fraud-alerts/{id}/create-case` | Create case from alert |

---

## Risk Scoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/risk-scoring/entity/{entity_id}` | Entity risk profile |
| GET | `/risk-scoring/entity/{entity_id}/history` | Risk score history |
| POST | `/risk-scoring/calculate` | On-demand risk calculation |
| GET | `/risk-scoring/distribution` | Risk distribution |
| GET | `/risk-scoring/top-risk` | Top N highest risk entities |

---

## Rules Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rules` | List rules |
| POST | `/rules` | Create rule |
| GET | `/rules/{id}` | Rule detail |
| PUT | `/rules/{id}` | Update rule |
| DELETE | `/rules/{id}` | Delete (soft) |
| PUT | `/rules/{id}/toggle` | Enable/disable |
| POST | `/rules/{id}/test` | Test against sample transaction |
| GET | `/rules/templates` | Pre-built templates |
| GET | `/rules/{id}/performance` | Hit rate, false positive stats |

---

## Case Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List cases |
| POST | `/cases` | Create case |
| GET | `/cases/{id}` | Case detail |
| PUT | `/cases/{id}` | Update case |
| PUT | `/cases/{id}/assign` | Assign case |
| POST | `/cases/{id}/timeline` | Add timeline event |
| PUT | `/cases/{id}/close` | Close with findings |
| GET | `/cases/statistics` | Case statistics |

---

## Analytics & Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/overview` | Dashboard overview |
| GET | `/analytics/fraud-trends` | Fraud trend time series |
| GET | `/analytics/transaction-volume` | Volume over time |
| GET | `/analytics/risk-distribution` | Risk distribution |
| GET | `/analytics/top-fraud-patterns` | Top patterns |
| GET | `/analytics/model-performance` | ML model metrics |
| GET | `/analytics/geographic` | Geographic distribution |
| POST | `/analytics/reports/generate` | Generate report |
| GET | `/analytics/reports/{id}/download` | Download report |

---

## Entities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/entities` | List entities |
| GET | `/entities/{id}` | Entity 360 |
| GET | `/entities/{id}/transactions` | Entity transactions |
| GET | `/entities/{id}/alerts` | Entity alerts |
| GET | `/entities/{id}/risk-profile` | Risk profile |
| GET | `/entities/{id}/network` | Relationship network |
| PUT | `/entities/{id}/watchlist` | Add/remove watchlist |

---

## ML Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | List models |
| GET | `/models/{id}` | Model detail + metrics |
| POST | `/models/{id}/promote` | Promote to active |
| POST | `/models/{id}/retire` | Retire model |
| GET | `/models/compare` | Compare performance |
| POST | `/models/retrain` | Trigger retraining |

---

## Watchlists

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/watchlists` | List entries |
| POST | `/watchlists` | Add entry |
| DELETE | `/watchlists/{id}` | Remove entry |
| POST | `/watchlists/screen` | Screen entity against lists |
| POST | `/watchlists/import` | Bulk import (CSV) |

---

## Network Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/network/graph` | Network graph data |
| GET | `/network/entity/{entity_id}/connections` | Entity connections |
| POST | `/network/analyze` | Network-based fraud analysis |

---

## Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit` | List audit logs (paginated) |
| GET | `/audit/export` | Export audit logs |

---

## System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/detailed` | Detailed (DB, Redis, Event Hub) |
| GET | `/settings` | System settings |
| PUT | `/settings` | Update settings |
| GET | `/users` | List users (admin) |
| POST | `/users` | Create user (admin) |
| PUT | `/users/{id}` | Update user (admin) |
| DELETE | `/users/{id}` | Deactivate user (admin) |

---

## Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhooks` | List webhooks |
| POST | `/webhooks` | Create webhook |
| PUT | `/webhooks/{id}` | Update webhook |
| DELETE | `/webhooks/{id}` | Delete webhook |
| POST | `/webhooks/{id}/test` | Test delivery |

---

## WebSocket Events (Socket.IO)

**Namespaces:** `/alerts`, `/transactions`, `/dashboard`

| Event | Namespace | Payload |
|-------|-----------|---------|
| `new_alert` | /alerts | Alert object |
| `alert_updated` | /alerts | Updated alert |
| `new_transaction` | /transactions | Transaction with fraud score |
| `transaction_flagged` | /transactions | Flagged transaction |
| `metrics_update` | /dashboard | Dashboard metrics |
| `model_status` | /dashboard | Model training/deployment status |

---

*For request/response schemas and error formats see the OpenAPI spec at `/docs`.*
>>>>>>> 4ecd489eaf599472f34a30b56d623fbfeb2f4a66
