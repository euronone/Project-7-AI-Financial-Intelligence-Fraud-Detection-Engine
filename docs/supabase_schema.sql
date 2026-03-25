-- ============================================================
-- FinShield AI — Supabase Schema (Clean)
-- ============================================================
-- Run this in: Supabase Dashboard > SQL Editor
-- URL: https://supabase.com/dashboard/project/YOUR_PROJECT_REF/sql/new
--
-- Design:
--   - Cards are embedded directly in the customers table (no join needed)
--   - All NOT NULL columns have sensible defaults (no surprise NULLs)
--   - Transactions store card_last4 + card_network as denormalised columns
--   - 10 test customers have full card_number visible for demo testing
--
-- Tables:
--   1. tenants
--   2. users
--   3. customers          ← includes card details (no separate cards table)
--   4. transactions       ← card info denormalised from customer
--   5. fraud_alerts
--   6. fraud_rules
--   7. ml_models
--   8. investigation_cases
--   9. audit_logs
--
-- Views:
--   v_fraud_summary       ← transactions + customer + card + verdict
--   v_alert_queue         ← open alerts sorted by severity
-- ============================================================


-- ── 1. Tenants ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tenants (
  id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  organization_name TEXT    NOT NULL,
  institution_type  TEXT    NOT NULL DEFAULT 'bank',
  subscription_plan TEXT    NOT NULL DEFAULT 'free',
  is_active         BOOLEAN NOT NULL DEFAULT true,
  plan_started_at   TIMESTAMPTZ      DEFAULT NOW(),
  plan_expires_at   TIMESTAMPTZ,
  created_at        TIMESTAMPTZ      DEFAULT NOW(),
  updated_at        TIMESTAMPTZ      DEFAULT NOW()
);


-- ── 2. Users ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id                       TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id                TEXT    NOT NULL REFERENCES tenants(id),
  email                    TEXT    UNIQUE NOT NULL,
  full_name                TEXT    NOT NULL,
  hashed_password          TEXT    NOT NULL,
  phone_number             TEXT    NOT NULL DEFAULT '',
  role                     TEXT    NOT NULL DEFAULT 'analyst',
  is_active                BOOLEAN NOT NULL DEFAULT true,
  has_completed_onboarding BOOLEAN NOT NULL DEFAULT false,
  last_login_at            TIMESTAMPTZ,
  created_at               TIMESTAMPTZ DEFAULT NOW(),
  updated_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);


