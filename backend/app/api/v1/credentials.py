"""BYOK Credentials Manager API — /api/v1/credentials"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.schemas.credentials import (
    CredentialDeleteResponse,
    CredentialOut,
    CredentialTestResult,
    CredentialUpsert,
)
from app.services import credential_service

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("", response_model=list[CredentialOut])
async def list_credentials(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all credentials for the current tenant (values masked)."""
    return await credential_service.list_credentials(db, current_user.tenant_id)


@router.put("", response_model=CredentialOut, status_code=status.HTTP_200_OK)
async def upsert_credential(
    body: CredentialUpsert,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Create or replace a credential for the current tenant.

    - If a row with the same (tenant_id, service, key_name) exists it is updated.
    - The plaintext `value` is encrypted with Fernet before storage.
    - The response always returns a masked value — the plaintext is never echoed.
    """
    if current_user.role not in ("admin", "analyst"):
        raise HTTPException(status_code=403, detail="Only admin/analyst can manage credentials")
    return await credential_service.upsert_credential(
        db, current_user.tenant_id, body, current_user.id
    )


@router.delete("/{credential_id}", response_model=CredentialDeleteResponse)
async def delete_credential(
    credential_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete a credential by ID (scoped to the current tenant)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete credentials")
    result = await credential_service.delete_credential(db, current_user.tenant_id, credential_id)
    if not result.deleted:
        raise HTTPException(status_code=404, detail="Credential not found")
    return result


@router.post("/{credential_id}/test", response_model=CredentialTestResult)
async def test_credential(
    credential_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Live-test the stored credential by making a real API call to the service.

    Supported live tests: resend, twilio, stripe, openai.
    Other services return success=True with a note that no live test is available.
    """
    from sqlalchemy import select
    from app.models.credential import TenantCredential

    result = await db.execute(
        select(TenantCredential).where(
            TenantCredential.id == credential_id,
            TenantCredential.tenant_id == current_user.tenant_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found")

    return await credential_service.test_credential(
        db, current_user.tenant_id, row.service, row.key_name
    )
