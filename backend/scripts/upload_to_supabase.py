"""
FinShield AI — Supabase Data Upload
=====================================
Reads the generated CSV files and uploads customers + transactions
to your Supabase project.

Schema: Cards are embedded directly in the customers table (no separate cards table).

Run AFTER seed_data.py:
    cd backend
    python scripts/upload_to_supabase.py

Requirements:
    SUPABASE_URL and SUPABASE_SERVICE_KEY set in backend/.env
"""

import asyncio
import csv
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

SUPABASE_URL         = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

DATA_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")
BATCH_SIZE = 500  # Supabase free tier: safe batch size


def load_csv(filename: str) -> list[dict]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [!] File not found: {path}")
        print("      Run: python scripts/seed_data.py first")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean_customer(row: dict, tenant_id: str) -> dict:
    """Map CSV columns to Supabase customers table schema.

    Card details are embedded directly — no separate cards table.
    Test customers have full card_number visible; regular customers are masked.
    """
    return {
        "id":                     row["customer_id"],
        "tenant_id":              tenant_id,
        # ── Identity ──────────────────────────────────────────────────────────
        "full_name":              row["full_name"],
        "email":                  row["email"],
        "phone_number":           row["phone_number"],
        "date_of_birth":          row["date_of_birth"] or "1990-01-01",
        # ── Location ──────────────────────────────────────────────────────────
        "city":                   row["city"],
        "state_province":         row["state_province"],
        "postal_code":            row["postal_code"],
        "country_code":           row["country_code"],
        # ── Account ───────────────────────────────────────────────────────────
        "account_type":           row["account_type"],
        "account_opening_date":   row["account_opening_date"] or "2020-01-01",
        "account_status":         row.get("account_status", "active"),
        "kyc_status":             row["kyc_status"],
        "kyc_verification_level": row["kyc_level"],
        "risk_score":             float(row["risk_score"]),
        "customer_tier":          row["customer_tier"],
        "balance_amount":         float(row["balance_amount"]),
        "active_card_count":      int(row["active_card_count"]),
        # ── Embedded card details ──────────────────────────────────────────────
        # card_number: full number for test customers, XXXX-XXXX-XXXX-{last4} for others
        "card_number":            row.get("card_number", "XXXX-XXXX-XXXX-0000"),
        "card_last4":             row.get("card_last4", "0000"),
        "card_network":           row.get("card_network", "Visa"),
        "card_cvv":               row.get("card_cvv", "000"),
        "card_expiry":            row.get("card_expiry", "12/2030"),
        "card_status":            row.get("card_status", "active"),
        "card_token":             row.get("card_token", ""),
        # ── Segmentation ──────────────────────────────────────────────────────
        "profile_type":           row.get("profile_type", "standard_salaried"),
        "is_test_customer":       str(row.get("is_test_customer", "False")).lower() == "true",
        "test_scenario":          row.get("test_scenario", ""),
    }


def clean_transaction(row: dict, tenant_id: str) -> dict:
    """Map CSV columns to Supabase transactions table schema.

    card_last4 and card_network are denormalised from the customer row.
    """
    # Parse triggered_rule_ids safely
    raw_rules = row.get("triggered_rule_ids", "[]")
    try:
        rules_list = json.loads(raw_rules) if raw_rules.startswith("[") else eval(raw_rules)
        triggered_rules = json.dumps(rules_list)
    except Exception:
        triggered_rules = "[]"

    return {
        "id":                     row["transaction_id"],
        "tenant_id":              tenant_id,
        "customer_id":            row["customer_id"],
        # ── Card (denormalised from customer) ─────────────────────────────────
        "card_last4":             row.get("card_last4", "0000"),
        "card_network":           row.get("card_network", "Visa"),
        # ── Merchant ──────────────────────────────────────────────────────────
        "merchant_name":          row["merchant_name"],
        "merchant_category_code": row["merchant_category_code"],
        # ── Amount ────────────────────────────────────────────────────────────
        "amount":                 float(row["amount"]),
        "currency":               row.get("currency", "INR"),
        # ── Type & Channel ────────────────────────────────────────────────────
        "transaction_type":       row.get("transaction_type", "purchase"),
        "channel":                row["channel"],
        # ── Location ──────────────────────────────────────────────────────────
        "location_lat":           float(row["location_lat"]) if row.get("location_lat") else 19.0760,
        "location_lng":           float(row["location_lng"]) if row.get("location_lng") else 72.8777,
        "city":                   row["city"],
        "country_code":           row.get("country_code", "IN"),
        # ── Device ────────────────────────────────────────────────────────────
        "ip_address":             row.get("ip_address", "0.0.0.0"),
        "device_fingerprint":     row.get("device_fingerprint", ""),
        "device_type":            row.get("device_type", "mobile"),
        # ── Status ────────────────────────────────────────────────────────────
        "status":                 row.get("status", "completed"),
        # ── Fraud fields ──────────────────────────────────────────────────────
        "fraud_score":            float(row["fraud_score"]) if row.get("fraud_score") else 0.0,
        "fraud_risk_level":       row.get("fraud_risk_level") or "low",
        "fraud_category":         row.get("fraud_category", "unscored"),
        "is_flagged":             str(row.get("is_flagged", "False")).lower() == "true",
        "is_blocked":             str(row.get("is_blocked", "False")).lower() == "true",
        "is_test":                False,
        "model_version":          row.get("model_version") or "ensemble_v1",
        "triggered_rule_ids":     triggered_rules,
        "fraud_scored_at":        row.get("fraud_scored_at") or None,
        "transaction_timestamp":  row["transaction_timestamp"],
    }


