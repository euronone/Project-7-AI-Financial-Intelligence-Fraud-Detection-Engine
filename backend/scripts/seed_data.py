"""
Seed script for FinShield AI — populates the database with realistic test data.

Generates:
- 10 users (2 admin, 4 analyst, 2 investigator, 2 viewer)
- 1000 entities (700 individuals, 200 businesses, 100 merchants)
- 5000 transactions (spanning 90 days, ~2% labeled fraud)
- 200 fraud alerts
- 10 investigation cases
- 10 active rules
- 100 watchlist entries
- 3 ML models (1 active, 1 retired, 1 training)

Usage: poetry run python scripts/seed_data.py
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import (
    AuditLog,
    Case,
    Entity,
    FraudAlert,
    MLModel,
    Notification,
    RiskScore,
    Rule,
    Transaction,
    User,
    Watchlist,
)

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
               "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
COUNTRIES = ["US", "GB", "CA", "DE", "FR", "AU", "JP", "BR", "IN", "MX", "NG", "ZA", "SG", "AE", "KR"]
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
MCC_CODES = ["5411", "5812", "5541", "7011", "4511", "5691", "5311", "5944", "5999", "6011"]
BUSINESS_NAMES = ["Acme Corp", "Global Trade LLC", "Swift Payments Inc", "Nexus Financial", "Pinnacle Holdings",
                  "Vertex Solutions", "Quantum Dynamics", "Atlas Enterprises", "Zenith Capital", "Vanguard Systems"]
MERCHANT_NAMES = ["Amazon", "Walmart", "Target", "Best Buy", "Costco", "Home Depot", "Starbucks", "McDonald's",
                  "Shell Gas", "Uber", "Netflix", "Apple Store", "Nike", "Zara", "Whole Foods"]

NOW = datetime.now(timezone.utc)


def random_ip() -> str:
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def random_date(days_back: int = 90) -> datetime:
    return NOW - timedelta(days=random.uniform(0, days_back))


async def seed_users(session: AsyncSession) -> list[User]:
    users_data = [
        ("admin@finshield.dev", "Admin", "User", "admin"),
        ("admin2@finshield.dev", "Admin", "Two", "admin"),
        ("analyst1@finshield.dev", "Alice", "Analyst", "analyst"),
        ("analyst2@finshield.dev", "Bob", "Analyst", "analyst"),
        ("analyst3@finshield.dev", "Carol", "Analyst", "analyst"),
        ("analyst4@finshield.dev", "Dan", "Analyst", "analyst"),
        ("investigator1@finshield.dev", "Eve", "Investigator", "investigator"),
        ("investigator2@finshield.dev", "Frank", "Investigator", "investigator"),
        ("viewer1@finshield.dev", "Grace", "Viewer", "viewer"),
        ("viewer2@finshield.dev", "Henry", "Viewer", "viewer"),
    ]
    users = []
    password_hash = hash_password("Admin123!@#")
    for email, first, last, role in users_data:
        u = User(
            email=email, password_hash=password_hash,
            first_name=first, last_name=last, role=role, is_active=True,
        )
        session.add(u)
        users.append(u)
    await session.flush()
    print(f"  Seeded {len(users)} users")
    return users


async def seed_entities(session: AsyncSession) -> list[Entity]:
    entities = []
    for i in range(700):
        e = Entity(
            external_id=f"IND-{i:05d}",
            entity_type="individual",
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            email=f"user{i}@example.com",
            country_code=random.choice(COUNTRIES),
            risk_score=Decimal(str(round(random.uniform(0, 0.4), 4))),
            risk_level="low",
            kyc_status=random.choice(["verified", "verified", "verified", "pending"]),
        )
        entities.append(e)
        session.add(e)
    for i in range(200):
        e = Entity(
            external_id=f"BIZ-{i:05d}",
            entity_type="business",
            name=f"{random.choice(BUSINESS_NAMES)} {random.randint(1,99)}",
            country_code=random.choice(COUNTRIES),
            risk_score=Decimal(str(round(random.uniform(0, 0.5), 4))),
            risk_level=random.choice(["low", "medium"]),
            kyc_status="verified",
        )
        entities.append(e)
        session.add(e)
    for i in range(100):
        e = Entity(
            external_id=f"MER-{i:05d}",
            entity_type="merchant",
            name=f"{random.choice(MERCHANT_NAMES)} #{random.randint(100,999)}",
            country_code=random.choice(COUNTRIES),
            risk_score=Decimal(str(round(random.uniform(0, 0.3), 4))),
            risk_level="low",
            kyc_status="verified",
        )
        entities.append(e)
        session.add(e)
    await session.flush()
    print(f"  Seeded {len(entities)} entities")
    return entities


async def seed_transactions(session: AsyncSession, entities: list[Entity]) -> list[Transaction]:
    transactions = []
    types = ["payment", "transfer", "withdrawal", "deposit", "refund"]
    channels = ["online", "pos", "atm", "mobile", "wire", "ach"]
    statuses = ["completed", "completed", "completed", "completed", "pending", "flagged"]

    for i in range(5000):
        is_fraud = random.random() < 0.02
        amount = round(random.uniform(5, 500), 2) if not is_fraud else round(random.uniform(2000, 50000), 2)
        fraud_score = round(random.uniform(0.7, 0.99), 4) if is_fraud else round(random.uniform(0.0, 0.35), 4)
        status = "flagged" if is_fraud and random.random() < 0.8 else random.choice(statuses)
        risk = "critical" if fraud_score > 0.8 else "high" if fraud_score > 0.6 else "medium" if fraud_score > 0.3 else "low"

        src = random.choice(entities)
        dst = random.choice(entities) if random.random() > 0.3 else None
        t = Transaction(
            external_id=f"TXN-{i:07d}",
            source_entity_id=src.id,
            destination_entity_id=dst.id if dst and dst.id != src.id else None,
            amount=Decimal(str(amount)),
            currency=random.choice(CURRENCIES),
            transaction_type=random.choice(types),
            channel=random.choice(channels),
            status=status,
            merchant_category_code=random.choice(MCC_CODES),
            ip_address=random_ip(),
            country_code=random.choice(COUNTRIES),
            card_present=random.choice([True, False]),
            fraud_score=Decimal(str(fraud_score)),
            risk_level=risk,
            processed_at=random_date(),
        )
        transactions.append(t)
        session.add(t)

    await session.flush()
    print(f"  Seeded {len(transactions)} transactions")
    return transactions


async def seed_rules(session: AsyncSession, users: list[User]) -> list[Rule]:
    admin = users[0]
    templates = [
        ("High Amount Alert", "amount", {"operator": "gt", "field": "amount", "value": 10000}, "high"),
        ("Velocity Check 1h", "velocity", {"operator": "gt", "field": "txn_count_1h", "value": 5}, "medium"),
        ("Cross-Border Flag", "geography", {"operator": "ne", "field": "country_code", "value": "source_country"}, "medium"),
        ("New Device Alert", "device", {"operator": "eq", "field": "is_new_device", "value": True}, "low"),
        ("Night Transaction", "pattern", {"operator": "between", "field": "hour", "value": [0, 5]}, "low"),
        ("Large Cash Withdrawal", "amount", {"operator": "gt", "field": "amount", "value": 5000, "channel": "atm"}, "high"),
        ("Rapid Succession", "velocity", {"operator": "gt", "field": "txn_count_5m", "value": 3}, "critical"),
        ("Blocked Country", "geography", {"operator": "in", "field": "country_code", "value": ["KP", "IR", "SY"]}, "critical"),
        ("Round Amount Pattern", "pattern", {"operator": "mod", "field": "amount", "value": 1000}, "medium"),
        ("Account Age Check", "custom", {"operator": "lt", "field": "account_age_days", "value": 7}, "medium"),
    ]
    rules = []
    for name, cat, conditions, sev in templates:
        r = Rule(
            name=name, category=cat,
            conditions={"rules": [conditions]},
            actions={"actions": [{"type": "create_alert"}]},
            severity=sev, is_active=True,
            priority=random.randint(1, 100),
            hit_count=random.randint(0, 500),
            created_by=admin.id,
        )
        rules.append(r)
        session.add(r)
    await session.flush()
    print(f"  Seeded {len(rules)} rules")
    return rules


async def seed_ml_models(session: AsyncSession, users: list[User]) -> list[MLModel]:
    admin = users[0]
    models = [
        MLModel(
            name="fraud-classifier", model_type="fraud_classifier", version="1.0.0",
            status="active", framework="xgboost",
            metrics={"accuracy": 0.95, "precision": 0.89, "recall": 0.82, "f1": 0.85, "auc_roc": 0.94},
            artifact_path="models/fraud_classifier_v1.onnx",
            promoted_at=NOW - timedelta(days=30), promoted_by=admin.id,
        ),
        MLModel(
            name="anomaly-detector", model_type="anomaly_detector", version="1.0.0",
            status="retired", framework="sklearn",
            metrics={"accuracy": 0.91, "precision": 0.78, "recall": 0.75, "f1": 0.76, "auc_roc": 0.88},
            artifact_path="models/anomaly_detector_v1.onnx",
        ),
        MLModel(
            name="fraud-classifier", model_type="fraud_classifier", version="2.0.0",
            status="training", framework="xgboost",
            metrics={}, artifact_path="models/fraud_classifier_v2_training.onnx",
        ),
    ]
    for m in models:
        session.add(m)
    await session.flush()
    print(f"  Seeded {len(models)} ML models")
    return models


async def seed_alerts(session: AsyncSession, transactions: list[Transaction], rules: list[Rule],
                      models: list[MLModel], users: list[User]) -> list[FraudAlert]:
    flagged = [t for t in transactions if t.status == "flagged"][:200]
    alert_types = ["ml_detection", "rule_trigger", "anomaly", "velocity"]
    severities = ["low", "medium", "high", "critical"]
    statuses = ["open", "open", "open", "investigating", "resolved_fraud", "resolved_false_positive", "dismissed"]
    analysts = [u for u in users if u.role in ("analyst", "investigator")]

    alerts = []
    for t in flagged:
        a = FraudAlert(
            transaction_id=t.id,
            entity_id=t.source_entity_id,
            alert_type=random.choice(alert_types),
            severity=random.choice(severities),
            status=random.choice(statuses),
            title=f"Suspicious transaction {t.external_id}",
            description=f"Transaction of {t.amount} {t.currency} flagged with score {t.fraud_score}",
            confidence_score=t.fraud_score,
            rule_id=random.choice(rules).id if random.random() > 0.5 else None,
            model_id=models[0].id if random.random() > 0.5 else None,
            assigned_to=random.choice(analysts).id if random.random() > 0.3 else None,
        )
        alerts.append(a)
        session.add(a)
    await session.flush()
    print(f"  Seeded {len(alerts)} fraud alerts")
    return alerts


async def seed_cases(session: AsyncSession, alerts: list[FraudAlert], users: list[User]) -> None:
    admin = users[0]
    analysts = [u for u in users if u.role in ("analyst", "investigator")]
    case_statuses = ["open", "in_progress", "pending_review", "closed_confirmed_fraud", "closed_false_positive"]

    for i in range(10):
        linked = random.sample([a.id for a in alerts], min(random.randint(1, 5), len(alerts)))
        c = Case(
            case_number=f"CASE-{NOW.strftime('%Y%m%d')}-{i+1:04d}",
            title=f"Investigation Case #{i+1}",
            description=f"Grouped investigation for {len(linked)} related alerts",
            status=random.choice(case_statuses),
            priority=random.choice(["low", "medium", "high", "critical"]),
            assigned_to=random.choice(analysts).id,
            total_amount_at_risk=Decimal(str(round(random.uniform(5000, 100000), 2))),
            alert_ids=linked,
            timeline={"events": [{"action": "created", "timestamp": NOW.isoformat(), "user": str(admin.id)}]},
            created_by=admin.id,
        )
        session.add(c)
    await session.flush()
    print("  Seeded 10 cases")


async def seed_watchlists(session: AsyncSession) -> None:
    types = ["sanctions", "pep", "internal_blacklist", "adverse_media", "custom"]
    sources = ["OFAC", "UN", "EU", "Internal", "Compliance Team"]
    for i in range(100):
        w = Watchlist(
            list_name=f"{random.choice(sources)} List",
            list_type=random.choice(types),
            entity_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            entity_identifiers={"name_variants": [f"variant_{i}"], "country": random.choice(COUNTRIES)},
            source=random.choice(sources),
            is_active=True,
        )
        session.add(w)
    await session.flush()
    print("  Seeded 100 watchlist entries")


async def seed_risk_scores(session: AsyncSession, entities: list[Entity], transactions: list[Transaction]) -> None:
    sample_entities = random.sample(entities, min(200, len(entities)))
    for e in sample_entities:
        score = round(random.uniform(0, 1), 4)
        rs = RiskScore(
            entity_id=e.id,
            overall_score=Decimal(str(score)),
            component_scores={"ml_score": round(random.uniform(0, 1), 4),
                              "rule_score": round(random.uniform(0, 1), 4),
                              "velocity_score": round(random.uniform(0, 1), 4),
                              "behavioral_score": round(random.uniform(0, 1), 4)},
            risk_factors={"factors": ["high_amount", "new_device"] if score > 0.5 else ["normal_pattern"]},
            model_version="1.0.0",
            explanation="Composite risk assessment" if score < 0.5 else "Elevated risk due to multiple factors",
        )
        session.add(rs)
    await session.flush()
    print(f"  Seeded {len(sample_entities)} risk scores")


async def main():
    print("FinShield AI — Seeding database...")
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print(f"  Database already has {count} users. Skipping seed.")
            print("  To re-seed, truncate all tables first.")
            return

        users = await seed_users(session)
        entities = await seed_entities(session)
        transactions = await seed_transactions(session, entities)
        rules = await seed_rules(session, users)
        models = await seed_ml_models(session, users)
        alerts = await seed_alerts(session, transactions, rules, models, users)
        await seed_cases(session, alerts, users)
        await seed_watchlists(session)
        await seed_risk_scores(session, entities, transactions)

        await session.commit()
        print("\nSeed complete!")
        print(f"  Default login: admin@finshield.dev / Admin123!@#")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
