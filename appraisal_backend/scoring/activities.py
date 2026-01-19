# scoring/activities.py

def calculate_activity_score(payload: dict) -> dict:
    """
    Input:
    {
      "activity_a": True,
      "activity_b": False,
      "activity_c": True,
      ...
    }
    """

    yes_count = sum(1 for v in payload.values() if v is True)

    if yes_count >= 3:
        grade = "Good"
        score = 10
    elif yes_count >= 1:
        grade = "Satisfactory"
        score = 5
    else:
        grade = "Not Satisfactory"
        score = 0

    return {
        "yes_count": yes_count,
        "grade": grade,
        "score": score
    }
