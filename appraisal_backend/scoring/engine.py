from scoring.pbas import calculate_pbas_score
from scoring.research import calculate_research_score
from scoring.teaching import (
    calculate_teaching_score,          # SPPU (unchanged)
    aggregate_teaching_blocks,
    calculate_pbas_teaching_score
)
from scoring.activities import calculate_activity_score


def calculate_full_score(payload: dict) -> dict:
    # ✅ PBAS Teaching
    teaching_blocks = payload["teaching"]["courses"]
    aggregated = aggregate_teaching_blocks(teaching_blocks)

    teaching_result = calculate_pbas_teaching_score(
        total_scheduled_classes=aggregated["total_scheduled"],
        total_held_classes=aggregated["total_held"],
    )

    # unchanged sections
    activity_result = calculate_activity_score(payload["activities"])
    research_result = calculate_research_score(payload["research"])
    pbas_result = calculate_pbas_score(payload["pbas"])

    total_score = (
        teaching_result["score"]
        + activity_result["score"]
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
        "activities": activity_result,
        "research": research_result,
        "pbas": pbas_result,
        "total_score": total_score,
    }
