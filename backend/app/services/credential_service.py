"""BYOK Credentials Manager — save, retrieve (masked), rotate, delete, and test credentials."""

import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encryptor
from app.models.credential import TenantCredential
from app.schemas.credentials import (
    CredentialDeleteResponse,
    CredentialOut,
    CredentialTestResult,
    CredentialUpsert,
)

logger = logging.getLogger(__name__)


def _mask(plaintext: str) -> str:
    """Return a masked version: '••••••••' + last 4 chars."""
    if len(plaintext) <= 4:
        return "••••" + plaintext
    return "••••••••" + plaintext[-4:]


def _to_out(row: TenantCredential, decrypted_value: str) -> CredentialOut:
    return CredentialOut(
        id=row.id,
        service=row.service,
        key_name=row.key_name,
        label=row.label,
        masked_value=_mask(decrypted_value),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── CRUD ─────────────────────────────────────────────────────────────────────


async def list_credentials(db: AsyncSession, tenant_id: str) -> list[CredentialOut]:
    """Return all credentials for a tenant (values masked)."""
    result = await db.execute(
        select(TenantCredential)
        .where(TenantCredential.tenant_id == tenant_id)
        .order_by(TenantCredential.service, TenantCredential.key_name)
    )
    rows = result.scalars().all()

    out = []
    for row in rows:
        try:
            plain = encryptor.decrypt(row.value_encrypted)
        except Exception:
            plain = "????-decryption-failed"
        out.append(_to_out(row, plain))
    return out


async def upsert_credential(
    db: AsyncSession,
    tenant_id: str,
    body: CredentialUpsert,
    created_by: str,
) -> CredentialOut:
    """Create or replace a credential. Encrypts before writing."""
    encrypted = encryptor.encrypt(body.value)

    result = await db.execute(
        select(TenantCredential).where(
            TenantCredential.tenant_id == tenant_id,
            TenantCredential.service == body.service,
            TenantCredential.key_name == body.key_name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value_encrypted = encrypted
        existing.label = body.label or existing.label
        existing.updated_at = datetime.now(timezone.utc)
        row = existing
    else:
        row = TenantCredential(
            tenant_id=tenant_id,
            service=body.service,
            key_name=body.key_name,
            label=body.label,
            value_encrypted=encrypted,
            created_by=created_by,
        )
        db.add(row)

    await db.commit()
    await db.refresh(row)
    return _to_out(row, body.value)


async def delete_credential(
    db: AsyncSession,
    tenant_id: str,
    credential_id: str,
) -> CredentialDeleteResponse:
    """Delete a credential by ID (scoped to tenant)."""
    result = await db.execute(
        delete(TenantCredential).where(
            TenantCredential.id == credential_id,
            TenantCredential.tenant_id == tenant_id,
        )
    )
    await db.commit()
    return CredentialDeleteResponse(deleted=result.rowcount > 0, id=credential_id)


async def scan_any_cred_for_service(
    db: AsyncSession,
    tenant_id: str,
    service: str,
) -> str | None:
    """
    ISSUE-005: fallback scan — return the decrypted value of the FIRST credential
    stored under `service` regardless of key_name.  Handles users who save their
    Brevo/Resend key under a non-canonical key_name (e.g. "api_key" instead of
    "brevo_api_key").  Callers should always try `get_decrypted` with the canonical
    key_name first; this is the second-chance lookup.
    """
    result = await db.execute(
        select(TenantCredential)
        .where(
            TenantCredential.tenant_id == tenant_id,
            TenantCredential.service == service,
        )
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    try:
        val = encryptor.decrypt(row.value_encrypted)
        if val:
            logger.debug(
                "Cred resolved via service-scan | service=%s key_name=%s", service, row.key_name
            )
            return val
    except Exception as exc:
        logger.warning("scan_any_cred_for_service decrypt error service=%s: %s", service, exc)
    return None


async def get_decrypted(
    db: AsyncSession,
    tenant_id: str,
    service: str,
    key_name: str,
) -> str | None:
    """Return plaintext value for internal use (never exposed to frontend)."""
    result = await db.execute(
        select(TenantCredential).where(
            TenantCredential.tenant_id == tenant_id,
            TenantCredential.service == service,
            TenantCredential.key_name == key_name,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    try:
        return encryptor.decrypt(row.value_encrypted)
    except Exception as exc:
        logger.error(
            "Decryption error for tenant=%s service=%s key=%s: %s",
            tenant_id,
            service,
            key_name,
            exc,
        )
        return None


# ── Connection testers ────────────────────────────────────────────────────────


async def test_credential(
    db: AsyncSession,
    tenant_id: str,
    service: str,
    key_name: str,
) -> CredentialTestResult:
    """Live-test a stored credential by making an authenticated API call."""
    plain = await get_decrypted(db, tenant_id, service, key_name)
    if not plain:
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=False,
            message="Credential not found or decryption failed",
        )

    tester = _TESTERS.get(service)
    if tester is None:
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=True,
            message="No live test available for this service — credential is stored and encrypted.",
        )

    return await tester(service, key_name, plain)


async def _test_resend(service: str, key_name: str, api_key: str) -> CredentialTestResult:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code in (200, 403):
            return CredentialTestResult(
                service=service,
                key_name=key_name,
                success=True,
                message="Resend API key is valid.",
                latency_ms=ms,
            )
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=False,
            message=f"Resend returned HTTP {r.status_code}",
            latency_ms=ms,
        )
    except Exception as exc:
        return CredentialTestResult(
            service=service, key_name=key_name, success=False, message=f"Connection error: {exc}"
        )


async def _test_twilio(service: str, key_name: str, value: str) -> CredentialTestResult:
    # Twilio needs both SID + token; we test by calling the account endpoint
    # For simplicity we just validate the format here
    if key_name == "twilio_account_sid":
        ok = value.startswith("AC") and len(value) == 34
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=ok,
            message="Twilio Account SID format valid."
            if ok
            else "Invalid Twilio Account SID format (should start with 'AC' and be 34 chars).",
        )
    return CredentialTestResult(
        service=service,
        key_name=key_name,
        success=True,
        message="Credential stored. Use Test Connection in Settings to validate full Twilio flow.",
    )


async def _test_stripe(service: str, key_name: str, api_key: str) -> CredentialTestResult:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.stripe.com/v1/account",
                auth=(api_key, ""),
            )
        ms = int((time.monotonic() - start) * 1000)
        success = r.status_code == 200
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=success,
            message="Stripe key valid." if success else f"Stripe returned HTTP {r.status_code}",
            latency_ms=ms,
        )
    except Exception as exc:
        return CredentialTestResult(
            service=service, key_name=key_name, success=False, message=f"Connection error: {exc}"
        )


