from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data


def get_sppu_pdf_data(appraisal: Appraisal) -> Dict:
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})

    teaching = raw.get("teaching", {})
    activities = raw.get("activities", {})
    research = raw.get("research", {})
    scores = raw.get("scores", {})

    total_assigned = teaching.get("total_classes_assigned", 0)
    total_taught = teaching.get("classes_taught", 0)

    percentage = teaching.get("percentage")
    if percentage is None and total_assigned:
        percentage = round((total_taught / total_assigned) * 100, 2)
    elif percentage is None:
        percentage = 0

    return {
        **base,

        "teaching": {
            "total_assigned": total_assigned,
            "total_taught": total_taught,
            "percentage": f"{percentage}%",
            "grade": teaching.get("grade", ""),
            "verified_grade": "Good" if appraisal.principal else "",
        },

        "activities": {
            "list": activities.get("list", []),
            "grade": activities.get("grade", ""),
            "verified_grade": "",
        },

        "research": {
            "journal_count": research.get("journal_count", 0),
            "conference_count": research.get("conference_count", 0),
            "total": (
                research.get("journal_count", 0)
                + research.get("conference_count", 0)
            ),
            "verified": "",
        },

        "scores": {
            "overall_grade": scores.get("overall_grade", ""),
        },
    }
