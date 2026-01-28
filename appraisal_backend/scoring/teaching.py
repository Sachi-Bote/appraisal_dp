# scoring/teaching.py
from decimal import Decimal, ROUND_HALF_UP
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


def aggregate_teaching_blocks(blocks: list[dict]) -> dict:
    """
    Input (from frontend):
    [
        {
            "semester": "1/2024-25",
            "course_code": "CS101",
            "scheduled_classes": 40,
            "held_classes": 38
        },
        {
            "semester": "1/2024-25",
            "course_code": "CS102",
            "scheduled_classes": 44,
            "held_classes": 42
        }
    ]

    Output:
    {
        "course_count": 2,
        "total_scheduled": 84,
        "total_held": 80
    }
    """

    total_scheduled = 0
    total_held = 0

    for block in blocks:
        total_scheduled += int(block.get("scheduled_classes", 0))
        total_held += int(block.get("held_classes", 0))

    return {
        "course_count": len(blocks),
        "total_scheduled": total_scheduled,
        "total_held": total_held,
    }




PBAS_MAX_TEACHING_SCORE = Decimal("25.00")


def calculate_pbas_teaching_score(
    total_scheduled_classes: int,
    total_held_classes: int,
) -> dict:
    """
    PBAS Teaching Process Score (Max 25)

    Input:
    - total_scheduled_classes
    - total_held_classes

    Output:
    {
        "attendance_percentage": Decimal,
        "score": Decimal
    }
    """

    if total_scheduled_classes <= 0:
        return {
            "attendance_percentage": Decimal("0.00"),
            "score": Decimal("0.00"),
        }

    attendance_percentage = (
        Decimal(total_held_classes)
        / Decimal(total_scheduled_classes)
        * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    score = (
        attendance_percentage
        / Decimal("100")
        * PBAS_MAX_TEACHING_SCORE
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Hard cap at max
    if score > PBAS_MAX_TEACHING_SCORE:
        score = PBAS_MAX_TEACHING_SCORE

    return {
        "attendance_percentage": attendance_percentage,
        "score": score,
    }

