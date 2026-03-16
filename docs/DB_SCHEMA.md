# FinShield AI — Database Schema

**Database:** PostgreSQL 16 (Azure Database for PostgreSQL Flexible Server)  
**ORM:** SQLAlchemy 2.0 (async)  
**Migrations:** Alembic  

This document summarizes the core tables. Implement with Alembic migrations; align ORM models and repositories with this schema. Partitioning: `transactions` by `processed_at` (monthly), `audit_logs` by `created_at` (monthly).

---

## users

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| role | ENUM('admin','analyst','investigator','viewer') | NOT NULL, default 'viewer' |
| is_active | BOOLEAN | default TRUE |
| mfa_enabled | BOOLEAN | default FALSE |
| mfa_secret | VARCHAR(255) | NULLABLE |
| last_login_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## transactions

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| external_id | VARCHAR(255) | UNIQUE, NOT NULL |
| source_entity_id | UUID | FK → entities(id) |
| destination_entity_id | UUID | FK → entities(id), NULLABLE |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL (ISO 4217) |
| transaction_type | ENUM('payment','transfer','withdrawal','deposit','refund') | NOT NULL |
| channel | ENUM('online','pos','atm','mobile','wire','ach') | NOT NULL |
| status | ENUM('pending','completed','failed','reversed','flagged','blocked') | NOT NULL |
| merchant_category_code | VARCHAR(4) | NULLABLE |
| description | TEXT | NULLABLE |
| ip_address | INET | NULLABLE |
| device_fingerprint | VARCHAR(255) | NULLABLE |
| geolocation_lat | DECIMAL(10,7) | NULLABLE |
| geolocation_lng | DECIMAL(10,7) | NULLABLE |
| country_code | VARCHAR(2) | NULLABLE |
| card_present | BOOLEAN | NULLABLE |
| fraud_score | DECIMAL(5,4) | NULLABLE (0.0000–1.0000) |
| risk_level | ENUM('low','medium','high','critical') | NULLABLE |
| processed_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | default NOW() |

**Indexes:** source_entity_id, processed_at, fraud_score, status, external_id. **Partitioning:** by processed_at (monthly).

---

## entities

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| external_id | VARCHAR(255) | UNIQUE |
| entity_type | ENUM('individual','business','merchant') | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NULLABLE |
| phone | VARCHAR(50) | NULLABLE |
| country_code | VARCHAR(2) | NULLABLE |
| risk_score | DECIMAL(5,4) | default 0.0000 |
| risk_level | ENUM('low','medium','high','critical') | default 'low' |
| is_watchlisted | BOOLEAN | default FALSE |
| kyc_status | ENUM('pending','verified','rejected','expired') | default 'pending' |
| metadata | JSONB | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## fraud_alerts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| transaction_id | UUID | FK → transactions(id) |
| entity_id | UUID | FK → entities(id), NULLABLE |
| alert_type | ENUM('ml_detection','rule_trigger','manual','watchlist_match','anomaly','velocity') | NOT NULL |
| severity | ENUM('low','medium','high','critical') | NOT NULL |
| status | ENUM('open','investigating','escalated','resolved_fraud','resolved_false_positive','dismissed') | NOT NULL, default 'open' |
| title | VARCHAR(500) | NOT NULL |
| description | TEXT | NOT NULL |
| confidence_score | DECIMAL(5,4) | NULLABLE |
| rule_id | UUID | FK → rules(id), NULLABLE |
| model_id | UUID | FK → ml_models(id), NULLABLE |
| evidence | JSONB | NULLABLE |
| assigned_to | UUID | FK → users(id), NULLABLE |
| resolved_by | UUID | FK → users(id), NULLABLE |
| resolved_at | TIMESTAMPTZ | NULLABLE |
| resolution_notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## rules

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | NULLABLE |
| category | ENUM('velocity','amount','geography','pattern','device','custom') | NOT NULL |
| conditions | JSONB | NOT NULL |
| actions | JSONB | NOT NULL |
| severity | ENUM('low','medium','high','critical') | NOT NULL |
| is_active | BOOLEAN | default TRUE |
| priority | INTEGER | default 100 |
| hit_count | BIGINT | default 0 |
| false_positive_rate | DECIMAL(5,4) | NULLABLE |
| created_by | UUID | FK → users(id) |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## cases

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| case_number | VARCHAR(50) | UNIQUE, NOT NULL (e.g. CASE-YYYYMMDD-XXXX) |
| title | VARCHAR(500) | NOT NULL |
| description | TEXT | NULLABLE |
| status | ENUM('open','in_progress','pending_review','escalated','closed_confirmed_fraud','closed_false_positive') | NOT NULL |
| priority | ENUM('low','medium','high','critical') | NOT NULL |
| assigned_to | UUID | FK → users(id), NULLABLE |
| total_amount_at_risk | DECIMAL(18,4) | NULLABLE |
| alert_ids | UUID[] | Array of alert IDs |
| timeline | JSONB | Array of timeline events |
| findings | TEXT | NULLABLE |
| created_by | UUID | FK → users(id) |
| closed_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## risk_scores

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| entity_id | UUID | FK → entities(id) |
| transaction_id | UUID | FK → transactions(id), NULLABLE |
| overall_score | DECIMAL(5,4) | NOT NULL |
| component_scores | JSONB | NOT NULL |
| risk_factors | JSONB | NOT NULL |
| model_version | VARCHAR(50) | NOT NULL |
| explanation | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

