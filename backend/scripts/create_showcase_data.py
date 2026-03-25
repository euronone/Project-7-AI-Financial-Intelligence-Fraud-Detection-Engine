"""
FinShield AI — Showcase Dataset Builder
=========================================
Merges customers + cards into a single flat CSV for class presentation.

Each row = one customer with their primary card details inline.
Test customers (10) show full unmasked card numbers.
Regular customers show XXXX-XXXX-XXXX-{last4} format.

Outputs:
    data/samples/showcase_customers_cards.csv   ← merged flat file
    data/samples/showcase_transactions.csv       ← transactions with customer name joined

Run:
    cd backend
    python scripts/create_showcase_data.py
"""

import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows, filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows -> {path}")


def main():
    print("\n" + "="*60)
    print("  FinShield AI -- Showcase Dataset Builder")
    print("="*60)

    customers    = load_csv("customers_100.csv")
    cards        = load_csv("cards_100.csv")
    transactions = load_csv("transactions_10000.csv")

    # ── Build primary card lookup: customer_id -> primary card row ────────────
    primary_cards = {}
    all_cards_by_customer = {}
    for c in cards:
        cid = c["customer_id"]
        all_cards_by_customer.setdefault(cid, []).append(c)
        if c["is_primary"] == "True":
            primary_cards[cid] = c

    # ── Merge customers + primary card into one flat row ─────────────────────
    print("\n[1/2] Building merged customer + card dataset...")
    merged = []
    for cust in customers:
        cid  = cust["customer_id"]
        card = primary_cards.get(cid, {})
        is_test = card.get("is_test_card", "False") == "True"

        # For test cards: show full number. For others: show masked.
        card_display = card.get("card_number") if is_test and card.get("card_number") \
                       else card.get("card_masked", "N/A")

        merged.append({
            # ── Customer identity ──────────────────────────────────────────
            "customer_id":          cid,
            "full_name":            cust["full_name"],
            "email":                cust["email"],
            "phone_number":         cust["phone_number"],
            "date_of_birth":        cust.get("date_of_birth", ""),
            # ── Primary card details (cols 6–11) ───────────────────────────
            "card_network":         card.get("card_network", ""),
            "card_number":          card_display,
            "card_cvv":             card.get("card_cvv", ""),
            "card_expiry":          card.get("card_expiry", ""),
            "card_status":          card.get("card_status", ""),
            "total_cards":          len(all_cards_by_customer.get(cid, [])),
            # ── Account details ────────────────────────────────────────────
            "account_type":         cust["account_type"],
            "account_status":       cust.get("account_status", "active"),
            "city":                 cust["city"],
            "state_province":       cust["state_province"],
            "country_code":         cust["country_code"],
            "kyc_status":           cust["kyc_status"],
            "customer_tier":        cust["customer_tier"],
            "balance_amount":       cust["balance_amount"],
            "risk_score":           cust["risk_score"],
            "profile_type":         cust["profile_type"],
            # ── Test scenario label (empty for regular customers) ──────────
            "test_scenario":        cust.get("test_scenario", ""),
        })

    write_csv(merged, "showcase_customers_cards.csv")

    # ── Build customer name lookup for transaction join ───────────────────────
    cust_name = {c["customer_id"]: c["full_name"] for c in customers}
    card_num  = {c["customer_id"]: (
        c.get("card_number") if primary_cards.get(c["customer_id"], {}).get("is_test_card") == "True"
        else primary_cards.get(c["customer_id"], {}).get("card_masked", "")
    ) for c in customers}

    # ── Build showcase transactions: join customer name + card number ─────────
    print("\n[2/2] Building showcase transactions (with customer name + card)...")
    txn_rows = []
    for t in transactions:
        cid = t["customer_id"]
        txn_rows.append({
            # ── Who ────────────────────────────────────────────────────────
            "transaction_id":        t["transaction_id"],
            "customer_name":         cust_name.get(cid, "Unknown"),
            "customer_id":           cid,
            "card_number":           card_num.get(cid, ""),
            # ── What & where ───────────────────────────────────────────────
            "amount_inr":            t["amount"],
            "merchant_name":         t["merchant_name"],
            "channel":               t["channel"],
            "city":                  t["city"],
            "country_code":          t["country_code"],
            "device_type":           t["device_type"],
            "transaction_timestamp": t["transaction_timestamp"],
            # ── Fraud verdict ──────────────────────────────────────────────
            "fraud_category":        t["fraud_category"],
            "fraud_score":           t["fraud_score"],
            "fraud_risk_level":      t["fraud_risk_level"],
            "is_flagged":            t["is_flagged"],
            "is_blocked":            t["is_blocked"],
            "triggered_rules":       t["triggered_rule_ids"],
            "status":                t["status"],
        })

    write_csv(txn_rows, "showcase_transactions.csv")

    # ── Print summary table of test customers ─────────────────────────────────
    print("\n" + "="*100)
    print("  TEST CUSTOMERS QUICK REFERENCE")
    print("="*100)
    test_rows = [r for r in merged if r["test_scenario"]]
    print(f"  {'Name':<22} {'Card Number':<22} {'CVV':<6} {'Expiry':<10} {'Balance':>12}  {'Scenario'}")
    print("-"*100)
    for r in test_rows:
        print(f"  {r['full_name']:<22} {r['card_number']:<22} {r['card_cvv']:<6} "
              f"{r['card_expiry']:<10} {float(r['balance_amount']):>12,.2f}  {r['test_scenario']}")

    print("\n" + "="*60)
    print("  SHOWCASE FILES READY")
    print("="*60)
    print("  showcase_customers_cards.csv")
    print("    -> 110 rows (100 regular + 10 test)")
    print("    -> Columns: customer info + primary card (number visible for test)")
    print()
    print("  showcase_transactions.csv")
    print("    -> 10,000 rows with customer name + card number joined")
    print("    -> Fraud verdict columns included")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
