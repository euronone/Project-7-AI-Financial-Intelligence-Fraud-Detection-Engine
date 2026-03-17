# FinShield AI — Feature Task Assignments

> Each feature maps to a dedicated branch off `development`. Branch naming follows the convention: `feature/<feature-id>-<slug>`.
> Assignees column is intentionally blank — fill in contributor GitHub handles before distribution.


---

## Branch Strategy

```
main
└── development
    ├── feature/f1-realtime-transaction-monitoring
    ├── feature/f2-ml-fraud-detection
    ├── feature/f3-rules-engine
    ├── feature/f4-fraud-alert-management
    ├── feature/f5-risk-scoring
    ├── feature/f6-case-management
    ├── feature/f7-analytics-reporting
    ├── feature/f8-entity-management
    ├── feature/f9-watchlist-sanctions-screening
    ├── feature/f10-network-graph-visualization
    ├── feature/f11-authentication-authorization
    ├── feature/f12-audit-trail
    ├── feature/f13-notifications-webhooks
    └── feature/f14-settings-configuration
```

All PRs must target `development`. CI must pass before merge. Requires at least 1 reviewer approval.

---

## Feature Tasks

### F1 — Real-Time Transaction Monitoring
**Branch:** `feature/f1-realtime-transaction-monitoring`
**Assignee:**
**Phase:** 2 (Weeks 4–6)

| Sub-task | Description |
|---|---|
| F1.1 | Transaction ingestion via REST API and Azure Event Hubs (Kafka protocol) |
| F1.2 | Fraud detection pipeline processing with <200ms P95 latency |
| F1.3 | Live transaction feed on dashboard via WebSocket auto-refresh |
| F1.4 | Batch ingestion support (up to 10,000 transactions per request) |
| F1.5 | Transaction search: full-text, date range, amount, entity, status, risk level, channel, geography filters |
| F1.6 | Transaction detail view: raw data, fraud score breakdown, risk factors, linked alerts, similar transactions, entity context |
| F1.7 | Export transactions to CSV and JSON with applied filters |

**Backend files:** `app/api/v1/transactions.py`, `app/services/transaction_service.py`, `app/streaming/consumer.py`, `app/streaming/processor.py`
**Frontend files:** `src/app/(dashboard)/transactions/`, `src/components/transactions/`, `src/hooks/use-transactions.ts`

---

### F2 — ML-Powered Fraud Detection
**Branch:** `feature/f2-ml-fraud-detection`
**Assignee:**
**Phase:** 3 (Weeks 7–9)

| Sub-task | Description |
|---|---|
| F2.1 | Fraud Classifier — XGBoost + Neural Network ensemble, outputs fraud probability (0.0–1.0) |
| F2.2 | Anomaly Detection — Isolation Forest + Autoencoder for statistical outliers |
| F2.3 | Behavioral Profiling — per-entity baselines with configurable deviation thresholds |
| F2.4 | Network Analysis — graph-based fraud ring detection via connected components and centrality |
| F2.5 | Feature Engineering — extract 200+ features (transaction, temporal, velocity, entity, geographic, device, behavioral, network, derived) |
| F2.6 | Model Explainability — SHAP values per prediction, top contributing features on alert detail |
| F2.7 | Model Registry — version, track, promote, retire models; compare metrics (accuracy, precision, recall, F1, AUC-ROC, AUC-PR) |
| F2.8 | Automated Retraining — trigger on performance degradation; feedback loop from resolved alerts |
| F2.9 | ONNX Runtime inference pipeline for sub-10ms production serving |

**Backend files:** `app/ml/`, `app/ml/training/`, `app/services/ml_service.py`, `app/services/fraud_detection_service.py`
**Frontend files:** `src/app/(dashboard)/ml-models/`, `src/components/charts/model-performance-chart.tsx`

---

### F3 — Rules Engine
**Branch:** `feature/f3-rules-engine`
**Assignee:**
**Phase:** 2 (Weeks 4–6)

| Sub-task | Description |
|---|---|
| F3.1 | Visual rule builder UI with drag-and-drop condition grouping (AND/OR logic) |
| F3.2 | Condition types: amount thresholds, velocity checks, geographic, time-based, entity attributes, device/IP, pattern, custom field |
| F3.3 | Actions: block transaction, flag for review, adjust risk score, create alert, notify team, trigger webhook |
| F3.4 | Rule testing — dry-run against historical transactions to estimate hit rate and false positive rate |
| F3.5 | Rule templates — pre-built rules for card testing, account takeover, money mules, first-party fraud |
| F3.6 | Rule priority and execution order configuration |
| F3.7 | Rule performance dashboard — hit counts, false positive rates, trend over time |

**Backend files:** `app/rules/`, `app/api/v1/rules.py`, `app/services/rules_engine_service.py`
**Frontend files:** `src/app/(dashboard)/rules-engine/`, `src/components/rules/`

---

