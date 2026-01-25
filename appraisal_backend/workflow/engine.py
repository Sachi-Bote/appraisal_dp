
from .states import States, VALID_TRANSITIONS


def can_transition(current_state, new_state):
    """
    Check if a state transition is allowed.
    """
    return new_state in VALID_TRANSITIONS.get(current_state, [])


class WorkflowEngine:
    def __init__(self, initial_state):
        self.state = initial_state

    def transition(self, new_state):
        if not can_transition(self.state, new_state):
            raise ValueError(
                f"Invalid transition: {self.state} → {new_state}"
            )
        self.state = new_state
        return self.state


def perform_action(*, current_state, next_state):
    """
    Core workflow transition validator.
    This is the SINGLE source of truth.
    """

    if current_state not in VALID_TRANSITIONS:
        raise ValueError(
            f"No transitions defined from state '{current_state}'"
        )

    if next_state not in VALID_TRANSITIONS[current_state]:
        raise ValueError(
            f"Transition not allowed: {current_state} → {next_state}"
        )

    return next_state
