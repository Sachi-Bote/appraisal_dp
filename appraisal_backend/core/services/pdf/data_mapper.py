from typing import Dict
from core.models import Appraisal


def get_common_pdf_data(appraisal: Appraisal) -> Dict:
    faculty = appraisal.faculty
    appraisal_data = appraisal.appraisal_data or {}

    return {
        "faculty": {
            "name": faculty.full_name,
            "designation": faculty.designation,
            "department": (
                faculty.department.department_name
                if faculty.department else ""
            ),
            "email": faculty.email,
            "mobile": faculty.mobile,
        },

        "period": appraisal.academic_year,

        "remarks": {
            "justification": appraisal.remarks or "",
            "hod_comments": "",
            "principal": "",
        },

        "signatures": {
            "teacher_date": "",
            "hod_date": "",
            "principal_date": "",
        },

        "raw": appraisal_data,
    }
