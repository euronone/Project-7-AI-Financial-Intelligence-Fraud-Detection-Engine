"""
Seed Supabase Auth with 4 test users
Run:
    cd backend
    .venv/Scripts/python.exe scripts/seed_supabase_auth.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

settings = get_settings()


async def seed_supabase_auth():
    """Create 4 test users in Supabase Auth"""

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_KEY not configured in .env")
        return

    try:
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        test_users = [
            {"email": "admin1@finshield.test",     "password": "Admin123!@#"},
            {"email": "admin2@finshield.test",     "password": "Admin123!@#"},
            {"email": "analyst1@finshield.test",   "password": "Analyst123!@#"},
            {"email": "analyst2@finshield.test",   "password": "Analyst123!@#"},
        ]

        print("[INFO] Seeding Supabase Auth users...\n")

        for user_data in test_users:
            try:
                # Create user in Supabase Auth using proper API
                supabase.auth.admin.create_user(
                    {
                        "email": user_data["email"],
                        "password": user_data["password"],
                        "email_confirm": True,
                    }
                )
                print(f"[OK] Created in Supabase Auth: {user_data['email']}")
            except Exception as e:
                error_str = str(e).lower()
                if "already exists" in error_str or "user already registered" in error_str:
                    print(f"[INFO] User already exists in Supabase Auth: {user_data['email']}")
                else:
                    print(f"[INFO] Supabase result for {user_data['email']}: {str(e)[:80]}")

        print("\n[SUCCESS] Supabase Auth seeding complete!")
        print("\n=== Test Credentials (Supabase Auth) ===")
        print("Admin 1:    admin1@finshield.test   /  Admin123!@#")
        print("Admin 2:    admin2@finshield.test   /  Admin123!@#")
        print("Analyst 1:  analyst1@finshield.test /  Analyst123!@#")
        print("Analyst 2:  analyst2@finshield.test /  Analyst123!@#")
        print("=====================================\n")

    except ImportError:
        print("[ERROR] supabase package not found. Already installed via pip.")
    except Exception as exc:
        print(f"[ERROR] {exc}")


if __name__ == "__main__":
    asyncio.run(seed_supabase_auth())
