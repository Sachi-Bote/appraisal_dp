# validation/master_validator.py
"""
Master validator that orchestrates validations across all sections.
This exposes `validate_full_form(payload)` which returns (ok, error_message_or_empty).
"""

from typing import Dict, Tuple

from .global_rules import ensure_keys_present, validate_required_fields
from .teaching_rules import validate_teaching_input
from .activity_rules import validate_activities
from .research_rules import validate_research_payload
from .pbas_rules import validate_pbas_scores

# Top-level required keys for a single appraisal submission payload
TOP_LEVEL_REQUIRED = {"faculty_id", "year", "teaching", "activities", "research", "pbas", "submit_action", "role"}


def validate_full_form(payload: Dict) -> Tuple[bool, str]:
    """
    Validate a full appraisal submission payload.

    Expected top-level shape:
    {
      "faculty_id": 1,
      "year": 2024,
      "teaching": { ... },
      "activities": { ... },
      "research": { ... },
      "pbas": { ... },
      "submit_action": "submit",
      "role": "faculty"
    }
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object."

    ok, err = ensure_keys_present(payload, TOP_LEVEL_REQUIRED)
    if not ok:
        return False, err


    # Validate tutorial / teaching block
    ok, err = validate_teaching_input(payload["teaching"])
    if not ok:
        return False, f"Teaching validation failed: {err}"

    # Validate activities
    ok, err = validate_activities(payload["activities"])
    if not ok:
        return False, f"Activities validation failed: {err}"

    # Validate research
    ok, err = validate_research_payload(payload["research"])
    if not ok:
        return False, f"Research validation failed: {err}"

    # Validate PBAS
    ok, err = validate_pbas_scores(payload["pbas"])
    if not ok:
        return False, f"PBAS validation failed: {err}"

    # Optional: Additional sanity checks
    # e.g., ensure at least one positive contribution in research or activities to avoid empty submission
    try:
        research_sum = sum(int(v) for v in payload["research"].values())
    except Exception:
        research_sum = 0

    if research_sum == 0 and all(not v for v in payload["activities"].values()):
        # Not fatal — depends on policy. Here we warn/fail to avoid empty forms.
        return False, "Submission appears empty: no research items and no activities flagged."

    return True, ""
