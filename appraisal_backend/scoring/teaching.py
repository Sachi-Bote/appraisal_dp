# scoring/teaching.py

def calculate_teaching_percentage(classes_taught: int, total_classes: int) -> float:
    if total_classes == 0:
        return 0.0
    return (classes_taught / total_classes) * 100


def calculate_teaching_grade(percentage: float) -> str:
    if percentage >= 80:
        return "Good"
    elif percentage >= 70:
        return "Satisfactory"
    else:
        return "Not Satisfactory"


def calculate_teaching_score(payload: dict) -> dict:
    """
    Input:
    {
        "total_classes_assigned": 100,
        "classes_taught": 90
    }
    Output:
    {
        "percentage": 90.0,
        "grade": "Good",
        "score": 10   # example scoring weight
    }
    """

    total_classes = payload["total_classes_assigned"]
    taught = payload["classes_taught"]

    percentage = calculate_teaching_percentage(taught, total_classes)
    grade = calculate_teaching_grade(percentage)

    # Default score-mapping (you can adjust to actual SPPU rule)
    score_map = {"Good": 10, "Satisfactory": 5, "Not Satisfactory": 0}
    score = score_map[grade]

    return {
        "percentage": percentage,
        "grade": grade,
        "score": score,
    }
