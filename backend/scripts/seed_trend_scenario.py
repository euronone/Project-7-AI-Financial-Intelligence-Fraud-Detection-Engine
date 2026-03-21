#!/usr/bin/env python3
"""
Seed trend data for the dashboard Fraud Trends chart.

Creates fraud alerts spread across the last 30 days so the dashboard
shows a visible trend (count and amount by day).

Run AFTER seed_data.py. Safe to run multiple times (adds more alerts).

Usage: poetry run python scripts/seed_trend_scenario.py
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import FraudAlert, MLModel, Rule, Transaction, User

settings = get_settings()
NOW = datetime.now(timezone.utc)


async def main():
    print("FinShield AI — Seeding trend scenario (fraud alerts across 30 days)...")

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        tx_result = await session.execute(select(Transaction).where(Transaction.amount > 50).limit(350))
        transactions = list(tx_result.scalars().all())
        if not transactions:
            print("  No transactions. Run seed_data.py first.")
            return

        rules_result = await session.execute(select(Rule).where(Rule.is_active.is_(True)).limit(1))
        rule = rules_result.scalar_one_or_none()
        models_result = await session.execute(select(MLModel).where(MLModel.status == "active").limit(1))
        model = models_result.scalar_one_or_none()
        users_result = await session.execute(select(User).where(User.role.in_(["analyst", "investigator"])).limit(5))
        analysts = list(users_result.scalars().all())

        total = 0
        for day_offset in range(30, 0, -1):
            day_start = NOW - timedelta(days=day_offset)
            # Slight upward trend: more alerts in recent days
            base_count = 3 + (30 - day_offset) // 6 + random.randint(-1, 2)
            count = max(2, min(base_count, 8))

            for _ in range(count):
                txn = random.choice(transactions)
                hour, minute = random.randint(0, 23), random.randint(0, 59)
                created_at = day_start.replace(hour=hour, minute=minute, second=0, microsecond=0)

                alert = FraudAlert(
                    transaction_id=txn.id,
                    entity_id=txn.source_entity_id,
                    alert_type=random.choice(["ml_detection", "rule_trigger", "anomaly", "velocity"]),
                    severity=random.choice(["low", "medium", "high", "critical"]),
                    status=random.choice(["open", "open", "investigating", "resolved_fraud", "resolved_false_positive"]),
                    title=f"Flagged: {txn.external_id}",
                    description=f"Amount {txn.amount} {txn.currency}",
                    confidence_score=txn.fraud_score or Decimal(str(round(random.uniform(0.5, 0.92), 4))),
                    rule_id=rule.id if rule and random.random() > 0.5 else None,
                    model_id=model.id if model and random.random() > 0.5 else None,
                    assigned_to=random.choice(analysts).id if analysts and random.random() > 0.5 else None,
                )
                # Set created_at/updated_at before add so they're used on insert (override server_default)
                alert.created_at = created_at
                alert.updated_at = created_at
                session.add(alert)
                total += 1

            await session.flush()

        await session.commit()
        print(f"  Added {total} fraud alerts spread across the last 30 days.")
        print("  Refresh the dashboard to see the Fraud Trends chart.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