---

## ml_models

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| model_type | ENUM('fraud_classifier','anomaly_detector','risk_scorer','behavioral_profiler') | NOT NULL |
| version | VARCHAR(50) | NOT NULL |
| status | ENUM('training','validating','active','retired','failed') | NOT NULL |
| framework | VARCHAR(50) | NOT NULL |
| metrics | JSONB | NOT NULL |
| parameters | JSONB | NULLABLE |
| artifact_path | VARCHAR(500) | NOT NULL |
| training_dataset_info | JSONB | NULLABLE |
| promoted_at | TIMESTAMPTZ | NULLABLE |
| promoted_by | UUID | FK → users(id), NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

**UNIQUE:** (name, version)

---

## watchlists

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| list_name | VARCHAR(255) | NOT NULL |
| list_type | ENUM('sanctions','pep','adverse_media','internal_blacklist','custom') | NOT NULL |
| entity_name | VARCHAR(500) | NOT NULL |
| entity_identifiers | JSONB | NOT NULL |
| source | VARCHAR(255) | NOT NULL |
| match_score | DECIMAL(5,4) | NULLABLE |
| is_active | BOOLEAN | default TRUE |
| expires_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |
| updated_at | TIMESTAMPTZ | default NOW() |

---

## audit_logs

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users(id), NULLABLE |
| action | VARCHAR(100) | NOT NULL |
| resource_type | VARCHAR(100) | NOT NULL |
| resource_id | UUID | NULLABLE |
| details | JSONB | NULLABLE |
| ip_address | INET | NULLABLE |
| user_agent | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

**Partitioning:** by created_at (monthly).

---

## notifications

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| type | ENUM('fraud_alert','case_update','system','rule_trigger','model_update') | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | default FALSE |
| metadata | JSONB | NULLABLE |
| created_at | TIMESTAMPTZ | default NOW() |

---

## webhooks

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| url | VARCHAR(2048) | NOT NULL |
| events | VARCHAR[] | NOT NULL |
| secret | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | default TRUE |
| last_triggered_at | TIMESTAMPTZ | NULLABLE |
| failure_count | INTEGER | default 0 |
| created_by | UUID | FK → users(id) |
| created_at | TIMESTAMPTZ | default NOW() |

---

*For ORM definitions and repositories see backend/app/models/ and backend/app/db/.*
