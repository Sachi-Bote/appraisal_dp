# core/services/pdf/data_mapper.py

from core.models import Appraisal  # optional, for type clarity
from core.models import FacultyProfile  # optional, for type clarity


def get_appraisal_pdf_data(appraisal):
    data = appraisal.appraisal_data or {}

    faculty = appraisal.faculty
    teaching_data = data.get("teaching", {})
    activities_data = data.get("activities", {})
    research_data = data.get("research", {})
    journal_count = research_data.get("journal_count", 0)
    conference_count = research_data.get("conference_count", 0)
    total_assigned = teaching_data.get("total_classes_assigned", 0)
    total_taught = teaching_data.get("classes_taught", 0)

    percentage = (
        round((total_taught / total_assigned) * 100, 2)
        if total_assigned else 0
    )

    # grading logic
    if percentage >= 80:
        teaching_grade = "Good"
    elif percentage >= 70:
        teaching_grade = "Satisfactory"
    else:
        teaching_grade = "Not Satisfactory"

    return {
        "faculty": {
            "name": faculty.full_name,
            "designation": faculty.designation,
            "department": faculty.department.department_name if faculty.department else "",
            "email": faculty.email,
            "mobile": faculty.mobile,
        },

        "period": appraisal.academic_year,

        "teaching": {
            "total_assigned": total_assigned,
            "total_taught": total_taught,
            "percentage": f"{percentage}%",
            "grade": teaching_grade,
            "verified_grade": appraisal.principal and "Good" or ""
        },

        "activities": {
            "list": activities_data.get("list", []),
            "grade": activities_data.get("grade", ""),
            "verified_grade": ""
        },

       "research": {
            "journal_count": journal_count,
            "conference_count": conference_count,
            "total": journal_count + conference_count,
            "verified": ""
        },

        "scores": {
            "overall_grade": teaching_grade
        },

        "remarks": {
            "justification": appraisal.remarks or "",
            "hod_comments": "",
            "principal": ""
        },

        "signatures": {
            "hod_date": "",
            "teacher_date": "",
            "principal_date": ""
        }
    }
