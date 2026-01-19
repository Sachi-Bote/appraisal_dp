
from .states import States, VALID_TRANSITIONS

def can_transition(current_state, new_state):
    return new_state in VALID_TRANSITIONS.get(current_state, [])


class WorkflowEngine:
    def __init__(self, initial_state):
        self.state = initial_state

    def transition(self, new_state):
        if not can_transition(self.state, new_state):
            raise ValueError(f"Invalid transition: {self.state} → {new_state}")
        self.state = new_state
        return self.state


ROLE_PERMISSIONS = {
    "faculty": ["submit", "resubmit"],
    "hod": ["submit", "resubmit", "hod_approve", "hod_reject"],
    "principal": ["principal_approve", "principal_reject"]
}



ACTIONS = {
    # SUBMISSION
    "submit": (States.DRAFT, States.SUBMITTED),
    "resubmit": (States.DRAFT, States.SUBMITTED),

    # HOD REVIEW
    "hod_approve": (States.SUBMITTED, States.HOD_APPROVED),
    "hod_reject": (States.SUBMITTED, States.DRAFT),

    # PRINCIPAL REVIEW
    "principal_approve": (States.HOD_APPROVED, States.PRINCIPAL_APPROVED),
    "principal_reject": (States.HOD_APPROVED, States.DRAFT),
}



def is_action_allowed(role, action):
    return action in ROLE_PERMISSIONS.get(role, [])


def perform_action(role, action, current_state):
    # 1. Role permission check
    if not is_action_allowed(role, action):
        raise PermissionError(
            f"Role '{role}' cannot perform '{action}'"
        )

    if action not in ACTIONS:
        raise ValueError("Invalid action")

    expected_current, new_state = ACTIONS[action]

    # 2. State check
    if current_state != expected_current:
        raise ValueError(
            f"Action '{action}' not allowed from state '{current_state}'"
        )

    # 3. Transition validation
    if not can_transition(current_state, new_state):
        raise ValueError(
            f"Invalid transition: {current_state} → {new_state}"
        )

    return new_state