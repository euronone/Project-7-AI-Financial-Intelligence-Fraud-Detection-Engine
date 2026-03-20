"""Condition evaluation for the rules engine.

Supports operators: eq, ne, gt, gte, lt, lte, in, not_in, between, contains, mod.
Conditions are applied against a flat transaction dict.
"""

from decimal import Decimal
from typing import Any

OPERATORS = {
    "eq", "ne", "gt", "gte", "lt", "lte",
    "in", "not_in", "between", "contains", "mod",
}


def evaluate_condition(condition: dict, txn: dict) -> bool:
    """Evaluate a single condition against a transaction dict.

    condition shape: {"field": str, "operator": str, "value": any}
    """
    field = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    if not field or not operator or operator not in OPERATORS:
        return False

    actual = txn.get(field)
    if actual is None and operator not in ("eq", "ne"):
        return False

    try:
        return _apply_operator(operator, _to_comparable(actual), expected)
    except (TypeError, ValueError):
        return False


def evaluate_condition_tree(tree: dict, txn: dict) -> tuple[bool, list[dict]]:
    """Evaluate a condition tree (AND/OR groups) and return (matched, per-condition results).

    tree shape: {"logic": "and"|"or", "rules": [condition | nested_tree]}
    If tree has no "logic" key, it is treated as a flat list of AND-ed conditions
    via the "rules" key.
    """
    logic = tree.get("logic", "and")
    rules = tree.get("rules", [])

    results: list[dict] = []
    passes: list[bool] = []

    for rule in rules:
        if "rules" in rule and "field" not in rule:
            nested_match, nested_results = evaluate_condition_tree(rule, txn)
            results.extend(nested_results)
            passes.append(nested_match)
        else:
            passed = evaluate_condition(rule, txn)
            results.append({**rule, "passed": passed})
            passes.append(passed)

    if logic == "or":
        matched = any(passes) if passes else False
    else:
        matched = all(passes) if passes else False

    return matched, results


def _to_comparable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _apply_operator(op: str, actual: Any, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "gt":
        return float(actual) > float(expected)
    if op == "gte":
        return float(actual) >= float(expected)
    if op == "lt":
        return float(actual) < float(expected)
    if op == "lte":
        return float(actual) <= float(expected)
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "between":
        low, high = expected
        return float(low) <= float(actual) <= float(high)
    if op == "contains":
        return str(expected).lower() in str(actual).lower()
    if op == "mod":
        return float(actual) % float(expected) == 0
    return False
