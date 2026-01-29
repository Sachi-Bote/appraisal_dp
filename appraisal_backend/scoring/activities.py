# scoring/activities.py

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

    # Count only explicit True values
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




def calculate_departmental_activity_score(payload: list) -> dict:
    """
    Input:
    [
      {
        "activity_code": "LAB_IN_CHARGE",
        "activity_name": "Lab In charge",
        "semester": "1/2024-25",
        "credits_claimed": 3
      },
      ...
    ]
    """

    MAX_CREDIT = 20
    PER_ACTIVITY_MAX = 3

    total_claimed = 0
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = activity.get("credits_claimed", 0)

        # 🔒 Validation
        if not isinstance(credits, int) or credits < 0 or credits > PER_ACTIVITY_MAX:
            raise ValueError(
                f"Invalid credits for departmental activity #{idx} "
                f"(must be between 0 and 3)"
            )

        total_claimed += credits

        validated_activities.append({
            "activity_code": activity.get("activity_code"),
            "activity_name": activity.get("activity_name"),
            "semester": activity.get("semester"),
            "credits_claimed": credits
        })

    total_awarded = min(total_claimed, MAX_CREDIT)

    return {
        "activities": validated_activities,
        "total_claimed": total_claimed,
        "total_awarded": total_awarded,
        "max_credit": MAX_CREDIT
    }


# scoring/activities.py

def calculate_institute_activity_score(payload: list) -> dict:
    """
    Input:
    [
      {
        "activity_code": "HOD_DEAN",
        "activity_name": "HoD / Dean",
        "semester": "1/2024-25",
        "credits_claimed": 4
      },
      ...
    ]
    """

    MAX_CREDIT = 10
    PER_ACTIVITY_MAX = 4

    total_claimed = 0
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = activity.get("credits_claimed", 0)

        # 🔒 Validation
        if not isinstance(credits, int) or credits < 0 or credits > PER_ACTIVITY_MAX:
            raise ValueError(
                f"Invalid credits for institute activity #{idx} "
                f"(must be between 0 and 4)"
            )

        total_claimed += credits

        validated_activities.append({
            "activity_code": activity.get("activity_code"),
            "activity_name": activity.get("activity_name"),
            "semester": activity.get("semester"),
            "credits_claimed": credits
        })

    total_awarded = min(total_claimed, MAX_CREDIT)

    return {
        "activities": validated_activities,
        "total_claimed": total_claimed,
        "total_awarded": total_awarded,
        "max_credit": MAX_CREDIT
    }


# scoring/activities.py

def calculate_society_activity_score(payload: list) -> dict:
    """
    Input:
    [
      {
        "activity_code": "BLOOD_DONATION",
        "activity_name": "Blood Donation Activity organization",
        "semester": "2024-25",
        "credits_claimed": 5
      },
      ...
    ]
    """

    MAX_CREDIT = 10
    PER_ACTIVITY_MAX = 5

    total_claimed = 0
    validated_activities = []

    for idx, activity in enumerate(payload, start=1):
        credits = activity.get("credits_claimed", 0)

        # 🔒 Validation
        if not isinstance(credits, int) or credits < 0 or credits > PER_ACTIVITY_MAX:
            raise ValueError(
                f"Invalid credits for society activity #{idx} "
                f"(must be between 0 and 5)"
            )

        total_claimed += credits

        validated_activities.append({
            "activity_code": activity.get("activity_code"),
            "activity_name": activity.get("activity_name"),
            "semester": activity.get("semester"),
            "credits_claimed": credits
        })

    total_awarded = min(total_claimed, MAX_CREDIT)

    return {
        "activities": validated_activities,
        "total_claimed": total_claimed,
        "total_awarded": total_awarded,
        "max_credit": MAX_CREDIT
    }
