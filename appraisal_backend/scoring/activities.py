from decimal import Decimal, InvalidOperation
from scoring.activity_selection import normalize_activity_payload


def calculate_sppu_activity_score(payload: dict) -> dict:
    """
    Input:
    {
      "administrative_responsibility": True,
      "exam_duties": False,
      "student_related": True,
      ...
    }
    """

    normalized = normalize_activity_payload(payload)
    yes_count = int(normalized.get("yes_count", 0))

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
        "score": score,
        "flags": normalized.get("section_flags", {}),
    }


def calculate_student_feedback_score(feedback_entries: list) -> dict:
    """
    Input:
    [
      { "feedback_score": 18.5 },
      { "feedback_score": 17.0 }
    ]
    """

    if not feedback_entries:
        return {
            "total": 0,
            "average": 0,
            "count": 0,
        }

    total = sum(float(e["feedback_score"]) for e in feedback_entries)
    count = len(feedback_entries)
    average = round(total / count, 2)

    # PBAS allows max 25
    final_score = min(round(total, 2), 25)

    return {
        "count": count,
        "total": round(total, 2),
        "average": average,
        "score": final_score,
    }


def _to_decimal_or_invalid(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("-1")


def calculate_departmental_activity_score(payload: list) -> dict:
    """
    Section C: Departmental Activities (Max credit 20)
    Criteria in provided table: 3 points per activity/semester/event.
    """

    max_credit = Decimal("20")
    per_activity_max = Decimal("3")

    total_claimed = Decimal("0")
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = _to_decimal_or_invalid(activity.get("credits_claimed", 0))

        if credits < 0 or credits > per_activity_max:
            raise ValueError(
                f"Invalid credits for departmental activity #{idx} "
                f"(must be between 0 and 3)"
            )

        total_claimed += credits
        validated_activities.append(
            {
                "activity_code": activity.get("activity_code"),
                "activity_name": activity.get("activity_name") or activity.get("activity"),
                "semester": activity.get("semester"),
                "credits_claimed": float(credits),
            }
        )

    total_awarded = min(total_claimed, max_credit)

    return {
        "activities": validated_activities,
        "total_claimed": float(total_claimed),
        "total_awarded": float(total_awarded),
        "max_credit": float(max_credit),
    }


def _normalize_institute_activity_key(activity: dict) -> str:
    code = str(activity.get("activity_code", "") or "").strip().upper()
    name = str(activity.get("activity_name", "") or activity.get("activity", "") or "").strip().upper()
    text = f"{code} {name}"

    if "HOD" in text or "DEAN" in text:
        return "HOD_DEAN"
    if "COORDINATOR" in text and any(k in text for k in ("APPOINTED", "HEAD OF INSTITUTE", "HOI")):
        return "COORDINATOR_APPOINTED_BY_HOI"
    if "ORGANIZED" in text and "CONFERENCE" in text:
        return "ORGANIZED_CONFERENCE"
    if any(k in text for k in ("FDP", "CO-COORDINATOR", "COORDINATOR")) and "CONFERENCE" in text:
        return "FDP_CONFERENCE_COORDINATOR"

    return code


def calculate_institute_activity_score(payload: list) -> dict:
    """
    Section D: Institute Activities (Max credit 10)
    Criteria caps from provided table:
    - HoD / Dean: 4
    - Coordinator appointed by Head of Institute: 2
    - Organized Conference: 2
    - FDP/Conference coordination: 1 (can be fractional split)
    """

    max_credit = Decimal("10")
    default_per_activity_max = Decimal("4")
    institute_activity_caps = {
        "HOD_DEAN": Decimal("4"),
        "COORDINATOR_APPOINTED_BY_HOI": Decimal("2"),
        "ORGANIZED_CONFERENCE": Decimal("2"),
        "FDP_CONFERENCE_COORDINATOR": Decimal("1"),
    }

    total_claimed = Decimal("0")
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = _to_decimal_or_invalid(activity.get("credits_claimed", 0))
        activity_key = _normalize_institute_activity_key(activity)
        per_activity_max = institute_activity_caps.get(activity_key, default_per_activity_max)

        if credits < 0 or credits > per_activity_max:
            raise ValueError(
                f"Invalid credits for institute activity #{idx} "
                f"(must be between 0 and {per_activity_max})"
            )

        total_claimed += credits
        validated_activities.append(
            {
                "activity_code": activity.get("activity_code"),
                "activity_name": activity.get("activity_name") or activity.get("activity"),
                "semester": activity.get("semester"),
                "credits_claimed": float(credits),
            }
        )

    total_awarded = min(total_claimed, max_credit)

    return {
        "activities": validated_activities,
        "total_claimed": float(total_claimed),
        "total_awarded": float(total_awarded),
        "max_credit": float(max_credit),
    }


def calculate_society_activity_score(payload: list) -> dict:
    """
    Section F: Contribution to Society (Max credit 10)
    Criteria in provided table: 5 points per activity.
    """

    max_credit = Decimal("10")
    per_activity_max = Decimal("5")

    total_claimed = Decimal("0")
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = _to_decimal_or_invalid(activity.get("credits_claimed", 0))

        if credits < 0 or credits > per_activity_max:
            raise ValueError(
                f"Invalid credits for society activity #{idx} "
                f"(must be between 0 and 5)"
            )

        total_claimed += credits
        validated_activities.append(
            {
                "activity_code": activity.get("activity_code"),
                "activity_name": activity.get("activity_name") or activity.get("activity"),
                "semester": activity.get("semester"),
                "credits_claimed": float(credits),
            }
        )

    total_awarded = min(total_claimed, max_credit)

    return {
        "activities": validated_activities,
        "total_claimed": float(total_claimed),
        "total_awarded": float(total_awarded),
        "max_credit": float(max_credit),
    }


ACR_GRADE_SCORE_MAP = {
    "A+": Decimal("10"),
    "A": Decimal("8"),
    "B": Decimal("6"),
    "C": Decimal("4"),
}


def calculate_institute_acr_score(grade) -> dict:
    grade_str = str(grade).strip().upper()

    if grade_str in ACR_GRADE_SCORE_MAP:
        return {
            "activity": "ACR",
            "grade": grade_str,
            "credit_point": ACR_GRADE_SCORE_MAP[grade_str],
        }

    try:
        val = float(grade_str)
        if 8 <= val <= 10:
            return {"activity": "ACR", "grade": "A+", "credit_point": Decimal("10")}
        if 6 <= val < 8:
            return {"activity": "ACR", "grade": "A", "credit_point": Decimal("8")}
        if 4 <= val < 6:
            return {"activity": "ACR", "grade": "B", "credit_point": Decimal("6")}
        return {"activity": "ACR", "grade": "C", "credit_point": Decimal("4")}
    except Exception:
        return {
            "activity": "ACR",
            "grade": grade_str,
            "credit_point": Decimal("0"),
        }
