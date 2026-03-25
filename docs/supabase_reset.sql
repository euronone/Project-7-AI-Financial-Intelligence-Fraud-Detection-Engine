-- ============================================================
-- FinShield AI — Supabase Reset
-- ============================================================
-- Run this BEFORE supabase_schema.sql to drop all old tables.
-- ⚠️  This deletes all existing data — only use for fresh setup.
--
-- Step 1: Paste this entire file into Supabase SQL Editor → Run
-- Step 2: Then paste and run docs/supabase_schema.sql
-- ============================================================

-- Drop views first (they reference tables)
DROP VIEW IF EXISTS v_alert_queue CASCADE;
DROP VIEW IF EXISTS v_fraud_summary CASCADE;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS audit_logs             CASCADE;
DROP TABLE IF EXISTS investigation_cases    CASCADE;
DROP TABLE IF EXISTS ml_models              CASCADE;
DROP TABLE IF EXISTS fraud_rules            CASCADE;
DROP TABLE IF EXISTS fraud_alerts           CASCADE;
DROP TABLE IF EXISTS transactions           CASCADE;
DROP TABLE IF EXISTS cards                  CASCADE;  -- old separate cards table (if it existed)
DROP TABLE IF EXISTS customers              CASCADE;
DROP TABLE IF EXISTS users                  CASCADE;
DROP TABLE IF EXISTS tenants                CASCADE;

-- Confirm
SELECT 'Reset complete — ready to run supabase_schema.sql' AS status;
