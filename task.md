# FinShield AI — Feature Task Assignments

> Each feature maps to a dedicated branch off `development`. Branch naming follows the convention: `feature/<feature-id>-<slug>`.
> Assignees column is intentionally blank — fill in contributor GitHub handles before distribution.

> **IMPORTANT:** The sections below are ordered by **dependency-safe development sequence**, not by feature number.
> Follow the stage order to avoid blocked work and migration failures.

---

## Branch Strategy

```
main
└── development
    ├── feature/f11-authentication-authorization   ← Stage 2 (start here after foundation)
    ├── feature/f8-entity-management               ← Stage 3A (backend only — entities needed before transactions)
    ├── feature/f1-realtime-transaction-monitoring ← Stage 3B (REST ingestion) + Stage 7 (streaming)
    ├── feature/f3-rules-engine                    ← Stage 4
    ├── feature/f2-ml-fraud-detection              ← Stage 5 (feature eng + models) + Stage 6 (pipeline wiring)
    ├── feature/f5-risk-scoring                    ← Stage 6 (alongside fraud pipeline)
    ├── feature/f4-fraud-alert-management          ← Stage 8
    ├── feature/f6-case-management                 ← Stage 9
    ├── feature/f13-notifications-webhooks         ← Stage 10
    ├── feature/f7-analytics-reporting             ← Stage 11
    ├── feature/f9-watchlist-sanctions-screening   ← Stage 13
    ├── feature/f10-network-graph-visualization    ← Stage 14
    ├── feature/f12-audit-trail                    ← Stage 15
    └── feature/f14-settings-configuration        ← Stage 16
```

All PRs must target `development`. CI must pass before merge. Requires at least 1 reviewer approval.

---

## Dependency Chain Overview

```
Stage 0: Foundation (config, DB session, all models + schemas, migrations)
    │
    ▼
Stage 2: F11 — Auth & RBAC (every endpoint needs this)
    │
    ▼
Stage 3: F8-backend (entities) + F1-Part A (transaction REST ingestion) + Seed Data
    │
    ├──────────────────────┐
    ▼                      ▼
Stage 4: F3            Stage 5: F2 — Feature Eng + ML Models
Rules Engine               │
    │                      ▼
    └──────────┬─── Stage 6: F2 pipeline + F5 — Fraud Detection + Risk Scoring
               │
               ▼
         Stage 7: F1-Part B — WebSocket + Event Hub Streaming
               │
               ▼
         Stage 8: F4 — Fraud Alerts
               │
          ┌────┴────┐
          ▼         ▼
     Stage 9:   Stage 10:
     F6 Cases   F13 Notifications
          │
     ┌────┴──────────────────────┐
     ▼                           ▼
Stage 11: F7 Analytics    Stage 12: F8-frontend (Entity 360)
                                   Stage 13: F9 Watchlists
                                   Stage 14: F10 Network Graph
                                   Stage 15: F12 Audit Trail
                                   Stage 16: F14 Settings
```

---

## Stage 0 — Foundation (Pre-Feature, No Branch)

> **Not a feature branch.** This work goes directly on `development` as the project scaffold.
> Every feature depends on this being complete. Do not start any feature branch until Stage 0 is merged.

**No assignee branch — done once by project lead / first contributor.**

| Task | Files |
|---|---|
| App config & environment settings | `app/config.py`, `backend/.env.example` |
| Async DB session factory | `app/db/session.py` |
| Base SQLAlchemy model (audit fields) | `app/models/base.py` |
| Custom exceptions & error handlers | `app/core/exceptions.py` |
| Request middleware (logging, CORS, timing) | `app/core/middleware.py` |
| Rate limiter | `app/core/rate_limiter.py` |
| Startup/shutdown lifecycle events | `app/core/events.py` |
| **All SQLAlchemy models** (in FK order below) | `app/models/` |
| **All Pydantic schemas** (mirrors models) | `app/schemas/` |
| Alembic config + initial migration | `alembic.ini`, `app/db/migrations/` |
| FastAPI app entry point + router aggregator | `app/main.py`, `app/api/router.py` |
| Docker Compose local infra | `docker-compose.yml` |

