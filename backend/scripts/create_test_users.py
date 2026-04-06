"""
Create 4 new test users (2 admin, 2 analyst) in the database
Run:
    cd backend
    .venv/Scripts/python.exe scripts/create_test_users.py
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.models.user import User, Tenant
from app.core.security import hash_password
from app.config import get_settings

settings = get_settings()


async def create_test_users():
    """Create 4 test users and one shared test tenant"""

    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if test tenant already exists
            result = await session.execute(
                select(Tenant).where(Tenant.organization_name == "Test Institution")
            )
            tenant = result.scalar_one_or_none()

            if not tenant:
                # Create test tenant
                tenant = Tenant(
                    id=str(uuid.uuid4()),
                    organization_name="Test Institution",
                    institution_type="bank",
                    subscription_plan="pro",
                    plan_started_at=datetime.now(timezone.utc),
                )
                session.add(tenant)
                await session.flush()
                print(f"[OK] Created test tenant: {tenant.organization_name} (ID: {tenant.id})")
            else:
                print(f"[INFO] Test tenant already exists: {tenant.organization_name}")

            # Define 4 new test users
            test_users = [
                {
                    "email": "admin1@finshield.test",
                    "password": "Admin123!@#",
                    "full_name": "Admin One",
                    "role": "admin",
                    "phone": "+919100000010",
                },
                {
                    "email": "admin2@finshield.test",
                    "password": "Admin123!@#",
                    "full_name": "Admin Two",
                    "role": "admin",
                    "phone": "+919100000011",
                },
                {
                    "email": "analyst1@finshield.test",
                    "password": "Analyst123!@#",
                    "full_name": "Analyst One",
                    "role": "analyst",
                    "phone": "+919100000012",
                },
                {
                    "email": "analyst2@finshield.test",
                    "password": "Analyst123!@#",
                    "full_name": "Analyst Two",
                    "role": "analyst",
                    "phone": "+919100000013",
                },
            ]

            # Create each user if not exists
            for user_data in test_users:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    print(f"[INFO] User already exists: {user_data['email']}")
                    continue

                # Create new user
                user = User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=hash_password(user_data["password"]),
                    phone_number=user_data["phone"],
                    role=user_data["role"],
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(user)
                print(f"[OK] Created {user_data['role'].upper()}: {user_data['email']} / {user_data['password']}")

            # Commit all changes
            await session.commit()
            print("\n[SUCCESS] All test users created successfully!")
            print("\n=== New Test Credentials ===")
            print("Admin 1:    admin1@finshield.test   /  Admin123!@#")
            print("Admin 2:    admin2@finshield.test   /  Admin123!@#")
            print("Analyst 1:  analyst1@finshield.test /  Analyst123!@#")
            print("Analyst 2:  analyst2@finshield.test /  Analyst123!@#")
            print("=============================\n")

        except Exception as exc:
            print(f"[ERROR] Error: {exc}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_users())