### F4 — Fraud Alert Management
**Branch:** `feature/f4-fraud-alert-management`
**Assignee:**
**Phase:** 4 (Weeks 10–12)

| Sub-task | Description |
|---|---|
| F4.1 | Alert list view — filters by status, severity, type, date, assigned analyst |
| F4.2 | Alert detail view — transaction details, SHAP explanation, rule matches, entity risk profile, historical alerts, similar patterns, evidence panel |
| F4.3 | Alert workflow: Open → Investigating → Escalated → Resolved (Confirmed Fraud / False Positive) / Dismissed |
| F4.4 | Alert assignment to analysts with workload balancing visibility |
| F4.5 | Bulk actions: bulk assign, bulk resolve, bulk dismiss |
| F4.6 | Alert escalation with reason and notification to senior analysts |
| F4.7 | Resolution notes — mandatory for confirmed fraud, optional for false positive |
| F4.8 | Create investigation case from one or more related alerts |
| F4.9 | Real-time alert notifications via WebSocket, email, and SMS (configurable per severity) |

**Backend files:** `app/api/v1/fraud_alerts.py`, `app/services/fraud_detection_service.py`, `app/streaming/websocket_manager.py`
**Frontend files:** `src/app/(dashboard)/fraud-alerts/`, `src/components/fraud/`

---

### F5 — Risk Scoring
**Branch:** `feature/f5-risk-scoring`
**Assignee:**
**Phase:** 3 (Weeks 7–9)

| Sub-task | Description |
|---|---|
| F5.1 | Composite risk score (0.0–1.0) combining ML output, rule triggers, behavioral deviation, entity history, watchlist matches |
| F5.2 | Risk level classification: Low (0–0.3), Medium (0.3–0.6), High (0.6–0.8), Critical (0.8–1.0) — configurable thresholds |
| F5.3 | Component score breakdown: ML score, rule score, velocity score, behavioral score, network score |
| F5.4 | Risk score history per entity with trend visualization |
| F5.5 | Risk distribution dashboard — entity count per risk tier |
| F5.6 | Top-N highest risk entities leaderboard |
| F5.7 | Risk score auto-updates on new transaction, alert resolution, or watchlist match |

**Backend files:** `app/api/v1/risk_scoring.py`, `app/services/risk_scoring_service.py`, `app/ml/risk_scorer.py`
**Frontend files:** `src/app/(dashboard)/risk-scoring/`, `src/components/charts/risk-distribution-chart.tsx`

---

### F6 — Case Management
**Branch:** `feature/f6-case-management`
**Assignee:**
**Phase:** 4 (Weeks 10–12)

| Sub-task | Description |
|---|---|
| F6.1 | Create cases manually or from fraud alerts (one or more alerts per case) |
| F6.2 | Case detail — linked alerts, transactions, entities, and evidence |
| F6.3 | Case timeline — chronological log of all actions and events |
| F6.4 | Case assignment and reassignment |
| F6.5 | Case status workflow: Open → In Progress → Pending Review → Escalated → Closed (Confirmed Fraud / False Positive) |
| F6.6 | Case findings and resolution notes (structured form + free text) |
| F6.7 | Case statistics — open/closed counts, average resolution time, confirmed fraud rate |

**Backend files:** `app/api/v1/cases.py`, `app/services/case_service.py`, `app/models/case.py`, `app/schemas/case.py`
**Frontend files:** `src/app/(dashboard)/case-management/`, `src/hooks/use-analytics.ts`

---

### F7 — Analytics & Reporting
**Branch:** `feature/f7-analytics-reporting`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

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
**Frontend files:** `src/app/(dashboard)/analytics/`, `src/components/charts/`, `src/components/dashboard/`

---

### F8 — Entity Management (Customer/Merchant 360)
**Branch:** `feature/f8-entity-management`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

| Sub-task | Description |
|---|---|
| F8.1 | Entity list — search, filter by type, risk level, KYC status, watchlist status |
| F8.2 | Entity 360 view — profile info, risk score breakdown, transaction history, alerts, cases, behavioral profile, network connections |
| F8.3 | Entity risk profile — historical risk scores, contributing factors, trend |
| F8.4 | Entity transaction pattern visualization — amount distribution, time patterns, geographic spread |
| F8.5 | Entity network graph — connections to other entities via transactions |
| F8.6 | Watchlist screening with match scoring |

**Backend files:** `app/api/v1/entities.py`, `app/services/entity_service.py`, `app/models/entity.py`
**Frontend files:** `src/app/(dashboard)/entities/`, `src/types/entity.ts`

---

### F9 — Watchlist & Sanctions Screening
**Branch:** `feature/f9-watchlist-sanctions-screening`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

| Sub-task | Description |
|---|---|
| F9.1 | Manage internal watchlists (blacklist, greylist) |
| F9.2 | Integration with external sanctions lists (OFAC, UN, EU) |
| F9.3 | Fuzzy name matching with configurable match threshold |
| F9.4 | Bulk screening of entity database |
| F9.5 | Automatic screening on new entity creation or transaction |
| F9.6 | Watchlist hit alerts with match details and confidence score |
| F9.7 | CSV import/export for watchlist management |