**SQLAlchemy model creation order (respect FK constraints):**
1. `user.py`
2. `entity.py`
3. `transaction.py` ← FK → entities
4. `rule.py` ← FK → users
5. `ml_model.py` ← FK → users
6. `fraud_alert.py` ← FK → transactions, entities, rules, ml_models, users
7. `case.py` ← FK → users
8. `risk_score.py` ← FK → entities, transactions
9. `watchlist.py`
10. `audit_log.py` ← FK → users
11. `notification.py` ← FK → users
12. `webhook.py` ← FK → users

**Done when:** `alembic upgrade head` runs clean, FastAPI starts, `/api/v1/health` returns 200.

---

## Stage 2 — F11: Authentication & Authorization

**Branch:** `feature/f11-authentication-authorization`
**Assignee:**
**Depends on:** Stage 0 (Foundation)
**Weeks:** 1–3

> Every other feature's API endpoints require auth middleware. This must be fully merged before any other backend feature branch begins writing protected routes.

| Sub-task | Description |
|---|---|
| F11.1 | Email/password auth with JWT (access token: 15min, refresh token: 7d) |
| F11.2 | Azure AD SSO integration via OAuth2/OIDC |
| F11.3 | Multi-factor authentication (TOTP) |
| F11.4 | RBAC — Admin, Analyst, Investigator, Viewer roles with defined permissions |
| F11.5 | API key authentication for system-to-system integrations |
| F11.6 | Session management with forced logout capability |
| F11.7 | Password policy — min 12 chars, complexity requirements, history check |
| F11.8 | Account lockout after 5 failed attempts (30min cooldown) |

**Backend files:** `app/api/v1/auth.py`, `app/api/v1/users.py`, `app/core/security.py`, `app/core/permissions.py`
**Frontend files:** `src/app/(auth)/login/`, `src/app/(auth)/register/`, `src/app/(auth)/forgot-password/`, `src/app/(auth)/layout.tsx`, `src/lib/auth.ts`, `src/hooks/use-auth.ts`, `src/stores/auth-store.ts`, `src/middleware.ts`

**Done when:** Login returns JWT, protected routes reject unauthenticated requests, RBAC denies unauthorized roles.

---

## Stage 3 — F8 Backend + F1 Part A: Entities & Transaction Ingestion

> **Why F8 backend comes before F1:** The `transactions` table has a foreign key → `entities(id)`.
> Running the transaction migration without the entity service in place causes an FK violation.
> Build entity backend first, then transaction REST ingestion. Streaming (F1.3) comes in Stage 7.

### Stage 3A — F8 Backend: Entity Model & Service

**Branch:** `feature/f8-entity-management`
**Assignee:**
**Depends on:** Stage 2 (Auth)
**Weeks:** 4 (first half)

> Build the backend only. The Entity 360 frontend UI is Stage 12 — it needs alerts, cases, and risk scores to exist first.

| Sub-task | Description |
|---|---|
| F8-BE.1 | Entity CRUD — create, read, update; filter by type, risk level, KYC status, watchlist status |
| F8-BE.2 | Entity service with risk score field maintained on every transaction processed |
| F8-BE.3 | Entity list API endpoint with pagination and filtering |
| F8-BE.4 | Entity detail API endpoint (data only — no 360 UI yet) |

**Backend files:** `app/models/entity.py`, `app/schemas/entity.py`, `app/services/entity_service.py`, `app/api/v1/entities.py`

**Done when:** `POST /entities`, `GET /entities`, `GET /entities/{id}` work with auth.

---

### Stage 3B — F1 Part A: Transaction REST Ingestion

**Branch:** `feature/f1-realtime-transaction-monitoring`
**Assignee:**
**Depends on:** Stage 3A (Entity backend), Stage 2 (Auth)
**Weeks:** 4–5

> Build REST ingestion + transaction list/detail UI only. Wire fraud score as a stub (return 0.0) for now.
> F1.3 (WebSocket live feed) is Stage 7 — the fraud pipeline must exist before the feed is meaningful.

| Sub-task | Description |
|---|---|
| F1.1 | Transaction ingestion via REST API (POST /transactions, POST /transactions/batch) |
| F1.4 | Batch ingestion support (up to 10,000 transactions per request) |
| F1.5 | Transaction search: full-text, date range, amount, entity, status, risk level, channel, geography filters |
| F1.6 | Transaction detail view: raw data, fraud score breakdown (stub), risk factors, entity context |
| F1.7 | Export transactions to CSV and JSON with applied filters |

