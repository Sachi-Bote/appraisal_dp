#Total Number of Activities = 7
#Total Number of Activies teacher participated in : User Input
from typing import Dict, Tuple
from .global_rules import is_boolean

def validate_activities(payload: Dict) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Activities payload must be a JSON object"
    
    if not payload:
        return True, ""
    
    for key, value in payload.items():
        if not is_boolean(value):
            return False, f"Activity field '{key}' must be a boolean (true or false)"
        
    return True, ""
