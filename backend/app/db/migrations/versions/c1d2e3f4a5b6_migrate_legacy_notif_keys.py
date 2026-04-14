"""migrate_legacy_notif_keys

ISSUE-007: Promote legacy notification API keys stored inside
tenants.db_config_json["notifications"] into the canonical
tenant_credentials table, then strip them from the JSON blob.

Affects keys:
  - notifications.resend_api_key   → service="resend",  key_name="resend_api_key"
  - notifications.brevo_api_key    → service="brevo",   key_name="brevo_api_key"

Other notification fields (company_alert_email, sms_enabled, email_*) are
intentionally left in db_config_json — they are not secrets and the read path
expects them there.

Revision ID: c1d2e3f4a5b6
Revises: b3f1a2d4e5c6
Create Date: 2026-04-14 00:00:00.000000
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b3f1a2d4e5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Keys to migrate: (json_field_name, credential_service, credential_key_name)
_KEYS_TO_MIGRATE = [
    ("resend_api_key", "resend", "resend_api_key"),
    ("brevo_api_key", "brevo", "brevo_api_key"),
]


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    now = datetime.now(timezone.utc)

    try:
        tenants = session.execute(
            sa.text("SELECT id, db_config_json FROM tenants WHERE db_config_json IS NOT NULL")
        ).fetchall()

        for tenant_id, raw_json in tenants:
            if not raw_json:
                continue

            # db_config_json may be stored as a string (SQLite) or dict (Postgres)
            cfg: dict = json.loads(raw_json) if isinstance(raw_json, str) else dict(raw_json)
            notif: dict = cfg.get("notifications", {})
            if not notif:
                continue

            changed = False
            for json_field, svc, key_name in _KEYS_TO_MIGRATE:
                encrypted_val = notif.get(json_field, "")
                if not encrypted_val:
                    continue

                # Check if already promoted (idempotent)
                existing = session.execute(
                    sa.text(
                        "SELECT id FROM tenant_credentials "
                        "WHERE tenant_id = :tid AND service = :svc AND key_name = :kn"
                    ),
                    {"tid": tenant_id, "svc": svc, "kn": key_name},
                ).fetchone()

                if not existing:
                    session.execute(
                        sa.text(
                            "INSERT INTO tenant_credentials "
                            "(id, tenant_id, service, key_name, label, value_encrypted, created_by, created_at, updated_at) "
                            "VALUES (:id, :tid, :svc, :kn, :lbl, :val, :by, :cat, :uat)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "tid": tenant_id,
                            "svc": svc,
                            "kn": key_name,
                            "lbl": f"Migrated from legacy config ({json_field})",
                            "val": encrypted_val,
                            "by": None,
                            "cat": now,
                            "uat": now,
                        },
                    )

                # Strip the key from db_config_json regardless of whether we
                # just inserted or it was already there.
                notif.pop(json_field, None)
                changed = True

            if changed:
                cfg["notifications"] = notif
                session.execute(
                    sa.text("UPDATE tenants SET db_config_json = :cfg WHERE id = :tid"),
                    {"cfg": json.dumps(cfg), "tid": tenant_id},
                )

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    # Downgrade is intentionally a no-op: re-populating the JSON blob from
    # tenant_credentials would require decrypting and re-inserting secrets,
    # which is risky.  If a rollback is needed, restore from a database backup.
    pass