**Backend files:** `app/api/v1/transactions.py`, `app/services/transaction_service.py`
**Frontend files:** `src/app/(dashboard)/transactions/page.tsx`, `src/app/(dashboard)/transactions/[id]/page.tsx`, `src/components/transactions/transaction-table.tsx`, `src/components/transactions/transaction-filters.tsx`, `src/components/transactions/transaction-detail-card.tsx`, `src/hooks/use-transactions.ts`

> **Seed data:** Run `scripts/seed_data.py` after this stage so all future features have realistic data to work with.

**Done when:** Transactions can be ingested via REST, listed with filters, and viewed in detail. Fraud score shows as `0.0000` (stub).

---

## Stage 4 — F3: Rules Engine

**Branch:** `feature/f3-rules-engine`
**Assignee:**
**Depends on:** Stage 3B (transactions exist to test rules against)
**Weeks:** 5–6

> Rules engine has no ML dependency — build it in parallel with or immediately after F1 Part A.
> The fraud pipeline (Stage 6) will call this engine. Must be complete before Stage 6.

| Sub-task | Description |
|---|---|
| F3.2 | Condition types: amount thresholds, velocity checks, geographic, time-based, entity attributes, device/IP, pattern, custom field |
| F3.3 | Actions: block transaction, flag for review, adjust risk score, create alert, notify team, trigger webhook |
| F3.5 | Rule templates — pre-built rules for card testing, account takeover, money mules, first-party fraud |
| F3.6 | Rule priority and execution order configuration |
| F3.4 | Rule testing — dry-run against historical transactions to estimate hit rate and false positive rate |
| F3.7 | Rule performance dashboard — hit counts, false positive rates, trend over time |
| F3.1 | Visual rule builder UI with drag-and-drop condition grouping (AND/OR logic) |

**Backend files:** `app/rules/conditions.py`, `app/rules/actions.py`, `app/rules/engine.py`, `app/rules/templates.py`, `app/services/rules_engine_service.py`, `app/api/v1/rules.py`
**Frontend files:** `src/app/(dashboard)/rules-engine/page.tsx`, `src/app/(dashboard)/rules-engine/create/page.tsx`, `src/app/(dashboard)/rules-engine/[id]/page.tsx`, `src/components/rules/rule-list-item.tsx`, `src/components/rules/condition-editor.tsx`, `src/components/rules/rule-test-panel.tsx`, `src/components/rules/rule-builder.tsx`

**Done when:** Rules can be created, activated, and dry-run tested against seed transactions. Engine evaluates rules in priority order.

---

## Stage 5 — F2 Part A: Feature Engineering & ML Models

**Branch:** `feature/f2-ml-fraud-detection`
**Assignee:**
**Depends on:** Stage 3B (transaction + entity schemas finalized), Stage 3 seed data loaded
**Weeks:** 7–8

> Build feature engineering and train models first. The inference pipeline (Stage 6) wires these into the transaction flow.
> Do not wire into `transaction_service.py` yet — that is Stage 6.

| Sub-task | Description |
|---|---|
| F2.5 | Feature Engineering — extract 200+ features (transaction, temporal, velocity, entity, geographic, device, behavioral, network, derived) |
| F2.1 | Fraud Classifier — XGBoost + Neural Network ensemble, outputs fraud probability (0.0–1.0) |
| F2.2 | Anomaly Detection — Isolation Forest + Autoencoder for statistical outliers |
| F2.3 | Behavioral Profiling — per-entity baselines with configurable deviation thresholds |
| F2.4 | Network Analysis — graph-based fraud ring detection via connected components and centrality |
| F2.6 | Model Explainability — SHAP values per prediction, top contributing features on alert detail |
| F2.9 | ONNX Runtime inference pipeline for sub-10ms production serving |
| F2.7 | Model Registry — version, track, promote, retire models; compare metrics (accuracy, precision, recall, F1, AUC-ROC, AUC-PR) |
| F2.8 | Automated Retraining — trigger on performance degradation; feedback loop from resolved alerts |