def upload_table(client, table: str, rows: list[dict], label: str) -> int:
    """Upload rows in batches, print progress, return count uploaded."""
    uploaded = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            client.table(table).upsert(batch, on_conflict="id").execute()
            uploaded += len(batch)
            print(f"  Uploaded {label}: {uploaded:,}/{len(rows):,}", end="\r")
        except Exception as e:
            print(f"\n  ERROR in batch {i}-{i+len(batch)}: {e}")
    print(f"\n  Uploaded {uploaded:,} {label} to Supabase")
    return uploaded


async def upload():
    print("\n" + "="*60)
    print("  FinShield AI -- Supabase Upload")
    print("="*60)

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("\n  ERROR: SUPABASE_URL or SUPABASE_ANON_KEY not set in backend/.env")
        return

    key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_ANON_KEY

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, key)
        print(f"\n  Connected to: {SUPABASE_URL}")
    except Exception as e:
        print(f"\n  ERROR: Could not connect to Supabase: {e}")
        return

    # ── Step 1: Get tenant ────────────────────────────────────────────────────
    print("\n[1/3] Getting tenant ID from Supabase...")
    try:
        result = client.table("tenants").select("id").limit(1).execute()
        if result.data:
            tenant_id = result.data[0]["id"]
            print(f"  Found tenant: {tenant_id}")
        else:
            print("  No tenants found in Supabase.")
            print("  Run this SQL in Supabase Dashboard > SQL Editor:")
            print("  INSERT INTO tenants (id, organization_name, institution_type, subscription_plan, is_active)")
            print("  VALUES (gen_random_uuid()::text, 'FinShield Demo Bank', 'bank', 'pro', true);")
            return
    except Exception as e:
        print(f"  ERROR fetching tenant: {e}")
        print("  Run the SQL migration in docs/supabase_schema.sql first.")
        return

    # ── Step 2: Upload customers (card details embedded) ─────────────────────
    print("\n[2/3] Uploading customers (with embedded card details)...")
    customers_raw = load_csv("customers_100.csv")
    if not customers_raw:
        return
    customers = [clean_customer(r, tenant_id) for r in customers_raw]
    c_uploaded = upload_table(client, "customers", customers, "customers")

    # ── Step 3: Upload transactions ───────────────────────────────────────────
    print("\n[3/3] Uploading 10,000 transactions (this may take ~2-3 min)...")
    transactions_raw = load_csv("transactions_10000.csv")
    if not transactions_raw:
        return
    transactions = [clean_transaction(r, tenant_id) for r in transactions_raw]
    t_uploaded = upload_table(client, "transactions", transactions, "transactions")

    print("\n" + "="*60)
    print("  UPLOAD COMPLETE")
    print("="*60)
    print(f"  Customers:    {c_uploaded} (card details embedded in each row)")
    print(f"  Transactions: {t_uploaded:,}")
    print(f"  Supabase:     {SUPABASE_URL}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(upload())
