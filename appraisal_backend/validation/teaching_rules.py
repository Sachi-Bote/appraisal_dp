from typing import Dict, Tuple
from .global_rules import is_non_negative_int, validate_required_fields

REQUIRED_FIELDS = ["total_classes_assigned", "classes_taught"]

def validate_teaching_input(payload: Dict) -> Tuple[bool, str]:
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
