from scoring.pbas import calculate_pbas_score
from scoring.research import calculate_research_score

from scoring.teaching import (
    aggregate_teaching_blocks,
    calculate_pbas_teaching_score,
    calculate_sppu_teaching_score,
    SPPU_ATTENDANCE_SCORE_MAP,
)
from decimal import Decimal, ROUND_HALF_UP
from scoring.activities import (
    calculate_sppu_activity_score,
    calculate_departmental_activity_score,
    calculate_institute_activity_score,
    calculate_society_activity_score,
    calculate_student_feedback_score
)

from scoring.activities import calculate_institute_acr_score

def calculate_full_score(payload: dict) -> dict:
    


    # ✅ PBAS Teaching
    # ✅ PBAS Teaching (Category I – Max 25)
    teaching_blocks = payload.get("teaching", {}).get("courses", [])
    aggregated = aggregate_teaching_blocks(teaching_blocks)

    teaching_result = calculate_pbas_teaching_score(
        total_scheduled_classes=Decimal(aggregated["total_scheduled"]),
        total_held_classes=Decimal(aggregated["total_held"]),
    )

# ✅ SPPU Teaching (Attendance rating only)
    teaching_result_sppu = calculate_sppu_teaching_score(
        total_scheduled_classes=aggregated["total_scheduled"],
        total_held_classes=aggregated["total_held"],
    )

    teaching_sppu_score = Decimal(
        SPPU_ATTENDANCE_SCORE_MAP.get(
        teaching_result_sppu["rating"], 0
    )
)
    print("\n========== TEACHING DEBUG ==========")
    print("Total classes assigned:", aggregated["total_scheduled"])
    print("Classes taught:", aggregated["total_held"])
    print("Attendance %:", teaching_result["attendance_percentage"])
    print("Teaching score:", teaching_result["score"])


    # ✅ SPPU Activities (Yes / No)
    sppu_activity_result = calculate_sppu_activity_score(
        payload.get("activities", {})
    )

    feedback_result = calculate_student_feedback_score(
    payload.get("pbas", {}).get("student_feedback", [])
    )

    # ✅ PBAS Departmental Activities
    pbas_departmental_result = calculate_departmental_activity_score(
        payload.get("pbas", {}).get("departmental_activities", [])
    )

    pbas_institute_result = calculate_institute_activity_score(
    payload.get("pbas", {}).get("institute_activities", [])
    )

    # PBAS Society Activities
    pbas_society_result = calculate_society_activity_score(
    payload.get("pbas", {}).get("society_activities", [])
    )

    acr_result = calculate_institute_acr_score(
    payload["acr"]["grade"]
)


    # ✅ Other sections
    research_result = calculate_research_score(payload.get("research", {}))
    pbas_result = calculate_pbas_score(payload.get("pbas", {}))


    # ✅ TOTAL SCORE


    total_score = (
    Decimal(str(teaching_result["score"]))
    +teaching_sppu_score
    + Decimal(str(sppu_activity_result["score"]))
    + Decimal(str(feedback_result["score"]))
    + Decimal(str(pbas_departmental_result["total_awarded"]))
    + Decimal(str(pbas_institute_result["total_awarded"]))
    + Decimal(str(pbas_society_result["total_awarded"]))
    + Decimal(str(research_result["total"]))
    + Decimal(str(pbas_result["total"]))
    + Decimal(str(acr_result["credit_point"]))
)


    return {
        "teaching": {
            **teaching_result,
            "total_scheduled": aggregated["total_scheduled"],
            "total_held": aggregated["total_held"],
            "course_count": aggregated["course_count"],
        },
        "activities": sppu_activity_result,
        "student_feedback": feedback_result,
        "departmental_activities": pbas_departmental_result,
        "institute_activities": pbas_institute_result,
        "society_activities": pbas_society_result,
        "research": research_result,
        "pbas": pbas_result,
        "total_score": total_score,
        "acr" : acr_result,
    }