**Backend files:** `app/ml/feature_engineering.py`, `app/ml/training/data_prep.py`, `app/ml/training/train_fraud_model.py`, `app/ml/training/train_anomaly_model.py`, `app/ml/training/train_risk_model.py`, `app/ml/training/evaluate.py`, `app/ml/fraud_classifier.py`, `app/ml/anomaly_detector.py`, `app/ml/behavioral_profiler.py`, `app/ml/network_analyzer.py`, `app/ml/explainability.py`, `app/ml/model_registry.py`, `app/ml/pipeline.py`, `app/services/ml_service.py`, `app/api/v1/models.py`
**Frontend files:** `src/app/(dashboard)/ml-models/page.tsx`, `src/app/(dashboard)/ml-models/[id]/page.tsx`, `src/components/charts/model-performance-chart.tsx`

**Done when:** Models are trained, exported to ONNX, and `ml/pipeline.py` can accept a transaction dict and return a fraud probability + SHAP values.

---

## Stage 6 — F2 Pipeline Wiring + F5: Fraud Detection & Risk Scoring

**Branch:** `feature/f2-ml-fraud-detection` (continued) + `feature/f5-risk-scoring`
**Assignee:**
**Depends on:** Stage 4 (Rules Engine), Stage 5 (ML Models trained and in ONNX)
**Weeks:** 8–9

> This stage wires the rules engine + ML models into the transaction ingestion path and builds the composite risk score.
> Update `transaction_service.py` to call the fraud pipeline on every POST /transactions.
> Add graceful fallback: if ML is unavailable, fall back to rules-only scoring.

| Sub-task | Description |
|---|---|
| F1.2 | Wire fraud detection pipeline into transaction ingestion — <200ms P95 latency end-to-end |
| F5.1 | Composite risk score (0.0–1.0) combining ML output, rule triggers, behavioral deviation, entity history, watchlist matches |
| F5.2 | Risk level classification: Low (0–0.3), Medium (0.3–0.6), High (0.6–0.8), Critical (0.8–1.0) — configurable thresholds |
| F5.3 | Component score breakdown: ML score, rule score, velocity score, behavioral score, network score |
| F5.7 | Risk score auto-updates on new transaction, alert resolution, or watchlist match |
| F5.4 | Risk score history per entity with trend visualization |
| F5.5 | Risk distribution dashboard — entity count per risk tier |
| F5.6 | Top-N highest risk entities leaderboard |

**Backend files:** `app/services/fraud_detection_service.py`, `app/services/risk_scoring_service.py`, `app/ml/risk_scorer.py`, `app/api/v1/risk_scoring.py`
**Frontend files:** `src/app/(dashboard)/risk-scoring/page.tsx`, `src/app/(dashboard)/risk-scoring/profiles/[id]/page.tsx`, `src/components/transactions/fraud-score-indicator.tsx`, `src/components/charts/risk-distribution-chart.tsx`

> **Fallback requirement (per reliability spec):** If ML service is down, `fraud_detection_service.py` must fall back to rules-only scoring. Do not let an ML failure break transaction ingestion.

**Done when:** POST /transactions returns a real fraud_score, risk_level is set, entity risk profile updates, `/risk-scoring/entity/{id}` returns component breakdown.

---

## Stage 7 — F1 Part B: WebSocket & Event Hub Streaming

**Branch:** `feature/f1-realtime-transaction-monitoring` (continued)
**Assignee:**
**Depends on:** Stage 6 (fraud pipeline must be wired — stream emits fraud-scored transactions)
**Weeks:** 9–10

> WebSocket live feed only makes sense after the fraud pipeline exists. Streaming infrastructure can be scaffolded earlier but should only be wired to real data now.

| Sub-task | Description |
|---|---|
| F1.3 | Live transaction feed on dashboard via WebSocket auto-refresh |
| F1.1 (streaming part) | Transaction ingestion via Azure Event Hubs (Kafka protocol) |

**Backend files:** `app/streaming/websocket_manager.py`, `app/streaming/producer.py`, `app/streaming/consumer.py`, `app/streaming/processor.py`, `app/core/events.py`
**Frontend files:** `src/lib/socket.ts`, `src/hooks/use-socket.ts`, `src/components/dashboard/live-activity-ticker.tsx`, `src/components/dashboard/recent-transactions.tsx`