-- ── 3. Customers (card details embedded) ─────────────────────────────────────
--
-- Each customer row contains their primary card details directly.
-- No separate cards table — one row = one customer + their card.
--
-- card_number column:
--   • 10 test customers  → full visible number  e.g. "4111111111111111"
--   • All other customers → masked              e.g. "XXXX-XXXX-XXXX-1234"
--
CREATE TABLE IF NOT EXISTS customers (
  id                     TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id              TEXT    NOT NULL REFERENCES tenants(id),

  -- ── Identity ──────────────────────────────────────────────────────────────
  full_name              TEXT    NOT NULL,
  email                  TEXT    NOT NULL DEFAULT '',
  phone_number           TEXT    NOT NULL DEFAULT '',
  date_of_birth          DATE    NOT NULL DEFAULT '1990-01-01',

  -- ── Location ──────────────────────────────────────────────────────────────
  city                   TEXT    NOT NULL DEFAULT 'Mumbai',
  state_province         TEXT    NOT NULL DEFAULT 'Maharashtra',
  postal_code            TEXT    NOT NULL DEFAULT '400001',
  country_code           TEXT    NOT NULL DEFAULT 'IN',

  -- ── Account ───────────────────────────────────────────────────────────────
  account_type           TEXT    NOT NULL DEFAULT 'personal',
  account_opening_date   DATE    NOT NULL DEFAULT CURRENT_DATE,
  account_status         TEXT    NOT NULL DEFAULT 'active',
  kyc_status             TEXT    NOT NULL DEFAULT 'verified',
  kyc_verification_level TEXT    NOT NULL DEFAULT 'basic',

  -- ── Risk & Finance ────────────────────────────────────────────────────────
  risk_score             DECIMAL(5,4) NOT NULL DEFAULT 0.10,
  customer_tier          TEXT    NOT NULL DEFAULT 'standard',
  balance_amount         DECIMAL(18,2) NOT NULL DEFAULT 0.00,

  -- ── Card Details (primary card, embedded) ─────────────────────────────────
  -- card_number:
  --   test customers  → "4111111111111111"        (full, for Test Me tab)
  --   real customers  → "XXXX-XXXX-XXXX-1234"     (masked)
  card_number            TEXT    NOT NULL DEFAULT 'XXXX-XXXX-XXXX-0000',
  card_last4             TEXT    NOT NULL DEFAULT '0000',
  card_network           TEXT    NOT NULL DEFAULT 'Visa',
  card_cvv               TEXT    NOT NULL DEFAULT '000',
  card_expiry            TEXT    NOT NULL DEFAULT '12/2030',
  card_status            TEXT    NOT NULL DEFAULT 'active',
  card_token             TEXT    NOT NULL DEFAULT '',
  active_card_count      INTEGER NOT NULL DEFAULT 1,

  -- ── Segmentation ──────────────────────────────────────────────────────────
  profile_type           TEXT    NOT NULL DEFAULT 'standard_salaried',
  is_test_customer       BOOLEAN NOT NULL DEFAULT false,
  test_scenario          TEXT    NOT NULL DEFAULT '',
                         -- e.g. 'impossible_travel', 'velocity_fraud', ''

  created_at             TIMESTAMPTZ DEFAULT NOW(),
  updated_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_tenant   ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_customers_email    ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_risk     ON customers(risk_score);
CREATE INDEX IF NOT EXISTS idx_customers_tier     ON customers(customer_tier);
CREATE INDEX IF NOT EXISTS idx_customers_test     ON customers(is_test_customer);


-- ── 4. Transactions ───────────────────────────────────────────────────────────
--
-- card_last4 and card_network are copied from the customer at insert time
-- so every transaction row is self-contained (no JOIN needed for card info).
--
CREATE TABLE IF NOT EXISTS transactions (
  id                     TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id              TEXT    NOT NULL REFERENCES tenants(id),
  customer_id            TEXT    NOT NULL REFERENCES customers(id),

  -- ── Card used (denormalised from customer) ────────────────────────────────
  card_last4             TEXT    NOT NULL DEFAULT '0000',
  card_network           TEXT    NOT NULL DEFAULT 'Visa',

  -- ── Merchant ──────────────────────────────────────────────────────────────
  merchant_name          TEXT    NOT NULL DEFAULT 'Unknown',
  merchant_category_code TEXT    NOT NULL DEFAULT '5999',

  -- ── Amount ────────────────────────────────────────────────────────────────
  amount                 DECIMAL(18,2) NOT NULL,
  currency               TEXT    NOT NULL DEFAULT 'INR',

  -- ── Type & Channel ────────────────────────────────────────────────────────
  transaction_type       TEXT    NOT NULL DEFAULT 'purchase',
  channel                TEXT    NOT NULL DEFAULT 'online',

  -- ── Location (DOUBLE PRECISION — handles all global longitudes) ───────────
  location_lat           DOUBLE PRECISION NOT NULL DEFAULT 19.0760,
  location_lng           DOUBLE PRECISION NOT NULL DEFAULT 72.8777,
  city                   TEXT    NOT NULL DEFAULT 'Mumbai',
  country_code           TEXT    NOT NULL DEFAULT 'IN',

  -- ── Device ────────────────────────────────────────────────────────────────
  ip_address             TEXT    NOT NULL DEFAULT '0.0.0.0',
  device_fingerprint     TEXT    NOT NULL DEFAULT '',
  device_type            TEXT    NOT NULL DEFAULT 'mobile',

  -- ── Status ────────────────────────────────────────────────────────────────
  status                 TEXT    NOT NULL DEFAULT 'completed',

  -- ── FinShield Fraud Fields ────────────────────────────────────────────────
  fraud_score            DECIMAL(5,4) NOT NULL DEFAULT 0.0,
  fraud_risk_level       TEXT    NOT NULL DEFAULT 'low',
  fraud_category         TEXT    NOT NULL DEFAULT 'unscored',
  is_flagged             BOOLEAN NOT NULL DEFAULT false,
  is_blocked             BOOLEAN NOT NULL DEFAULT false,
  is_test                BOOLEAN NOT NULL DEFAULT false,
  model_version          TEXT    NOT NULL DEFAULT 'ensemble_v1',
  triggered_rule_ids     JSONB   NOT NULL DEFAULT '[]',
  fraud_scored_at        TIMESTAMPTZ      DEFAULT NOW(),

  transaction_timestamp  TIMESTAMPTZ NOT NULL,
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_txn_tenant      ON transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_txn_customer    ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_timestamp   ON transactions(transaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_txn_fraud_cat   ON transactions(fraud_category);
CREATE INDEX IF NOT EXISTS idx_txn_fraud_score ON transactions(fraud_score);
CREATE INDEX IF NOT EXISTS idx_txn_is_flagged  ON transactions(is_flagged);
CREATE INDEX IF NOT EXISTS idx_txn_is_test     ON transactions(is_test);


-- ── 5. Fraud Alerts ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fraud_alerts (
  id               TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id        TEXT    NOT NULL REFERENCES tenants(id),
  transaction_id   TEXT    NOT NULL REFERENCES transactions(id),
  customer_id      TEXT    NOT NULL REFERENCES customers(id),
  alert_type       TEXT    NOT NULL DEFAULT 'ml_model',
  severity         TEXT    NOT NULL DEFAULT 'medium',
  status           TEXT    NOT NULL DEFAULT 'open',
  analyst_id       TEXT    REFERENCES users(id),
  resolution_notes TEXT    NOT NULL DEFAULT '',
  is_confirmed     BOOLEAN NOT NULL DEFAULT false,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  resolved_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_tenant   ON fraud_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status   ON fraud_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON fraud_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_customer ON fraud_alerts(customer_id);


-- ── 6. Fraud Rules ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fraud_rules (
  id                  TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id           TEXT    NOT NULL REFERENCES tenants(id),
  rule_name           TEXT    NOT NULL,
  rule_category       TEXT    NOT NULL DEFAULT 'velocity',
  description         TEXT    NOT NULL DEFAULT '',
  conditions          JSONB   NOT NULL DEFAULT '{}',
  threshold           DECIMAL(10,2)    DEFAULT 0,
  action              TEXT    NOT NULL DEFAULT 'flag',
  severity            TEXT    NOT NULL DEFAULT 'medium',
  is_active           BOOLEAN NOT NULL DEFAULT true,
  priority            INTEGER NOT NULL DEFAULT 100,
  false_positive_rate DECIMAL(5,4)     DEFAULT 0,
  hit_rate            DECIMAL(5,4)     DEFAULT 0,
  total_triggers      INTEGER NOT NULL DEFAULT 0,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rules_tenant   ON fraud_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rules_active   ON fraud_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_rules_category ON fraud_rules(rule_category);


-- ── 7. ML Models ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ml_models (
  id                  TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id           TEXT    REFERENCES tenants(id),
  model_name          TEXT    NOT NULL,
  model_type          TEXT    NOT NULL DEFAULT 'ensemble',
  version             TEXT    NOT NULL,
  status              TEXT    NOT NULL DEFAULT 'training',
  precision           DECIMAL(5,4) DEFAULT 0,
  recall              DECIMAL(5,4) DEFAULT 0,
  f1_score            DECIMAL(5,4) DEFAULT 0,
  auc_roc             DECIMAL(5,4) DEFAULT 0,
  false_positive_rate DECIMAL(5,4) DEFAULT 0,
  training_samples    INTEGER      DEFAULT 0,
  artifact_path       TEXT    NOT NULL DEFAULT '',
  feature_importance  JSONB        DEFAULT '{}',
  is_active           BOOLEAN NOT NULL DEFAULT false,
  promoted_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_models_tenant ON ml_models(tenant_id);
CREATE INDEX IF NOT EXISTS idx_models_active ON ml_models(is_active);


-- ── 8. Investigation Cases ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigation_cases (
  id                     TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id              TEXT    NOT NULL REFERENCES tenants(id),
  alert_id               TEXT    NOT NULL REFERENCES fraud_alerts(id),
  customer_id            TEXT    NOT NULL REFERENCES customers(id),
  assigned_to            TEXT    REFERENCES users(id),
  case_number            TEXT    UNIQUE NOT NULL,
  title                  TEXT    NOT NULL,
  description            TEXT    NOT NULL DEFAULT '',
  status                 TEXT    NOT NULL DEFAULT 'open',
  priority               TEXT    NOT NULL DEFAULT 'medium',
  outcome                TEXT    NOT NULL DEFAULT '',
  notes                  JSONB   NOT NULL DEFAULT '[]',
  linked_transaction_ids JSONB   NOT NULL DEFAULT '[]',
  created_at             TIMESTAMPTZ DEFAULT NOW(),
  resolved_at            TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cases_tenant   ON investigation_cases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cases_status   ON investigation_cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_customer ON investigation_cases(customer_id);


-- ── 9. Audit Logs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
  id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id     TEXT NOT NULL REFERENCES tenants(id),
  user_id       TEXT REFERENCES users(id),
  action        TEXT NOT NULL,
  resource_type TEXT NOT NULL DEFAULT '',
  resource_id   TEXT NOT NULL DEFAULT '',
  old_value     JSONB         DEFAULT '{}',
  new_value     JSONB         DEFAULT '{}',
  ip_address    TEXT NOT NULL DEFAULT '0.0.0.0',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant   ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_user     ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);


-- ══════════════════════════════════════════════════════════════════════════════
-- VIEWS
-- ══════════════════════════════════════════════════════════════════════════════

-- ── v_fraud_summary ───────────────────────────────────────────────────────────
-- Every transaction with customer name + card number + fraud verdict in one row.
-- Frontend can query: GET /rest/v1/v_fraud_summary?fraud_category=eq.fraudulent
CREATE OR REPLACE VIEW v_fraud_summary AS
SELECT
  t.id                   AS transaction_id,
  t.transaction_timestamp,
  -- Customer
  c.full_name            AS customer_name,
  c.email                AS customer_email,
  c.phone_number         AS customer_phone,
  c.risk_score           AS customer_risk_score,
  c.customer_tier,
  c.is_test_customer,
  c.test_scenario,
  -- Card (from customer row — no join to separate table)
  c.card_number,
  c.card_last4,
  c.card_network,
  c.card_cvv,
  c.card_expiry,
  c.card_status          AS card_status,
  -- Transaction
  t.amount,
  t.currency,
  t.merchant_name,
  t.merchant_category_code,
  t.channel,
  t.city                 AS txn_city,
  t.country_code,
  t.device_type,
  t.status               AS txn_status,
  -- Fraud verdict
  t.fraud_score,
  t.fraud_risk_level,
  t.fraud_category,
  t.is_flagged,
  t.is_blocked,
  t.is_test,
  t.triggered_rule_ids,
  t.model_version
FROM transactions t
JOIN customers c ON c.id = t.customer_id;


-- ── v_alert_queue ─────────────────────────────────────────────────────────────
-- Open + under_review alerts sorted by severity for the analyst queue.
CREATE OR REPLACE VIEW v_alert_queue AS
SELECT
  a.id              AS alert_id,
  a.created_at      AS alerted_at,
  a.severity,
  a.status,
  a.alert_type,
  a.is_confirmed,
  -- Customer + card
  c.full_name       AS customer_name,
  c.phone_number    AS customer_phone,
  c.risk_score      AS customer_risk_score,
  c.card_number,
  c.card_network,
  c.is_test_customer,
  -- Transaction
  t.amount,
  t.currency,
  t.merchant_name,
  t.channel,
  t.city            AS txn_city,
  t.fraud_score,
  t.fraud_category,
  t.triggered_rule_ids
FROM fraud_alerts a
JOIN customers   c ON c.id = a.customer_id
JOIN transactions t ON t.id = a.transaction_id
WHERE a.status IN ('open', 'under_review')
ORDER BY
  CASE a.severity
    WHEN 'critical' THEN 1
    WHEN 'high'     THEN 2
    WHEN 'medium'   THEN 3
    ELSE 4
  END,
  a.created_at DESC;


-- ══════════════════════════════════════════════════════════════════════════════
-- SEED — demo tenant (safe to re-run, skips if tenant already exists)
-- ══════════════════════════════════════════════════════════════════════════════
INSERT INTO tenants (id, organization_name, institution_type, subscription_plan, is_active)
SELECT gen_random_uuid()::text, 'FinShield Demo Bank', 'bank', 'pro', true
WHERE NOT EXISTS (SELECT 1 FROM tenants LIMIT 1);


-- ══════════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (uncomment to enable multi-tenant isolation)
-- ══════════════════════════════════════════════════════════════════════════════
-- ALTER TABLE customers    ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY tenant_isolation ON transactions
--   USING (tenant_id = current_setting('app.current_tenant_id')::text);
-- CREATE POLICY tenant_isolation ON customers
--   USING (tenant_id = current_setting('app.current_tenant_id')::text);