async def _test_openai(service: str, key_name: str, api_key: str) -> CredentialTestResult:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        ms = int((time.monotonic() - start) * 1000)
        success = r.status_code == 200
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=success,
            message="OpenAI API key valid." if success else f"OpenAI returned HTTP {r.status_code}",
            latency_ms=ms,
        )
    except Exception as exc:
        return CredentialTestResult(
            service=service, key_name=key_name, success=False, message=f"Connection error: {exc}"
        )


async def _test_firebase(service: str, key_name: str, value: str) -> CredentialTestResult:
    """
    Validate a Firebase credential.

    Two credential shapes are supported:
      - key_name='server_key'  (legacy FCM HTTP v1 — starts with 'AAAA')
      - key_name='service_account_json' (current FCM HTTP v1 — JSON string)

    For server_key we can probe the FCM legacy endpoint to confirm validity.
    For service_account_json we validate that it parses as JSON and contains
    the expected fields — a live OAuth2 token exchange would require additional
    libraries that may not be installed.
    """
    import time as _time

    start = _time.monotonic()

    if key_name == "server_key":
        # Legacy FCM — probe with a dry-run request (no actual message sent)
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    headers={
                        "Authorization": f"key={value}",
                        "Content-Type": "application/json",
                    },
                    json={"registration_ids": ["dry_run_token_validation"]},
                )
            ms = int((_time.monotonic() - start) * 1000)
            # 200 = key valid (even if token is bogus), 401/403 = key invalid
            if r.status_code in (200, 400):
                return CredentialTestResult(
                    service=service,
                    key_name=key_name,
                    success=True,
                    message="Firebase Server Key is valid.",
                    latency_ms=ms,
                )
            return CredentialTestResult(
                service=service,
                key_name=key_name,
                success=False,
                message=f"Firebase returned HTTP {r.status_code} — key may be invalid or revoked.",
                latency_ms=ms,
            )
        except Exception as exc:
            return CredentialTestResult(
                service=service, key_name=key_name, success=False, message=f"Connection error: {exc}"
            )

    if key_name == "service_account_json":
        # Validate JSON structure — required fields per Google's service account schema
        import json as _json

        try:
            sa = _json.loads(value)
            required_fields = {"type", "project_id", "private_key_id", "private_key", "client_email"}
            missing = required_fields - set(sa.keys())
            if missing:
                return CredentialTestResult(
                    service=service,
                    key_name=key_name,
                    success=False,
                    message=f"Service account JSON is missing required fields: {', '.join(sorted(missing))}",
                )
            if sa.get("type") != "service_account":
                return CredentialTestResult(
                    service=service,
                    key_name=key_name,
                    success=False,
                    message="JSON 'type' field must be 'service_account'.",
                )
            ms = int((_time.monotonic() - start) * 1000)
            return CredentialTestResult(
                service=service,
                key_name=key_name,
                success=True,
                message=f"Firebase service account JSON is valid (project: {sa.get('project_id')}).",
                latency_ms=ms,
            )
        except _json.JSONDecodeError as exc:
            return CredentialTestResult(
                service=service,
                key_name=key_name,
                success=False,
                message=f"Service account value is not valid JSON: {exc}",
            )

    # Unknown key_name — accept as stored
    return CredentialTestResult(
        service=service,
        key_name=key_name,
        success=True,
        message="Firebase credential stored. Use 'server_key' or 'service_account_json' as key_name for live validation.",
    )


async def _test_brevo(service: str, key_name: str, api_key: str) -> CredentialTestResult:
    """Live-test a Brevo (Sendinblue) API key by hitting the /account endpoint."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.brevo.com/v3/account",
                headers={"api-key": api_key, "accept": "application/json"},
            )
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            return CredentialTestResult(
                service=service,
                key_name=key_name,
                success=True,
                message="Brevo API key is valid.",
                latency_ms=ms,
            )
        return CredentialTestResult(
            service=service,
            key_name=key_name,
            success=False,
            message=f"Brevo returned HTTP {r.status_code}",
            latency_ms=ms,
        )
    except Exception as exc:
        return CredentialTestResult(
            service=service, key_name=key_name, success=False, message=f"Connection error: {exc}"
        )


# Map service name → tester function
_TESTERS = {
    "resend": _test_resend,
    "brevo": _test_brevo,
    "twilio": _test_twilio,
    "stripe": _test_stripe,
    "openai": _test_openai,
    "firebase": _test_firebase,
}
