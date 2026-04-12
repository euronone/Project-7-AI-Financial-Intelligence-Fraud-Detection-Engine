"""
FinShield AI — Create / Upsert Admin & Analyst Users (local SQLite dev)
=======================================================================
Creates admin@finshield.local and analyst@finshield.local directly in the
local SQLite database (finshield_dev.db).  Does NOT require SUPABASE_SERVICE_KEY.

Run from the backend directory:
    python scripts/create_admin_local.py

Safe to run multiple times — uses upsert logic (update if exists).
"""

import asyncio
import os
import sys
import uuid

# Allow imports from /backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import Base  # noqa: E402
import app.models  # noqa: E402,F401 — registers all ORM models

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./finshield_dev.db")

USERS_TO_CREATE = [
    {
        "email":      "admin@finshield.local",
        "full_name":  "Admin User",
        "password":   "Admin123!@#",
        "role":       "admin",
    },
    {
        "email":      "analyst@finshield.local",
        "full_name":  "Fraud Analyst",
        "password":   "Analyst123!@#",
        "role":       "analyst",
    },
]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as db:
        # ── Ensure tables exist ────────────────────────────────────────────────
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # ── Get or create a default tenant ────────────────────────────────────
        from app.models.user import Tenant, User

        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                organization_name="FinShield Demo Bank",
                institution_type="bank",
                subscription_plan="pro",
                is_active=True,
            )
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)
            print(f"  Created tenant: {tenant.organization_name} (id={tenant.id[:8]}...)")
        else:
            print(f"  Using tenant: {tenant.organization_name} (id={tenant.id[:8]}...)")

        tenant_id = tenant.id

        # ── Create / update users ─────────────────────────────────────────────
        for spec in USERS_TO_CREATE:
            result = await db.execute(
                select(User).where(User.email == spec["email"])
            )
            user = result.scalar_one_or_none()

            if user:
                # Update role and password in case they drifted
                user.role            = spec["role"]
                user.hashed_password = hash_password(spec["password"])
                user.is_active       = True
                user.is_verified     = True
                user.has_completed_onboarding = True
                user.tenant_id       = tenant_id
                await db.commit()
                print(f"  Updated : {spec['email']} (role={spec['role']})")
            else:
                new_user = User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    email=spec["email"],
                    full_name=spec["full_name"],
                    hashed_password=hash_password(spec["password"]),
                    role=spec["role"],
                    is_active=True,
                    is_verified=True,
                    has_completed_onboarding=True,
                )
                db.add(new_user)
                await db.commit()
                print(f"  Created : {spec['email']} (role={spec['role']})")

    await engine.dispose()

    print()
    print("Done! Login credentials:")
    print("  admin@finshield.local    /  Admin123!@#   (role: admin)")
    print("  analyst@finshield.local  /  Analyst123!@#  (role: analyst)")


if __name__ == "__main__":
    asyncio.run(main())
