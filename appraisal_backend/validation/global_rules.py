# validation/global_rules.py
"""
Reusable generic validators and helper utilities.
"""

from typing import Iterable, Tuple, List, Dict, Any


def is_positive_number(value) -> bool:
    return isinstance(value, (int, float)) and value >= 0


def is_non_negative_int(value) -> bool:
    return isinstance(value, int) and value >= 0


def is_boolean(value) -> bool:
    return isinstance(value, bool)


def validate_required_fields(data: Dict[str, Any], fields: Iterable[str]) -> Tuple[bool, str]:
    """Ensure required keys exist (non-null). Returns (ok, error_message_or_empty)."""
    missing = [f for f in fields if f not in data or data[f] is None]
    if missing:
        return False, f"Missing required fields: {missing}"
    return True, ""


def ensure_keys_present(data: Dict[str, Any], expected_keys: Iterable[str]) -> Tuple[bool, str]:
    """Check top-level expected keys are present in a mapping."""
    missing = [k for k in expected_keys if k not in data]
    if missing:
        return False, f"Expected keys missing: {missing}"
    return True, ""

