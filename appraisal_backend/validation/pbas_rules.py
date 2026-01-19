# validation/pbas_rules.py
"""
Validations for PBAS 360° scoring buckets.
Expected payload:
{
  "teaching_process": 20,    # max 25
  "feedback": 22,            # max 25
  "department": 15,          # max 20
  "institute": 8,            # max 10
  "acr": 8,                  # max 10
  "society": 6               # max 10
}
"""

from typing import Dict, Tuple

LIMITS = {
    "teaching_process": 25,
    "feedback": 25,
    "department": 20,
    "institute": 10,
    "acr": 10,
    "society": 10,
}


def validate_pbas_scores(payload: Dict) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "PBAS payload must be a JSON object."

    missing = [k for k in LIMITS.keys() if k not in payload]
    if missing:
        return False, f"PBAS missing required score fields: {missing}"

    for key, max_val in LIMITS.items():
        val = payload.get(key)
        if not isinstance(val, (int, float)):
            return False, f"PBAS field '{key}' must be numeric."
        if val < 0 or val > max_val:
            return False, f"PBAS field '{key}' must be between 0 and {max_val}."

    return True, ""
