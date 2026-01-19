# validation/exceptions.py
class ValidationError(Exception):
    """Raised when validation fails with a message."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message
