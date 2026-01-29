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
TOP_LEVEL_REQUIRED = {
    "general",
    "teaching",
    "activities",
    "research",
    "pbas",
    "submit_action"
}


from typing import Dict, Tuple

def validate_full_form(payload: Dict, meta: Dict) -> Tuple[bool, str]:
    """
    Validate a full appraisal submission.

    payload  -> appraisal_data
    meta     -> request.data (academic_year, semester, form_type)
    """

    if not isinstance(payload, dict):
        return False, "appraisal_data must be a JSON object."

    # ---------- GENERAL ----------
    general = payload.get("general", {})
    if not isinstance(general, dict):
        return False, "general must be an object"

    required_general_fields = {"faculty_name", "department", "designation"}
    missing_general = required_general_fields - general.keys()
    if missing_general:
        return False, f"Missing general fields: {sorted(missing_general)}"

    # ---------- META ----------
    required_meta_fields = {"academic_year", "semester", "form_type"}
    missing_meta = required_meta_fields - meta.keys()
    if missing_meta:
        return False, f"Missing meta fields: {sorted(missing_meta)}"

    # ---------- TEACHING ----------
    ok, err = validate_teaching_input(payload["teaching"], meta.get("form_type"))
    if not ok:
        return False, f"Teaching validation failed: {err}"

    # ---------- ACTIVITIES ----------
    ok, err = validate_activities(payload["activities"])
    if not ok:
        return False, f"Activities validation failed: {err}"
    
     # ✅ ADD: PBAS Departmental Activities validation
    if meta.get("form_type") == "PBAS":
        dept_acts = payload.get("pbas", {}).get("departmental_activities", [])

        if not isinstance(dept_acts, list):
            return False, "Departmental activities must be a list"

        for idx, act in enumerate(dept_acts, start=1):
            if "credits_claimed" not in act:
                return False, f"Missing credits_claimed in departmental activity #{idx}"
            
    # ✅ ADD: PBAS Institute Activities validation
    if meta.get("form_type") == "PBAS":
        inst_acts = payload.get("pbas", {}).get("institute_activities", [])

        if not isinstance(inst_acts, list):
            return False, "Institute activities must be a list"

        for idx, act in enumerate(inst_acts, start=1):
            if "credits_claimed" not in act:
                return False, f"Missing credits_claimed in institute activity #{idx}"
            
    # ✅ ADD: PBAS Society Activities validation
    if meta.get("form_type") == "PBAS":
        society_acts = payload.get("pbas", {}).get("society_activities", [])

        if not isinstance(society_acts, list):
            return False, "Society activities must be a list"

        for idx, act in enumerate(society_acts, start=1):
            if "credits_claimed" not in act:
                return False, f"Missing credits_claimed in society activity #{idx}"


        # ✅ ADD: PBAS Student Feedback validation
    if meta.get("form_type") == "PBAS":
        feedback_entries = payload.get("pbas", {}).get("student_feedback", [])

        if not isinstance(feedback_entries, list):
            return False, "Student feedback must be a list"

        for idx, entry in enumerate(feedback_entries, start=1):
            if "feedback_score" not in entry:
                return False, f"Missing feedback_score in student_feedback #{idx}"

            try:
                score = float(entry["feedback_score"])
            except (TypeError, ValueError):
                return False, f"Invalid feedback_score in student_feedback #{idx}"

            if score < 0 or score > 25:
                return False, f"feedback_score must be between 0 and 25 in student_feedback #{idx}"

    

    # ---------- RESEARCH ----------
    ok, err = validate_research_payload(payload["research"])
    if not ok:
        return False, f"Research validation failed: {err}"

    # ---------- PBAS ----------
    ok, err = validate_pbas_scores(payload["pbas"])
    if not ok:
        return False, f"PBAS validation failed: {err}"

    # ---------- SANITY CHECK ----------
    research_sum = sum(int(v) for v in payload["research"].values() if isinstance(v, int))
    activity_sum = sum(int(v) for v in payload["activities"].values() if isinstance(v, int))

    if research_sum == 0 and activity_sum == 0:
        return False, "Submission appears empty: no research or activities."

    return True, ""
