# Database Schema

## Core Tables
- `users`: System users (admins, analysts, investigators)
- `transactions`: Financial transactions (partitioned by month)
- `entities`: Individuals, businesses, or merchants
- `fraud_alerts`: Generated alerts for suspicious activity
- `rules`: Configurable fraud detection rules
- `cases`: Investigation cases linking alerts and transactions
- `risk_scores`: Entity and transaction risk profiles
- `ml_models`: Model registry and metrics
- `watchlists`: Sanctions and internal blacklists
- `audit_logs`: Immutable system and user action logs (partitioned)
- `notifications`: User alerts and messages
- `webhooks`: Configured external webhooks

## Core Rules
- **Primary Keys:** All tables use UUIDs (`gen_random_uuid()`).
- **Timestamps:** All major tables include `created_at` and `updated_at` (TIMESTAMPTZ).
- **Enums:** Use ENUM types for finite states (e.g., `status`, `risk_level`, `alert_type`).
- **Partitioning:** High-volume tables (`transactions`, `audit_logs`) use range partitioning by date (monthly).
- **Auditability:** All user actions and system decisions must be logged in `audit_logs`.
- **Soft Deletes:** Use soft deletes where data retention is required for compliance (e.g., `is_active` flags on rules and models).