**Done when:** Transactions submitted via Event Hub are processed through the fraud pipeline and emitted as `new_transaction` / `transaction_flagged` Socket.IO events to connected clients.

---

## Stage 8 — F4: Fraud Alert Management

**Branch:** `feature/f4-fraud-alert-management`
**Assignee:**
**Depends on:** Stage 6 (fraud pipeline creates alerts), Stage 7 (WebSocket delivers them in real-time)
**Weeks:** 10–11

| Sub-task | Description |
|---|---|
| F4.1 | Alert list view — filters by status, severity, type, date, assigned analyst |
| F4.3 | Alert workflow: Open → Investigating → Escalated → Resolved (Confirmed Fraud / False Positive) / Dismissed |
| F4.4 | Alert assignment to analysts with workload balancing visibility |
| F4.7 | Resolution notes — mandatory for confirmed fraud, optional for false positive |
| F4.2 | Alert detail view — transaction details, SHAP explanation, rule matches, entity risk profile, historical alerts, similar patterns, evidence panel |
| F4.5 | Bulk actions: bulk assign, bulk resolve, bulk dismiss |
| F4.6 | Alert escalation with reason and notification to senior analysts |
| F4.8 | Create investigation case from one or more related alerts |
| F4.9 | Real-time alert notifications via WebSocket, email, and SMS (configurable per severity) |

**Backend files:** `app/api/v1/fraud_alerts.py`, `app/services/audit_service.py` (needed for alert workflow logging)
**Frontend files:** `src/app/(dashboard)/fraud-alerts/page.tsx`, `src/app/(dashboard)/fraud-alerts/[id]/page.tsx`, `src/components/fraud/alert-card.tsx`, `src/components/fraud/alert-timeline.tsx`, `src/components/fraud/investigation-panel.tsx`, `src/components/fraud/evidence-viewer.tsx`

**Done when:** Alerts are created automatically by the fraud pipeline, appear in the list, and can be worked through the full status workflow.

---

## Stage 9 — F6: Case Management

**Branch:** `feature/f6-case-management`
**Assignee:**
**Depends on:** Stage 8 (alerts must exist to link to cases)
**Weeks:** 11–12

| Sub-task | Description |
|---|---|
| F6.1 | Create cases manually or from fraud alerts (one or more alerts per case) |
| F6.3 | Case timeline — chronological log of all actions and events |
| F6.4 | Case assignment and reassignment |
| F6.5 | Case status workflow: Open → In Progress → Pending Review → Escalated → Closed (Confirmed Fraud / False Positive) |
| F6.2 | Case detail — linked alerts, transactions, entities, and evidence |
| F6.6 | Case findings and resolution notes (structured form + free text) |
| F6.7 | Case statistics — open/closed counts, average resolution time, confirmed fraud rate |

**Backend files:** `app/api/v1/cases.py`, `app/services/case_service.py`, `app/models/case.py`, `app/schemas/case.py`
**Frontend files:** `src/app/(dashboard)/case-management/page.tsx`, `src/app/(dashboard)/case-management/[id]/page.tsx`

**Done when:** Cases can be created from alerts, assigned, progressed through the workflow, and closed with findings.

---

## Stage 10 — F13: Notifications & Webhooks

**Branch:** `feature/f13-notifications-webhooks`
**Assignee:**
**Depends on:** Stage 8 (alerts trigger notifications), Stage 9 (case updates trigger notifications)
**Weeks:** 12

| Sub-task | Description |
|---|---|
| F13.1 | In-app notification center with unread badge and mark-as-read |
| F13.2 | Email notifications for critical and high severity alerts |
| F13.3 | SMS notifications for critical alerts (configurable) |
| F13.5 | Notification preferences per user (events and channels) |
| F13.4 | Webhook support for external system integration (Slack, PagerDuty, SIEM) |
| F13.6 | Webhook retry with exponential backoff (max 5 retries) |
| F13.7 | Webhook HMAC signature verification |

**Backend files:** `app/api/v1/webhooks.py`, `app/services/notification_service.py`, `app/services/webhook_service.py`, `app/integrations/email_service.py`, `app/integrations/sms_service.py`
**Frontend files:** `src/app/(dashboard)/settings/notifications/page.tsx`, `src/app/(dashboard)/settings/api-keys/page.tsx`

