# scoring/teaching.py
from decimal import Decimal, ROUND_HALF_UP

def calculate_teaching_percentage(classes_taught: int, total_classes: int) -> float:
    if total_classes == 0:
        return 0.0
    return (classes_taught / total_classes) * 100


SPPU_ATTENDANCE_SCORE_MAP = {
    "Good": 10,
    "Satisfactory": 7,
    "Not Satisfactory": 0
}


def calculate_sppu_teaching_score(
    total_scheduled_classes: int,
    total_held_classes: int
) -> dict:
    if total_scheduled_classes <= 0:
        return {
            "attendance_percentage": Decimal("0.00"),
            "rating": "Not Satisfactory"
        }

    attendance_percentage = (
        Decimal(total_held_classes)
        / Decimal(total_scheduled_classes)
        * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if attendance_percentage >= Decimal("80.00"):
        rating = "Good"
    elif attendance_percentage >= Decimal("70.00"):
        rating = "Satisfactory"
    else:
        rating = "Not Satisfactory"

    return {
        "attendance_percentage": attendance_percentage,
        "rating": rating
    }



def aggregate_teaching_blocks(blocks: list[dict]) -> dict:
    total_scheduled = 0
    total_held = 0

    for block in blocks:
        total_scheduled += int(block.get("total_classes_assigned", 0))
        total_held += int(block.get("classes_taught", 0))

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

