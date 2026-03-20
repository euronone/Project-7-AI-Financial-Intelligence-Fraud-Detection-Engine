"""Core rules engine evaluator.

Loads active rules ordered by priority, evaluates conditions against a transaction,
and executes matched actions. Designed to be called by the service layer.
"""

import uuid
from typing import Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.rules.actions import ActionResult, execute_actions
from app.rules.conditions import evaluate_condition_tree

logger = structlog.get_logger()


class RuleEvaluationResult:
    def __init__(
        self,
        rule_id: uuid.UUID,
        rule_name: str,
        matched: bool,
        condition_results: list[dict],
        action_results: list[dict],
        severity: str,
        priority: int,
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.matched = matched
        self.condition_results = condition_results
        self.action_results = action_results
        self.severity = severity
        self.priority = priority

    def to_dict(self) -> dict:
        return {
            "rule_id": str(self.rule_id),
            "rule_name": self.rule_name,
            "matched": self.matched,
            "severity": self.severity,
            "priority": self.priority,
            "conditions": self.condition_results,
            "actions": self.action_results,
        }


async def evaluate_transaction(
    db: AsyncSession,
    transaction: dict,
    *,
    dry_run: bool = False,
    rule_ids: list[uuid.UUID] | None = None,
) -> list[RuleEvaluationResult]:
    """Evaluate a transaction against all active rules (or specified rules).

    Returns a list of RuleEvaluationResult for every rule evaluated.
    """
    query = select(Rule).where(Rule.is_active == True).order_by(Rule.priority.asc())  # noqa: E712
    if rule_ids:
        query = select(Rule).where(Rule.id.in_(rule_ids)).order_by(Rule.priority.asc())

    result = await db.execute(query)
    rules = result.scalars().all()

    results: list[RuleEvaluationResult] = []

    for rule in rules:
        matched, condition_results = evaluate_condition_tree(rule.conditions, transaction)

        action_results: list[dict] = []
        if matched:
            actions = execute_actions(
                rule.actions,
                rule_id=rule.id,
                transaction=transaction,
                dry_run=dry_run,
            )
            action_results = [a.to_dict() for a in actions]

            if not dry_run:
                await db.execute(
                    update(Rule).where(Rule.id == rule.id).values(hit_count=Rule.hit_count + 1)
                )

        results.append(
            RuleEvaluationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                matched=matched,
                condition_results=condition_results,
                action_results=action_results,
                severity=rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
                priority=rule.priority,
            )
        )

    matched_count = sum(1 for r in results if r.matched)
    logger.info(
        "rules_evaluated",
        total=len(results),
        matched=matched_count,
        dry_run=dry_run,
    )

    return results


async def evaluate_single_rule(
    db: AsyncSession,
    rule_id: uuid.UUID,
    transaction: dict,
) -> RuleEvaluationResult:
    """Dry-run a single rule against a sample transaction (for rule testing)."""
    results = await evaluate_transaction(db, transaction, dry_run=True, rule_ids=[rule_id])
    if not results:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Rule", str(rule_id))
    return results[0]
