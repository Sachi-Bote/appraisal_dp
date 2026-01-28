from typing import Dict, Tuple
from .global_rules import is_non_negative_int, validate_required_fields

REQUIRED_FIELDS = ["total_classes_assigned", "classes_taught"]

def validate_teaching_input(payload: Dict, form_type: str) -> Tuple[bool, str]:
    # ✅ PBAS Teaching validation
    if form_type == "PBAS":
        if "courses" not in payload:
            return False, "Teaching validation failed: 'courses' is required for PBAS"

        if not isinstance(payload["courses"], list) or not payload["courses"]:
            return False, "Teaching validation failed: courses must be a non-empty list"

        for idx, course in enumerate(payload["courses"], start=1):
            if "scheduled_classes" not in course or "held_classes" not in course:
                return False, f"Teaching validation failed: course {idx} missing class data"

            if (
                not is_non_negative_int(course["scheduled_classes"])
                or not is_non_negative_int(course["held_classes"])
            ):
                return False, f"Teaching validation failed: invalid class numbers in course {idx}"

            if course["scheduled_classes"] == 0:
                return False, f"Teaching validation failed: scheduled_classes must be > 0 (course {idx})"

            if course["held_classes"] > course["scheduled_classes"]:
                return False, f"Teaching validation failed: held_classes > scheduled_classes (course {idx})"

        return True, ""

    # ✅ SPPU Teaching validation (OLD – KEEP EXACTLY)
    ok, err = validate_required_fields(payload, REQUIRED_FIELDS)
    if not ok:
        return False, err
    
    total = payload["total_classes_assigned"]
    taught = payload["classes_taught"]

    if not is_non_negative_int(total) or not is_non_negative_int(taught):
        return False, "Both 'total_class_assigned' and 'classes_taught' must be non-negative integers"
    
    if total == 0:
        return False, "'total_class_assigned' must be greater than zero"
    
    if taught > total:
        return False, "'classes_taught' cannot be greater than 'total_class_assigned'"
    
    return True, ""