**Done when:** Critical alerts trigger email + SMS + in-app notifications. Webhooks deliver payloads with HMAC signatures and retry on failure.

---

## Stage 11 — F7: Analytics & Reporting

**Branch:** `feature/f7-analytics-reporting`
**Assignee:**
**Depends on:** Stage 8 (alerts data), Stage 9 (cases data), Stage 5 (ML model metrics), Stage 4 (rule metrics)
**Weeks:** 13–14

> Analytics queries span all entities. All upstream features must be seeded with data before charts are meaningful.

| Sub-task | Description |
|---|---|
| F7.1 | Dashboard overview — total transactions (today/week/month), fraud rate, alert counts, avg fraud score, top risk entities |
| F7.2 | Fraud trend chart — count and rate over time (hourly/daily/weekly/monthly) |
| F7.3 | Transaction volume chart — volume over time by channel/status |
| F7.4 | Geographic heatmap — fraud density by country/region |
| F7.5 | Pattern analysis — most common fraud types, emerging patterns |
| F7.6 | Model performance dashboard — accuracy, precision, recall, F1, AUC over time per model |
| F7.7 | Rule effectiveness report — hit rate, false positive rate, catch rate per rule |
| F7.8 | Custom report builder — select metrics, date range, filters → generate PDF/CSV |
| F7.9 | Scheduled reports — daily/weekly/monthly auto-generated and emailed |

**Backend files:** `app/api/v1/analytics.py`, `app/services/analytics_service.py`
**Frontend files:** `src/app/(dashboard)/analytics/page.tsx`, `src/app/(dashboard)/analytics/trends/page.tsx`, `src/app/(dashboard)/analytics/patterns/page.tsx`, `src/app/(dashboard)/analytics/reports/page.tsx`, `src/app/(dashboard)/dashboard/page.tsx`, `src/components/charts/fraud-trend-chart.tsx`, `src/components/charts/transaction-volume-chart.tsx`, `src/components/charts/geo-heatmap.tsx`, `src/components/charts/anomaly-scatter-plot.tsx`, `src/components/dashboard/stats-card.tsx`, `src/components/dashboard/alert-feed.tsx`, `src/components/dashboard/risk-gauge.tsx`

**Done when:** Main dashboard shows live aggregated metrics. All chart endpoints return data. Reports can be generated and downloaded.

---

## Stage 12 — F8 Frontend: Entity 360 View

**Branch:** `feature/f8-entity-management` (continued)
**Assignee:**
**Depends on:** Stage 8 (alerts), Stage 9 (cases), Stage 6 (risk scores) — 360 view pulls from all of these
**Weeks:** 13–14

> The Entity 360 UI requires alerts, cases, and risk scores to exist. Backend was built in Stage 3A.
> Now build the complete frontend that aggregates everything.

| Sub-task | Description |
|---|---|
| F8.1 | Entity list — search, filter by type, risk level, KYC status, watchlist status |
| F8.2 | Entity 360 view — profile info, risk score breakdown, transaction history, alerts, cases, behavioral profile, network connections |
| F8.3 | Entity risk profile — historical risk scores, contributing factors, trend |
| F8.4 | Entity transaction pattern visualization — amount distribution, time patterns, geographic spread |
| F8.5 | Entity network graph — connections to other entities via transactions |
| F8.6 | Watchlist screening with match scoring |

**Backend files:** `app/api/v1/entities.py` (add remaining endpoints: `/transactions`, `/alerts`, `/risk-profile`, `/network`)
**Frontend files:** `src/app/(dashboard)/entities/page.tsx`, `src/app/(dashboard)/entities/[id]/page.tsx`, `src/types/entity.ts`

**Done when:** Entity 360 page shows full profile with transaction history, alerts, cases, risk score trend, and network connections.

---

## Stage 13 — F9: Watchlist & Sanctions Screening

**Branch:** `feature/f9-watchlist-sanctions-screening`
**Assignee:**
**Depends on:** Stage 12 (Entity 360 UI — watchlist status displayed there), Stage 3A (entity service for auto-screening)
**Weeks:** 14

