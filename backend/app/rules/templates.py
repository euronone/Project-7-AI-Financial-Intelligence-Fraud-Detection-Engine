"""Pre-built rule templates for common fraud patterns.

Each template returns a dict that can be used to pre-populate a new rule.
Users clone and customize these.
"""


def get_templates() -> list[dict]:
    return [
        {
            "name": "Card Testing Detection",
            "description": "Detects rapid low-value transactions typical of card testing attacks.",
            "category": "velocity",
            "severity": "high",
            "priority": 10,
            "conditions": {
                "logic": "and",
                "rules": [
                    {"field": "amount", "operator": "lt", "value": 5},
                    {"field": "txn_count_1h", "operator": "gt", "value": 10},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "block_transaction"},
                    {"type": "create_alert"},
                ],
            },
        },
        {
            "name": "Account Takeover",
            "description": "Flags transactions from new devices in different countries after password change.",
            "category": "device",
            "severity": "critical",
            "priority": 5,
            "conditions": {
                "logic": "and",
                "rules": [
                    {"field": "is_new_device", "operator": "eq", "value": True},
                    {"field": "country_code", "operator": "ne", "value": "home_country"},
                    {"field": "amount", "operator": "gt", "value": 500},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "block_transaction"},
                    {"type": "create_alert"},
                    {"type": "notify", "channel": "sms"},
                ],
            },
        },
        {
            "name": "Money Mule Detection",
            "description": "Detects rapid deposit-then-withdrawal patterns indicative of money muling.",
            "category": "pattern",
            "severity": "critical",
            "priority": 8,
            "conditions": {
                "logic": "and",
                "rules": [
                    {"field": "transaction_type", "operator": "eq", "value": "withdrawal"},
                    {"field": "amount", "operator": "gt", "value": 2000},
                    {"field": "account_age_days", "operator": "lt", "value": 30},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "flag_transaction"},
                    {"type": "create_alert"},
                    {"type": "adjust_risk_score", "delta": 0.3},
                ],
            },
        },
        {
            "name": "First-Party Fraud",
            "description": "Flags high-value transactions from accounts with recent info changes.",
            "category": "pattern",
            "severity": "high",
            "priority": 15,
            "conditions": {
                "logic": "and",
                "rules": [
                    {"field": "amount", "operator": "gt", "value": 5000},
                    {"field": "recent_info_change", "operator": "eq", "value": True},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "flag_transaction"},
                    {"type": "create_alert"},
                ],
            },
        },
        {
            "name": "Velocity Abuse",
            "description": "Detects unusually high transaction frequency within short time windows.",
            "category": "velocity",
            "severity": "medium",
            "priority": 20,
            "conditions": {
                "logic": "or",
                "rules": [
                    {"field": "txn_count_5m", "operator": "gt", "value": 3},
                    {"field": "txn_count_1h", "operator": "gt", "value": 15},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "flag_transaction"},
                    {"type": "create_alert"},
                ],
            },
        },
        {
            "name": "Geographic Anomaly",
            "description": "Flags transactions from sanctioned or high-risk countries.",
            "category": "geography",
            "severity": "high",
            "priority": 12,
            "conditions": {
                "logic": "and",
                "rules": [
                    {"field": "country_code", "operator": "in", "value": ["KP", "IR", "SY", "CU", "SD"]},
                ],
            },
            "actions": {
                "actions": [
                    {"type": "block_transaction"},
                    {"type": "create_alert"},
                    {"type": "notify", "channel": "email"},
                ],
            },
        },
    ]
