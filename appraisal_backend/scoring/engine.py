# scoring/engine.py

from .teaching import calculate_teaching_score
from .activities import calculate_activity_score
from .research import calculate_research_score
from .pbas import calculate_pbas_score


def calculate_full_score(payload: dict) -> dict:
    """
    Expected payload (already validated):

    {
        "teaching": {...},
        "activities": {...},
        "research": {...},
        "pbas": {
            "teaching_process": int,
            "feedback": int,
            "department": int,
            "institute": int,
            "acr": int,
            "society": int
        }
    }
    """

    teaching_result = calculate_teaching_score(payload["teaching"])
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
        "teaching": teaching_result,
        "activities": activity_result,
        "research": research_result,
        "pbas": pbas_result,
        "total_score": total_score
    }