| Sub-task | Description |
|---|---|
| F9.1 | Manage internal watchlists (blacklist, greylist) |
| F9.3 | Fuzzy name matching with configurable match threshold |
| F9.7 | CSV import/export for watchlist management |
| F9.2 | Integration with external sanctions lists (OFAC, UN, EU) |
| F9.5 | Automatic screening on new entity creation or transaction |
| F9.4 | Bulk screening of entity database |
| F9.6 | Watchlist hit alerts with match details and confidence score |

**Backend files:** `app/api/v1/watchlists.py`, `app/services/watchlist_service.py`, `app/integrations/sanctions_api.py`
**Frontend files:** `src/app/(dashboard)/watchlists/page.tsx`

**Done when:** Entities are auto-screened on creation, watchlist hits generate alerts, bulk import/export works.

---

## Stage 14 — F10: Network Graph Visualization

**Branch:** `feature/f10-network-graph-visualization`
**Assignee:**
**Depends on:** Stage 3B (transactions as edges), Stage 3A (entities as nodes), Stage 6 (risk scores for node coloring)
**Weeks:** 14–15

| Sub-task | Description |
|---|---|
| F10.1 | Interactive force-directed graph — entities as nodes, transactions as edges |
| F10.2 | Node size/color by risk score; edge thickness by transaction volume |
| F10.6 | Zoom, pan, and minimap navigation |
| F10.3 | Click-to-expand node neighborhoods |
| F10.4 | Filter graph by date range, amount range, risk level |
| F10.5 | Highlight suspicious clusters and fraud rings |

**Backend files:** `app/api/v1/network.py`, `app/services/network_analysis_service.py`, `app/ml/network_analyzer.py`
**Frontend files:** `src/app/(dashboard)/network-graph/page.tsx`, `src/components/network/graph-canvas.tsx`, `src/components/network/node-tooltip.tsx`, `src/components/network/graph-controls.tsx`

**Done when:** Network graph renders entities and transactions, nodes are colored by risk level, fraud ring clusters are highlighted.

---

## Stage 15 — F12: Audit Trail

**Branch:** `feature/f12-audit-trail`
**Assignee:**
**Depends on:** All previous stages (audit logs accumulate from all services; wire after services are stable)
**Weeks:** 15

> `audit_service.py` should be stubbed and called from Stage 8 onward. Stage 15 is when you build the viewer and wire all remaining service calls.

| Sub-task | Description |
|---|---|
| F12.1 | Log all user actions — login, data access, CRUD operations, config changes |
| F12.2 | Log all system actions — automated alert creation, model predictions, rule executions |
| F12.3 | Tamper-proof append-only log (no updates or deletes) |
| F12.4 | Audit log viewer — filters by user, action, resource, date range |
| F12.5 | Audit log export for compliance reporting |

**Backend files:** `app/api/v1/audit.py`, `app/services/audit_service.py`, `app/models/audit_log.py`
**Frontend files:** `src/app/(dashboard)/audit-log/page.tsx`

**Done when:** All services emit audit log entries. Viewer shows filterable, tamper-proof log. Export works.

---

## Stage 16 — F14: Settings & Configuration

**Branch:** `feature/f14-settings-configuration`
**Assignee:**
**Depends on:** All previous stages (you need to know what is configurable after building everything)
**Weeks:** 15–16

| Sub-task | Description |
|---|---|
| F14.1 | Risk score thresholds — configurable boundaries for low/medium/high/critical |
| F14.2 | Auto-block threshold — transactions above this fraud score are auto-blocked |
| F14.3 | Alert auto-assignment rules |
| F14.4 | Notification channel configuration |
| F14.5 | Data retention policies |
| F14.6 | API rate limiting configuration |
| F14.7 | Feature flags — enable/disable ML models, rules, integrations |

**Backend files:** `app/api/v1/settings.py`, `app/config.py`
**Frontend files:** `src/app/(dashboard)/settings/page.tsx`, `src/app/(dashboard)/settings/team/page.tsx`, `src/app/(dashboard)/settings/integrations/page.tsx`

**Done when:** Risk thresholds and feature flags are configurable at runtime without redeployment.

---

## Quick Reference: Development Sequence

