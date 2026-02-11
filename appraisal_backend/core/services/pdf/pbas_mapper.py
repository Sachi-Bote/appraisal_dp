from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data


def get_pbas_pdf_data(appraisal: Appraisal) -> Dict:
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})

    pbas = raw.get("pbas", {})

    teaching_rows = pbas.get("teaching_process", [])
    if not isinstance(teaching_rows, list):
        teaching_rows = raw.get("teaching", {}).get("courses", [])

    feedback_rows = pbas.get("student_feedback", pbas.get("students_feedback", []))
    activity_rows = pbas.get("departmental_activities", [])

    if not isinstance(feedback_rows, list):
        feedback_rows = []
    if not isinstance(activity_rows, list):
        activity_rows = []

    return {
        **base,

        # ================= PBAS TABLE A =================
        "pbas_teaching": {
            "rows": teaching_rows,
            "total_scheduled": sum(r.get("scheduled", 0) for r in teaching_rows),
            "total_held": sum(r.get("held", 0) for r in teaching_rows),
            "total_points": round(
                sum(r.get("points", 0) for r in teaching_rows), 2
            ),
        },

        # ================= PBAS TABLE B =================
        "pbas_feedback": {
            "rows": feedback_rows,
            "total": round(
                sum(r.get("average", r.get("feedback_score", 0)) for r in feedback_rows), 2
            ),
        },

        # ================= PBAS TABLE C =================
        "pbas_activities": {
            "rows": activity_rows
        },

        # ================= FINAL SCORE =================
        "scores": {
            "overall_grade": raw.get("scores", {}).get("overall_grade", ""),
        },
    }
