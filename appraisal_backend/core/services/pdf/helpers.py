def safe_text(value, default=""):
    """
    Ensures reportlab always gets a string.
    """
    if value is None:
        return default
    return str(value)
