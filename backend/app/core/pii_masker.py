from __future__ import annotations

import copy
import re
from typing import Any

PII_FIELDS: list[str] = [
    "email",
    "phone",
    "card_number",
    "ssn",
    "ip_address",
    "first_name",
    "last_name",
]

_FIELD_MASKERS: dict[str, str] = {
    "email": "mask_email",
    "phone": "mask_phone",
    "card_number": "mask_card",
    "ssn": "mask_card",
    "ip_address": "mask_ip",
    "first_name": "mask_name",
    "last_name": "mask_name",
}


def mask_email(email: str) -> str:
    """``j***@example.com``"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    return f"{local[0]}***@{domain}" if local else f"***@{domain}"


def mask_phone(phone: str) -> str:
    """``***1234``"""
    digits = re.sub(r"\D", "", phone)
    return f"***{digits[-4:]}" if len(digits) >= 4 else "***"


def mask_card(card_number: str) -> str:
    """``****1234``"""
    digits = re.sub(r"\D", "", card_number)
    return f"****{digits[-4:]}" if len(digits) >= 4 else "****"


def mask_ip(ip: str) -> str:
    """``192.168.***.**``"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.**"
    return "***"


def mask_name(name: str) -> str:
    """``J***``"""
    if not name:
        return "***"
    return f"{name[0]}***"


def mask_dict(
    data: dict[str, Any],
    fields_to_mask: list[str] | None = None,
) -> dict[str, Any]:
    """Recursively mask PII fields inside a dictionary.

    Args:
        data: Dictionary potentially containing PII values.
        fields_to_mask: Field names to mask.  Defaults to ``PII_FIELDS``.

    Returns:
        A deep copy of *data* with sensitive values replaced by masked versions.
    """
    if fields_to_mask is None:
        fields_to_mask = PII_FIELDS

    result = copy.deepcopy(data)
    _mask_recursive(result, set(fields_to_mask))
    return result


def _mask_recursive(obj: Any, fields: set[str]) -> None:
    if isinstance(obj, dict):
        for key in obj:
            if key in fields and isinstance(obj[key], str):
                masker_name = _FIELD_MASKERS.get(key)
                if masker_name:
                    masker = globals()[masker_name]
                    obj[key] = masker(obj[key])
                else:
                    obj[key] = "***"
            else:
                _mask_recursive(obj[key], fields)
    elif isinstance(obj, list):
        for item in obj:
            _mask_recursive(item, fields)
