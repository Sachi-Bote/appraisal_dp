
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
    "hod": ["start_hod_review", "hod_approve", "hod_reject"],
    "principal": ["start_principal_review", "principal_approve", "principal_reject", "finalize"],
}



ACTIONS = {
    # FACULTY
    "submit": (States.DRAFT, States.SUBMITTED),
    "resubmit": (States.DRAFT, States.SUBMITTED),

    # HOD ACTIONS
    "start_hod_review": (States.SUBMITTED, States.HOD_REVIEW),
    "hod_approve": (States.HOD_REVIEW, States.HOD_APPROVED),
    "hod_reject": (States.HOD_REVIEW, States.DRAFT),

    # PRINCIPAL ACTIONS
    "start_principal_review": (States.HOD_APPROVED, States.PRINCIPAL_REVIEW),
    "principal_approve": (States.PRINCIPAL_REVIEW, States.PRINCIPAL_APPROVED),
    "principal_reject": (States.PRINCIPAL_REVIEW, States.DRAFT),

    # FINAL
    "finalize": (States.PRINCIPAL_APPROVED, States.FINALIZED),
}




def is_action_allowed(role, action):
    return action in ROLE_PERMISSIONS.get(role, [])


def perform_action(role, action, current_state):
    # normalize role
    role = role.lower()

    # ✅ normalize state correctly
    if isinstance(current_state, str):
        current_state = current_state.lower()

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
