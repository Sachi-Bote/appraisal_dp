from typing import Dict
from core.models import Appraisal
from workflow.states import States


def _get_hod_comments(appraisal: Appraisal) -> str:
    appraisal_data = appraisal.appraisal_data or {}
    hod_review = appraisal_data.get("hod_review", {})
    if isinstance(hod_review, dict):
        parts = [
            (hod_review.get("comments_table1") or "").strip(),
            (hod_review.get("comments_table2") or "").strip(),
            (hod_review.get("remarks_suggestions") or "").strip(),
        ]
        merged = []
        for p in parts:
            if p and p not in merged:
                merged.append(p)
        if merged:
            return "\n".join(merged)

    approval = (
        appraisal.approval_history
        .filter(role="HOD")
        .order_by("-action_at", "-approval_id")
        .first()
    )
    return (approval.remarks or "").strip() if approval else ""


def _get_principal_remarks(appraisal: Appraisal) -> str:
    if appraisal.status not in {States.PRINCIPAL_APPROVED, States.FINALIZED}:
        return ""

    appraisal_data = appraisal.appraisal_data or {}
    principal_review = appraisal_data.get("principal_review", {})
    if isinstance(principal_review, dict):
        remarks = (principal_review.get("remarks") or "").strip()
        if remarks:
            return remarks

    if appraisal.remarks:
        return appraisal.remarks

    # Backward-compatible fallback for older approved records where remarks
    # may exist only in approval history.
    approval = (
        appraisal.approval_history
        .filter(role="PRINCIPAL", action="APPROVED")
        .order_by("-action_at", "-approval_id")
        .first()
    )
    return (approval.remarks if approval and approval.remarks else "")


def get_common_pdf_data(appraisal: Appraisal) -> Dict:
    faculty = appraisal.faculty
    appraisal_data = appraisal.appraisal_data or {}
    hod_comments = _get_hod_comments(appraisal)
    principal_remarks = _get_principal_remarks(appraisal)

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
            "hod_comments": hod_comments,
            "principal": principal_remarks,
        },

        "signatures": {
            "teacher_date": "",
            "hod_date": "",
            "principal_date": "",
        },

        "raw": appraisal_data,
    }