| Stage | Branch | Feature | Weeks | Blocked by |
|---|---|---|---|---|
| 0 | *(scaffold on development)* | Foundation — config, models, schemas, migrations | 1 | — |
| 2 | `feature/f11-authentication-authorization` | F11 — Auth & RBAC | 1–3 | Stage 0 |
| 3A | `feature/f8-entity-management` | F8 Backend — Entity model + service | 4 | Stage 2 |
| 3B | `feature/f1-realtime-transaction-monitoring` | F1 Part A — Transaction REST ingestion | 4–5 | Stage 3A |
| 4 | `feature/f3-rules-engine` | F3 — Rules Engine | 5–6 | Stage 3B |
| 5 | `feature/f2-ml-fraud-detection` | F2 Part A — Feature Engineering + ML Models | 7–8 | Stage 3B (seed data) |
| 6 | `feature/f2-ml-fraud-detection` + `feature/f5-risk-scoring` | F2 pipeline wiring + F5 — Fraud Detection + Risk Scoring | 8–9 | Stages 4 + 5 |
| 7 | `feature/f1-realtime-transaction-monitoring` | F1 Part B — WebSocket + Event Hub Streaming | 9–10 | Stage 6 |
| 8 | `feature/f4-fraud-alert-management` | F4 — Fraud Alert Management | 10–11 | Stages 6 + 7 |
| 9 | `feature/f6-case-management` | F6 — Case Management | 11–12 | Stage 8 |
| 10 | `feature/f13-notifications-webhooks` | F13 — Notifications & Webhooks | 12 | Stages 8 + 9 |
| 11 | `feature/f7-analytics-reporting` | F7 — Analytics & Reporting | 13–14 | Stages 8 + 9 |
| 12 | `feature/f8-entity-management` | F8 Frontend — Entity 360 UI | 13–14 | Stages 8 + 9 + 6 |
| 13 | `feature/f9-watchlist-sanctions-screening` | F9 — Watchlist & Sanctions | 14 | Stage 12 |
| 14 | `feature/f10-network-graph-visualization` | F10 — Network Graph | 14–15 | Stages 3 + 6 |
| 15 | `feature/f12-audit-trail` | F12 — Audit Trail | 15 | All services stable |
| 16 | `feature/f14-settings-configuration` | F14 — Settings & Config | 15–16 | All previous |

---

## Key Dependency Rules (Do Not Violate)

| Rule | Reason |
|---|---|
| Entity backend (Stage 3A) before Transaction ingestion (Stage 3B) | `transactions.source_entity_id` is a FK → `entities.id`. Migration fails without entities. |
| Rules Engine (Stage 4) before Fraud Pipeline (Stage 6) | `fraud_detection_service.py` calls `rules_engine.evaluate()`. Rules must exist. |
| ML Models trained (Stage 5) before Pipeline wired (Stage 6) | Pipeline loads ONNX model files. Nothing to load if training hasn't run. |
| Fraud Pipeline (Stage 6) before WebSocket feed (Stage 7) | Live feed emits fraud-scored transactions. Stub scores make the feed useless. |
| Fraud Pipeline (Stage 6) before Alerts (Stage 8) | Alerts are created by `fraud_detection_service.py` as part of post-processing. |
| Alerts (Stage 8) before Cases (Stage 9) | Cases link to `alert_ids[]`. No alerts = no case content. |
| Alerts + Cases (Stages 8–9) before Analytics (Stage 11) | Dashboard charts query alerts and cases. Empty tables = empty charts. |
| Alerts + Cases + Risk Scores before Entity 360 UI (Stage 12) | Entity 360 aggregates alerts, cases, risk history. Build after all three exist. |

---

## Git Workflow for Contributors

```bash
# 1. Sync your local development branch
git checkout development
git pull origin development

# 2. Create your feature branch
git checkout -b feature/f<N>-<slug>

# 3. Work, commit using conventional commits
git commit -m "feat(f<N>): <description>"

# 4. Push and open PR targeting development
git push origin feature/f<N>-<slug>
# Open PR: feature/f<N>-<slug> → development
```

**PR Checklist:**
- [ ] CI passes (lint, type-check, tests)
- [ ] Coverage targets met (backend ≥80% unit, frontend ≥75% unit)
- [ ] At least 1 reviewer approval
- [ ] No secrets committed
- [ ] Conventional commit messages
