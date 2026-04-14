# Settings ⇄ Other Windows — Backend Connection Audit

Date: 2026-04-14
Scope: backend only — traces every path from `Settings` (DB, Integrations, Notifications, Plan, Schema Mapping) to where those values are actually consumed, and flags the fragile joints.

---

## 1. End-to-end map

```
  ┌───────────────────────────┐            ┌─────────────────────────────┐
  │  POST /auth/signup        │──writes──▶ │ tenants.db_config_json      │
  │  (institution + user)     │            │   .notifications            │
  └───────────────────────────┘            │     company_alert_email     │
                                           │     sms_enabled             │
                                           │     email_customer/company  │
                                           └─────────────────────────────┘
                                                      ▲
           ┌──────────────────────────────────────────┼──────────────┐
           │                                          │              │
  PUT /settings/notifications          PUT /credentials (BYOK)   ENV vars
           │                                          │              │
           ▼                                          ▼              ▼
  ┌───────────────────────────────────────────────────────────────────┐
  │ Alert dispatch: fraud_detection_service._notify_and_broadcast()   │
  │   → pre-fetches BYOK keys for resend / brevo / twilio             │
  │   → notification_service.send_fraud_alert_notifications()         │
  │     → _send_email()  (Resend → Brevo fallback)                   │
  │     → _send_twilio_sms()                                          │
  └───────────────────────────────────────────────────────────────────┘
           ▲                                          ▲
  /simulator Test Me calls ──────────────────────────┘
  (resolves creds via _resolve_resend_key / _resolve_twilio_creds)

  PUT /settings/database  ──▶ tenants.db_type / .db_config_json (encrypted)
                                │
                                ▼
                      data_sync_service  +  data_sources API
                                │
                                ▼
                      tenants.schema_mapping_json  (shared with simulator +
                      fraud_detection_service + data_sync)
```

## 2. Consumers of each settings field

