"""Action handlers for the rules engine.

Actions fire when a rule matches. Side-effect actions (notify, webhook) should
be dispatched via Celery in production — here they are stubbed as log entries.
"""

import uuid
from typing import Any

import structlog

logger = structlog.get_logger()


class ActionResult:
    def __init__(self, action_type: str, executed: bool, details: dict | None = None):
        self.action_type = action_type
        self.executed = executed
        self.details = details or {}

    def to_dict(self) -> dict:
        return {"type": self.action_type, "executed": self.executed, "details": self.details}


def execute_actions(
    actions_config: dict,
    *,
    rule_id: uuid.UUID,
    transaction: dict,
    dry_run: bool = False,
) -> list[ActionResult]:
    """Execute (or simulate in dry_run) the actions defined on a rule."""
    action_list = actions_config.get("actions", [])
    results: list[ActionResult] = []

    for action_def in action_list:
        action_type = action_def.get("type", "")
        handler = ACTION_HANDLERS.get(action_type, _handle_unknown)
        result = handler(action_def, rule_id=rule_id, transaction=transaction, dry_run=dry_run)
        results.append(result)

    return results


def _handle_create_alert(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    if dry_run:
        return ActionResult("create_alert", False, {"reason": "dry_run", "would_create": True})
    logger.info("action_create_alert", rule_id=str(rule_id), txn_id=transaction.get("id"))
    return ActionResult("create_alert", True, {"txn_id": transaction.get("id")})


def _handle_flag_transaction(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    if dry_run:
        return ActionResult("flag_transaction", False, {"reason": "dry_run"})
    logger.info("action_flag_transaction", rule_id=str(rule_id), txn_id=transaction.get("id"))
    return ActionResult("flag_transaction", True)


def _handle_block_transaction(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    if dry_run:
        return ActionResult("block_transaction", False, {"reason": "dry_run"})
    logger.info("action_block_transaction", rule_id=str(rule_id), txn_id=transaction.get("id"))
    return ActionResult("block_transaction", True)


def _handle_adjust_risk(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    delta = action.get("delta", 0.1)
    return ActionResult("adjust_risk_score", not dry_run, {"delta": delta})


def _handle_notify(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    if dry_run:
        return ActionResult("notify", False, {"reason": "dry_run"})
    logger.info("action_notify", rule_id=str(rule_id), channel=action.get("channel", "email"))
    return ActionResult("notify", True, {"channel": action.get("channel", "email")})


def _handle_webhook(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    if dry_run:
        return ActionResult("webhook", False, {"reason": "dry_run", "url": action.get("url")})
    logger.info("action_webhook", rule_id=str(rule_id), url=action.get("url"))
    return ActionResult("webhook", True, {"url": action.get("url")})


def _handle_unknown(action: dict, *, rule_id: uuid.UUID, transaction: dict, dry_run: bool) -> ActionResult:
    return ActionResult(action.get("type", "unknown"), False, {"reason": "unknown_action_type"})


ACTION_HANDLERS = {
    "create_alert": _handle_create_alert,
    "flag_transaction": _handle_flag_transaction,
    "block_transaction": _handle_block_transaction,
    "adjust_risk_score": _handle_adjust_risk,
    "notify": _handle_notify,
    "webhook": _handle_webhook,
}