**Backend files:** `app/api/v1/watchlists.py`, `app/services/watchlist_service.py`, `app/integrations/sanctions_api.py`
**Frontend files:** `src/app/(dashboard)/watchlists/`

---

### F10 — Network Graph Visualization
**Branch:** `feature/f10-network-graph-visualization`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

| Sub-task | Description |
|---|---|
| F10.1 | Interactive force-directed graph — entities as nodes, transactions as edges |
| F10.2 | Node size/color by risk score; edge thickness by transaction volume |
| F10.3 | Click-to-expand node neighborhoods |
| F10.4 | Filter graph by date range, amount range, risk level |
| F10.5 | Highlight suspicious clusters and fraud rings |
| F10.6 | Zoom, pan, and minimap navigation |

**Backend files:** `app/api/v1/network.py`, `app/services/network_analysis_service.py`, `app/ml/network_analyzer.py`
**Frontend files:** `src/app/(dashboard)/network-graph/`, `src/components/network/`

---

### F11 — Authentication & Authorization
**Branch:** `feature/f11-authentication-authorization`
**Assignee:**
**Phase:** 1 (Weeks 1–3)

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

**Backend files:** `app/api/v1/auth.py`, `app/core/security.py`, `app/core/permissions.py`
**Frontend files:** `src/app/(auth)/`, `src/lib/auth.ts`, `src/hooks/use-auth.ts`, `src/stores/auth-store.ts`

---

### F12 — Audit Trail
**Branch:** `feature/f12-audit-trail`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

| Sub-task | Description |
|---|---|
| F12.1 | Log all user actions — login, data access, CRUD operations, config changes |
| F12.2 | Log all system actions — automated alert creation, model predictions, rule executions |
| F12.3 | Tamper-proof append-only log (no updates or deletes) |
| F12.4 | Audit log viewer — filters by user, action, resource, date range |
| F12.5 | Audit log export for compliance reporting |

**Backend files:** `app/api/v1/audit.py`, `app/services/audit_service.py`, `app/models/audit_log.py`
**Frontend files:** `src/app/(dashboard)/audit-log/`

---

### F13 — Notifications & Webhooks
**Branch:** `feature/f13-notifications-webhooks`
**Assignee:**
**Phase:** 4 (Weeks 10–12)

| Sub-task | Description |
|---|---|
| F13.1 | In-app notification center with unread badge and mark-as-read |
| F13.2 | Email notifications for critical and high severity alerts |
| F13.3 | SMS notifications for critical alerts (configurable) |
| F13.4 | Webhook support for external system integration (Slack, PagerDuty, SIEM) |
| F13.5 | Notification preferences per user (events and channels) |
| F13.6 | Webhook retry with exponential backoff (max 5 retries) |
| F13.7 | Webhook HMAC signature verification |

**Backend files:** `app/api/v1/webhooks.py`, `app/services/notification_service.py`, `app/services/webhook_service.py`, `app/integrations/email_service.py`, `app/integrations/sms_service.py`
**Frontend files:** `src/app/(dashboard)/settings/notifications/`, `src/app/(dashboard)/settings/api-keys/`

---

### F14 — Settings & Configuration
**Branch:** `feature/f14-settings-configuration`
**Assignee:**
**Phase:** 5 (Weeks 13–15)

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
**Frontend files:** `src/app/(dashboard)/settings/`, `src/app/(dashboard)/settings/team/`, `src/app/(dashboard)/settings/integrations/`

---

## Quick Reference: Branch → Phase Mapping

| Branch | Feature | Phase | Weeks |
|---|---|---|---|
| `feature/f11-authentication-authorization` | Auth & RBAC | 1 | 1–3 |
| `feature/f1-realtime-transaction-monitoring` | Transaction Monitoring | 2 | 4–6 |
| `feature/f3-rules-engine` | Rules Engine | 2 | 4–6 |
| `feature/f2-ml-fraud-detection` | ML Fraud Detection | 3 | 7–9 |
| `feature/f5-risk-scoring` | Risk Scoring | 3 | 7–9 |
| `feature/f4-fraud-alert-management` | Alert Management | 4 | 10–12 |
| `feature/f6-case-management` | Case Management | 4 | 10–12 |
| `feature/f13-notifications-webhooks` | Notifications & Webhooks | 4 | 10–12 |
| `feature/f7-analytics-reporting` | Analytics & Reporting | 5 | 13–15 |
| `feature/f8-entity-management` | Entity Management | 5 | 13–15 |
| `feature/f9-watchlist-sanctions-screening` | Watchlist Screening | 5 | 13–15 |
| `feature/f10-network-graph-visualization` | Network Graph | 5 | 13–15 |
| `feature/f12-audit-trail` | Audit Trail | 5 | 13–15 |
| `feature/f14-settings-configuration` | Settings & Config | 5 | 13–15 |

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