| Setting | Written by | Read by |
|---|---|---|
| `tenants.db_type` + `db_config_json` (db creds) | `PUT /settings/database` | `data_sync_service`, `data_sources`, `test-connection` |
| `db_config_json.notifications.company_alert_email` | `PUT /settings/notifications` + signup | `fraud_detection_service._notify_and_broadcast`, `simulator._resolve_company_alert_emails` |
| `db_config_json.notifications.sms_enabled / email_*` toggles | `PUT /settings/notifications` | (declared; **not yet enforced** — see issue #3) |
| `tenant_credentials(resend, brevo, twilio, …)` | `PUT /credentials` | `fraud_detection_service`, `simulator._resolve_*`, `notification_service` overrides |
| `schema_mapping_json` | `PUT /settings/schema-mapping` | `fraud_detection_service` (feature extraction), `data_sync_service`, `simulator` |
| `tenants.subscription_plan` | `PUT /settings/plan` | Plan gating (currently informational only) |

## 3. Identified issues (issue log)

### ISSUE-001 — new-user signup left the alert email blank  ✅ FIXED
**Symptom:** After signup, fraud alerts fired but `results["email_company"] = "skipped:no_key_or_email"` because no `company_alert_email` existed.
**Root cause:** `POST /auth/signup` created a tenant without initialising `db_config_json`. User had to re-enter the same email in Settings → Notifications.
**Fix:** Signup now seeds `tenant.db_config_json.notifications = {company_alert_email: body.email, sms_enabled: bool(phone), email_customer: True, email_company: True}`.
**File:** [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py)

### ISSUE-002 — email provider was hard-coded to Resend  ✅ FIXED
**Symptom:** If a tenant only had a Brevo key, the platform still said "no email provider configured."
**Root cause:** `notification_service.send_fraud_alert_notifications` called `_send_resend` inline with no abstraction for other providers.
**Fix:** Added `_send_email()` helper (Resend → Brevo fallback), `_send_brevo()` HTTP helper, `BREVO_API_KEY` setting, Brevo live-test under `/credentials/{id}/test`, and Brevo listed in `/settings/keys-summary` + `/settings/notifications`.

### ISSUE-003 — notification toggles are persisted but not honoured  ✅ FIXED
**Symptom:** `sms_enabled / email_customer / email_company` are saved via `PUT /settings/notifications` but `send_fraud_alert_notifications` ignored them.
**Fix:** `fraud_detection_service` now reads all three toggles from `notif_cfg` before `create_task` fires and passes them as `sms_enabled`, `email_customer_enabled`, `email_company_enabled` to `send_fraud_alert_notifications`, which gates each channel accordingly.
**Files:** [backend/app/services/fraud_detection_service.py](../backend/app/services/fraud_detection_service.py), [backend/app/services/notification_service.py](../backend/app/services/notification_service.py)

### ISSUE-004 — `keys-summary` list is hard-coded  ✅ FIXED
**Fix:** Added `SUPPORTED_PROVIDERS` constant to [backend/app/schemas/credentials.py](../backend/app/schemas/credentials.py). `settings.py /keys-summary` now imports and uses it. Adding a new provider requires only one change: a single entry in that list.

### ISSUE-005 — BYOK key-name fallback only exists for Resend  ✅ FIXED
**Fix:** Extracted `scan_any_cred_for_service(db, tenant_id, service)` shared helper into [credential_service.py](../backend/app/services/credential_service.py). `simulator._resolve_resend_key` now delegates to it (step 2), and a new `simulator._resolve_brevo_key` function uses the same chain. `fraud_detection_service` also uses it for both Resend and Brevo.

### ISSUE-006 — plan is advisory only  ✅ FIXED (SMS gate)
**Fix:** `fraud_detection_service` reads `tenant_obj.subscription_plan` and passes `tenant_plan` to `send_fraud_alert_notifications`. The notification service strips `sms` from the channel list if `tenant_plan not in ("pro", "advanced")`, returning `"skipped:plan_upgrade_required"`. Full endpoint-level gating (txn caps, connector limits) remains a future task.
**Files:** [backend/app/services/fraud_detection_service.py](../backend/app/services/fraud_detection_service.py), [backend/app/services/notification_service.py](../backend/app/services/notification_service.py)

### ISSUE-007 — legacy notification key path still read  ✅ FIXED
**Fix:** Alembic migration `c1d2e3f4a5b6` promotes `db_config_json.notifications.resend_api_key` and `brevo_api_key` into `tenant_credentials` and strips them from the JSON blob. Migration is idempotent and safe to run multiple times.
**File:** [backend/app/db/migrations/versions/c1d2e3f4a5b6_migrate_legacy_notif_keys.py](../backend/app/db/migrations/versions/c1d2e3f4a5b6_migrate_legacy_notif_keys.py)

### ISSUE-008 — `EMAIL_FROM` fallback caused 403/401 rejections  ✅ FIXED
**Fix:** `fraud_detection_service` pre-resolves `from_email` via `get_decrypted(db, tenant_id, "resend", "from_email")` while the DB session is open, then passes it as `override_from_email`. `notification_service` uses it directly when present; when absent it falls back to `onboarding@resend.dev` (Resend sandbox) instead of the unowned `noreply@finshield.ai` domain.
**Files:** [backend/app/services/fraud_detection_service.py](../backend/app/services/fraud_detection_service.py), [backend/app/services/notification_service.py](../backend/app/services/notification_service.py)

### ISSUE-009 — `db_config_json` mutations need `flag_modified`  ✅ FIXED
**Fix:** All mutation sites now assign a *new* dict object (not in-place mutation) so SQLAlchemy detects the change without needing `flag_modified`. `save_schema_mapping` was updated to use `updated = dict(existing)` + assignment pattern. `PUT /settings/database` already used assignment. Code comments added at both sites explaining the rule for future contributors.
**Files:** [backend/app/api/v1/settings.py](../backend/app/api/v1/settings.py)

---

## 4. How to reproduce the "new user auto-populate" test

1. `POST /api/v1/auth/signup` with `{email, password, full_name, phone_number, institution_name, institution_type}`.
2. Login and call `GET /api/v1/settings/notifications` — expect `company_alert_email` to equal the signup email.
3. Run any fraud-scoring flow (e.g., `POST /api/v1/transactions/test`) — `notification_service` should now deliver to the signup email with whichever of Resend / Brevo is configured at the platform or tenant level.

## 5. Coverage gaps to watch

- No test exercises the Resend→Brevo fallback path in `notification_service._send_email`.
- `credential_service._test_twilio` is format-only, not a live ping — a bad token is only caught when the first alert fails.
- `PUT /auth/signup` has no integration test verifying the seeded `db_config_json`.
