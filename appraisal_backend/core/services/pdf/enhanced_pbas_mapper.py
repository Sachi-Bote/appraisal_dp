from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal
import re


def _get_first(data, keys, default=None):
    if not isinstance(data, dict):
        return default
    for key in keys:
        if key in data and data.get(key) is not None:
            return data.get(key)
    return default


def _get_list(data, keys):
    value = _get_first(data, keys, [])
    return value if isinstance(value, list) else []


def _to_float(value, default=0.0):
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _to_int(value, default=0):
    try:
        if value in ("", None):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _has_meaningful_research_data(entry: Dict) -> bool:
    if not isinstance(entry, dict):
        return False
    title = str(entry.get("title", "")).strip()
    name = str(entry.get("name", "")).strip()
    activity = str(entry.get("activity", "")).strip()
    year = str(entry.get("year", "")).strip()
    enclosure_no = str(entry.get("enclosure_no", "")).strip()
    enclosure = str(entry.get("enclosure", "")).strip()
    if not any([title, name, activity, year, enclosure_no, enclosure]):
        return False
    if title.lower() == "award" and not any([year, enclosure_no, enclosure]):
        return False
    return True


def _humanize_key(value: str) -> str:
    if not value:
        return ""
    return str(value).replace("_", " ").strip().title()


def _clean_promotion_due_text(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    unique_dates = []
    for d in dates:
        if d not in unique_dates:
            unique_dates.append(d)
    non_date_text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)
    non_date_text = re.sub(r"\s+", " ", non_date_text).strip()
    combined = " ".join(part for part in [non_date_text, " ".join(unique_dates[:2])] if part).strip()
    return combined or text


