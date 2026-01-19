# scoring/pbas.py

def calculate_pbas_score(payload: dict) -> dict:
    """
    Payload is already validated and FINAL:
    {
        "teaching_process": int,
        "feedback": int,
        "department": int,
        "institute": int,
        "acr": int,
        "society": int
    }
    """

    total = sum(payload.values())

    return {
        "breakdown": payload,
        "total": total
    }