from scoring.pbas import calculate_pbas_score
from scoring.research import calculate_research_score
from scoring.teaching import (
    calculate_teaching_score,          # SPPU (unchanged)
    aggregate_teaching_blocks,
    calculate_pbas_teaching_score
)
from scoring.activities import (
    calculate_sppu_activity_score,
    calculate_departmental_activity_score,
    calculate_institute_activity_score,
    calculate_society_activity_score
)

def calculate_full_score(payload: dict) -> dict:
    # ✅ PBAS Teaching
    teaching_blocks = payload.get("teaching", {}).get("courses", [])
    aggregated = aggregate_teaching_blocks(teaching_blocks)

    teaching_result = calculate_pbas_teaching_score(
        total_scheduled_classes=aggregated["total_scheduled"],
        total_held_classes=aggregated["total_held"],
    )

    # ✅ SPPU Activities (Yes / No)
    sppu_activity_result = calculate_sppu_activity_score(
        payload.get("activities", {})
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

    # ✅ Other sections
    research_result = calculate_research_score(payload.get("research", {}))
    pbas_result = calculate_pbas_score(payload.get("pbas", {}))

    # ✅ TOTAL SCORE
    total_score = (
    teaching_result["score"]
    + sppu_activity_result["score"]
    + pbas_departmental_result["total_awarded"]
    + pbas_institute_result["total_awarded"]
    + pbas_society_result["total_awarded"]
    + research_result["total"]
    + pbas_result["total"]
)

    return {
        "teaching": {
            **teaching_result,
            "total_scheduled": aggregated["total_scheduled"],
            "total_held": aggregated["total_held"],
            "course_count": aggregated["course_count"],
        },
        "activities": sppu_activity_result,
        "departmental_activities": pbas_departmental_result,
        "institute_activities": pbas_institute_result,
        "society_activities": pbas_society_result,
        "research": research_result,
        "pbas": pbas_result,
        "total_score": total_score,
    }