def get_enhanced_pbas_pdf_data(appraisal: Appraisal) -> Dict:
    """
    Extract all data for enhanced AICTE PBAS PDF generation with complete fields.
    """
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})

    try:
        calculated_scores = calculate_full_score(raw)
    except Exception:
        calculated_scores = {
            "teaching": {},
            "activities": {},
            "student_feedback": {},
            "departmental_activities": {},
            "institute_activities": {},
            "society_activities": {},
            "research": {},
            "pbas": {},
            "acr": {},
            "total_score": Decimal("0.00"),
        }

    pbas = raw.get("pbas", {}) if isinstance(raw.get("pbas"), dict) else {}
    general = raw.get("general", {}) if isinstance(raw.get("general"), dict) else {}

    teaching_root = raw.get("teaching", {}) if isinstance(raw.get("teaching"), dict) else {}
    teaching_courses = _get_list(teaching_root, ["courses", "course_list", "teaching_process"])
    if not teaching_courses:
        teaching_courses = _get_list(pbas, ["teaching_process", "teachingProcess"])

    normalized_teaching = []
    for idx, course in enumerate(teaching_courses):
        if not isinstance(course, dict):
            continue
        scheduled = _to_int(_get_first(course, ["scheduled_classes", "scheduled", "total_classes_assigned"]), 0)
        held = _to_int(_get_first(course, ["held_classes", "held", "classes_taught", "total_classes_taught"]), 0)
        row_points = _to_float(_get_first(course, ["points", "points_earned"]), 0)

        normalized_teaching.append({
            "semester": _get_first(course, ["semester", "term"], ""),
            "course_code": _get_first(course, ["course_code", "courseCode", "code"], ""),
            "course_name": _get_first(course, ["course_name", "courseName", "course"], ""),
            "scheduled_classes": scheduled,
            "held_classes": held,
            "points_earned": row_points,
            "enclosure_no": _get_first(course, ["enclosure_no", "enclosure", "enclosureNo"], ""),
            "sr_no": idx + 1,
        })

    total_scheduled = calculated_scores.get("teaching", {}).get("total_scheduled", 0)
    total_held = calculated_scores.get("teaching", {}).get("total_held", 0)
    attendance_percentage = calculated_scores.get("teaching", {}).get("attendance_percentage", 0)
    if not total_scheduled:
        total_scheduled = sum(_to_int(c.get("scheduled_classes")) for c in normalized_teaching)
    if not total_held:
        total_held = sum(_to_int(c.get("held_classes")) for c in normalized_teaching)
    if not attendance_percentage:
        attendance_percentage = round((total_held / total_scheduled) * 100, 2) if total_scheduled else 0

    student_feedback = _get_list(pbas, ["student_feedback", "students_feedback", "feedback_entries", "feedback"])
    departmental_activities = _get_list(pbas, ["departmental_activities", "departmentalActivities", "department"])
    institute_activities = _get_list(pbas, ["institute_activities", "instituteActivities", "institute"])
    society_activities = _get_list(pbas, ["society_activities", "societyActivities", "society"])

    normalized_feedback = []
    for idx, feedback in enumerate(student_feedback):
        if not isinstance(feedback, dict):
            continue
        normalized_feedback.append({
            "semester": _get_first(feedback, ["semester", "term"], ""),
            "course_code": _get_first(feedback, ["course_code", "courseCode", "code"], ""),
            "course_name": _get_first(feedback, ["course_name", "courseName", "course"], ""),
            "feedback_score": _to_float(_get_first(feedback, ["feedback_score", "average", "score"]), 0),
            "enclosure_no": _get_first(feedback, ["enclosure_no", "enclosure", "enclosureNo"], ""),
            "sr_no": idx + 1,
        })

    def _normalize_activity_entries(entries):
        normalized = []
        for idx, activity in enumerate(entries):
            if not isinstance(activity, dict):
                continue
            normalized.append({
                "semester": _get_first(activity, ["semester", "term"], ""),
                "activity": _get_first(activity, ["activity", "name", "title"], ""),
                "credits_claimed": _to_float(_get_first(activity, ["credits_claimed", "credit_point", "creditPoint", "credit"]), 0),
                "criteria": _get_first(activity, ["criteria", "remarks"], ""),
                "enclosure_no": _get_first(activity, ["enclosure_no", "enclosure", "enclosureNo"], ""),
                "sr_no": idx + 1,
            })
        return normalized

    normalized_departmental = _normalize_activity_entries(departmental_activities)
    normalized_institute = _normalize_activity_entries(institute_activities)
    normalized_society = _normalize_activity_entries(society_activities)

    research_entries = raw.get("research", {}).get("entries", [])
    normalized_research_entries = []
    for entry in research_entries:
        if not isinstance(entry, dict):
            continue
        entry_type = _get_first(entry, ["type", "category"], "")
        if not str(entry_type).strip() or not _has_meaningful_research_data(entry):
            continue
        title_value = _get_first(entry, ["title", "name", "activity"], "-")
        normalized_research_entries.append({
            **entry,
            "type_display": _humanize_key(entry_type),
            "title_display": title_value,
            "name": _get_first(entry, ["name"], title_value),
            "year": _get_first(entry, ["year"], "-"),
            "enclosure_no": _get_first(entry, ["enclosure_no", "enclosure"], "-"),
        })

    journal_count = sum(1 for e in normalized_research_entries if "journal" in str(e.get("type", "")).lower())
    conference_count = sum(1 for e in normalized_research_entries if "conference" in str(e.get("type", "")).lower())

    acr = raw.get("acr", {})
    acr_score = _to_float(_get_first(pbas, ["acr", "acr_score"]), calculated_scores.get("acr", {}).get("credit_point", 0))

    if attendance_percentage >= 80:
        overall_grade = "Good"
    elif attendance_percentage >= 70:
        overall_grade = "Satisfactory"
    else:
        overall_grade = "Not Satisfactory"

    teaching_section_score = _to_float(
        _get_first(pbas, ["teaching_process_score"]),
        calculated_scores.get("teaching", {}).get("score", 0),
    )
    if not teaching_section_score:
        teaching_section_score = _to_float(
            _get_first(pbas, ["teaching_process", "teachingProcess"]),
            calculated_scores.get("teaching", {}).get("score", 0),
        )

    # ✅ FETCH VERIFIED GRADE
    verified_grade = ""
    try:
        if hasattr(appraisal, 'appraisalscore'):
            verified_grade = appraisal.appraisalscore.verified_grade
    except Exception:
        pass

    return {
        "verified_grade": verified_grade,
        **base,
        "faculty_ext": {
            "name": _get_first(general, ["faculty_name", "name"], base["faculty"]["name"]),
            "designation": _get_first(general, ["designation"], base["faculty"]["designation"]),
            "date_of_joining": _get_first(general, ["date_of_joining", "joining_date", "date_joining"], ""),
            "department_center": _get_first(general, ["department", "department_centre", "department_center"], base["faculty"]["department"]),
            "communication_address": _get_first(general, ["communication_address", "address"], ""),
            "email_mobile": f'{_get_first(general, ["email"], base["faculty"]["email"])} / {_get_first(general, ["mobile", "phone"], base["faculty"]["mobile"])}',
            "present_designation_grade_pay": _get_first(general, ["present_designation_grade_pay", "grade_pay", "gradePay"], ""),
            "promotion_designation_due_date": _clean_promotion_due_text(
                _get_first(general, ["promotion_designation_due_date", "promotion_designation", "promotion_due_date"], "")
            ),
            "assessment_period": _get_first(general, ["assessment_period"], base.get("period", "")),
        },
        "teaching": {
            "courses": normalized_teaching,
            "total_scheduled": total_scheduled,
            "total_held": total_held,
            "attendance_percentage": attendance_percentage,
            "total_points": round(sum(_to_float(c.get("points_earned")) for c in normalized_teaching), 2),
        },
        "student_feedback": {
            "entries": normalized_feedback,
            "total_score": round(sum(_to_float(f.get("feedback_score")) for f in normalized_feedback), 2),
        },
        "departmental_activities": {
            "entries": normalized_departmental,
            "total_credits": round(sum(_to_float(a.get("credits_claimed")) for a in normalized_departmental), 2),
        },
        "institute_activities": {
            "entries": normalized_institute,
            "total_credits": round(sum(_to_float(a.get("credits_claimed")) for a in normalized_institute), 2),
        },
        "society_activities": {
            "entries": normalized_society,
            "total_credits": round(sum(_to_float(a.get("credits_claimed")) for a in normalized_society), 2),
        },
        "research": {
            "entries": normalized_research_entries,
            "journal_count": journal_count,
            "conference_count": conference_count,
            "total": journal_count + conference_count,
            "verified": "",
        },
        "acr": {
            "grade": calculated_scores.get("acr", {}).get("grade") or _get_first(acr, ["grade"], ""),
            "score": calculated_scores.get("acr", {}).get("credit_point") or acr_score,
            "enclosure_no": _get_first(acr, ["enclosure_no", "enclosure", "enclosureNo"], ""),
        },
        "pbas_section_scores": {
            "teaching_process": teaching_section_score,
            "feedback": _to_float(_get_first(pbas, ["feedback", "student_feedback_score"]), 0),
            "department": _to_float(_get_first(pbas, ["department", "departmental"]), 0),
            "institute": _to_float(_get_first(pbas, ["institute"]), 0),
            "society": _to_float(_get_first(pbas, ["society"]), 0),
            "acr": acr_score,
        },
        "scores": {
            "overall_grade": overall_grade,
            "teaching_score": float(calculated_scores.get("teaching", {}).get("score", 0)),
            "activities_score": float(calculated_scores.get("activities", {}).get("score", 0)),
            "student_feedback_score": float(calculated_scores.get("student_feedback", {}).get("score", 0)),
            "departmental_score": float(calculated_scores.get("departmental_activities", {}).get("total_awarded", 0)),
            "institute_score": float(calculated_scores.get("institute_activities", {}).get("total_awarded", 0)),
            "society_score": float(calculated_scores.get("society_activities", {}).get("total_awarded", 0)),
            "research_score": float(calculated_scores.get("research", {}).get("total", 0)),
            "pbas_score": float(calculated_scores.get("pbas", {}).get("total", 0)),
            "acr_score": float(calculated_scores.get("acr", {}).get("credit_point", 0)),
            "total_score": float(calculated_scores.get("total_score", 0)),
        },
        "academic_year": raw.get("academic_year", ""),
        "semester": raw.get("semester", ""),
        "form_type": "AICTE PBAS",
    }
