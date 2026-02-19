from typing import Dict, Tuple
from scoring.activity_selection import validate_activity_payload

def validate_activities(payload: Dict) -> Tuple[bool, str]:
    return validate_activity_payload(payload)
