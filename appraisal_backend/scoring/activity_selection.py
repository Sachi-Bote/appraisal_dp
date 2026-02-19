from __future__ import annotations

from typing import Any, Dict, List, Tuple


ACTIVITY_SECTIONS: List[Dict[str, Any]] = [
    {
        "section_key": "a_administrative",
        "label": "Administrative responsibilities (HOD / Dean / Coordinator etc.)",
        "legacy_flag": "administrative_responsibility",
        "activities": [
            "Departmental Library in charge",
            "Cleanliness in charge",
            "Departmental store/Purchase in-charge",
            "Student Feedback in charge",
            "In-charge/Member of AICTE/State Govt./University statutory committee",
            "NBA/NACC coordinator",
            "Rector/Warden/Canteen",
            "Scholarship in-charge",
            "Any other administrative activity",
        ],
    },
    {
        "section_key": "b_exam_duties",
        "label": "Examination & evaluation duties",
        "legacy_flag": "exam_duties",
        "activities": [
            "Practical/Exam timetable in charge",
            "Internal/External academic monitoring coordinator",
            "Exam activities/duties",
            "Any other examination/evaluation duty",
        ],
    },
    {
        "section_key": "c_student_related",
        "label": "Student related co-curricular / extension activities",
        "legacy_flag": "student_related",
        "activities": [
            "Student Association (Chapter co-coordinator)",
            "Project mentoring for project competition",
            "Student counseling",
            "Sports in charge and co-coordinator",
            "PRO/Gymkhana/Gathering/Publicity/student club activity",
            "Blood donation activity organization",
            "Yoga classes",
            "Medical camp/health camp organization",
            "Literacy camp organization",
            "Environmental awareness camp",
            "Swachh Bharat mission / NCC / NSS activity",
            "Any other student-related activity",
        ],
    },
    {
        "section_key": "d_organizing_events",
        "label": "Organizing seminars / workshops / conferences",
        "legacy_flag": "organizing_events",
        "activities": [
            "Initiative for CEP/STTP/testing consultancy",
            "Organization of MOOCS/NPTEL/spoken tutorials/webinars",
            "Organization of FDP/Conference/Training/Workshop",
            "Induction program in charge",
            "Any other event organization activity",
        ],
    },
    {
        "section_key": "e_phd_guidance",
        "label": "Guiding PhD students",
        "legacy_flag": "phd_guidance",
        "activities": [
            "Evidence of activity involved in guiding PhD students",
            "Any other PhD guidance activity",
        ],
    },
    {
        "section_key": "f_research_project",
        "label": "Conducting minor / major research projects",
        "legacy_flag": "research_project",
        "activities": [
            "Conducting minor research project",
            "Conducting major research project",
            "Any other research project activity",
        ],
    },
    {
        "section_key": "g_sponsored_project",
        "label": "Publication in UGC / Peer-reviewed journals",
        "legacy_flag": "sponsored_project",
        "activities": [
            "Single or joint publication in peer-reviewed journal",
            "Publication in UGC listed journal",
            "Any other publication activity",
        ],
    },
]


SECTION_ALIAS_MAP: Dict[str, str] = {
    "a": "a_administrative",
    "administrative": "a_administrative",
    "administrative_responsibility": "a_administrative",
    "administrativeresponsibility": "a_administrative",
    "a_administrative": "a_administrative",
    "b": "b_exam_duties",
    "exam": "b_exam_duties",
    "exam_duties": "b_exam_duties",
    "examination_duties": "b_exam_duties",
    "b_exam_duties": "b_exam_duties",
    "c": "c_student_related",
    "student_related": "c_student_related",
    "student_related_activities": "c_student_related",
    "c_student_related": "c_student_related",
    "d": "d_organizing_events",
    "organizing_events": "d_organizing_events",
    "organizing_seminars": "d_organizing_events",
    "d_organizing_events": "d_organizing_events",
    "e": "e_phd_guidance",
    "phd_guidance": "e_phd_guidance",
    "guiding_phd_students": "e_phd_guidance",
    "e_phd_guidance": "e_phd_guidance",
    "f": "f_research_project",
    "research_project": "f_research_project",
    "conducting_research_projects": "f_research_project",
    "f_research_project": "f_research_project",
    "g": "g_sponsored_project",
    "publication_in_ugc": "g_sponsored_project",
    "publication": "g_sponsored_project",
    "sponsored_project": "g_sponsored_project",
    "g_sponsored_project": "g_sponsored_project",
}


LEGACY_FLAG_TO_SECTION = {
    section["legacy_flag"]: section["section_key"] for section in ACTIVITY_SECTIONS
}

SECTION_TO_LEGACY_FLAG = {
    section["section_key"]: section["legacy_flag"] for section in ACTIVITY_SECTIONS
}


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1", "on"}:
            return True
        if normalized in {"false", "no", "n", "0", "off", ""}:
            return False
    return bool(value)


def normalize_section_key(raw_key: Any) -> str | None:
    if raw_key is None:
        return None
    text = str(raw_key).strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    return SECTION_ALIAS_MAP.get(text)


def _extract_selection_list(payload: Dict[str, Any]) -> List[Any]:
    candidates = (
        "selected_activities",
        "selectedActivities",
        "activity_selections",
        "activitySelections",
        "selected_entries",
        "entries",
        "selections",
    )
    for key in candidates:
        val = payload.get(key)
        if isinstance(val, list):
            return val
    return []


def derive_activity_flags(payload: Dict[str, Any]) -> Dict[str, bool]:
    if not isinstance(payload, dict):
        payload = {}

    section_flags = {section["section_key"]: False for section in ACTIVITY_SECTIONS}

    for item in _extract_selection_list(payload):
        section_key = None
        if isinstance(item, dict):
            section_key = normalize_section_key(
                item.get("section_key")
                or item.get("section")
                or item.get("category_key")
                or item.get("category")
                or item.get("bucket")
            )
        elif isinstance(item, str):
            section_key = normalize_section_key(item)

        if section_key:
            section_flags[section_key] = True

    for legacy_flag, section_key in LEGACY_FLAG_TO_SECTION.items():
        if _to_bool(payload.get(legacy_flag)):
            section_flags[section_key] = True

    for raw_key, value in payload.items():
        section_key = normalize_section_key(raw_key)
        if section_key and _to_bool(value):
            section_flags[section_key] = True

    return section_flags


def normalize_activity_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(payload or {})
    section_flags = derive_activity_flags(payload)

    # Keep backward compatibility for existing consumers.
    for section_key, yes in section_flags.items():
        payload[section_key] = yes
        payload[SECTION_TO_LEGACY_FLAG[section_key]] = yes

    payload["yes_count"] = sum(1 for yes in section_flags.values() if yes)
    payload["section_flags"] = dict(section_flags)
    return payload


def get_activity_sections() -> List[Dict[str, Any]]:
    return [
        {
            "section_key": section["section_key"],
            "label": section["label"],
            "legacy_flag": section["legacy_flag"],
            "activities": list(section["activities"]),
        }
        for section in ACTIVITY_SECTIONS
    ]


def validate_activity_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Activities payload must be a JSON object"

    selected = _extract_selection_list(payload)
    for idx, item in enumerate(selected, start=1):
        if isinstance(item, str):
            if not normalize_section_key(item):
                return False, f"Invalid section key in selected activity #{idx}"
            continue
        if not isinstance(item, dict):
            return False, f"Selected activity #{idx} must be an object"
        section_key = normalize_section_key(
            item.get("section_key")
            or item.get("section")
            or item.get("category_key")
            or item.get("category")
            or item.get("bucket")
        )
        if not section_key:
            return False, f"Missing/invalid section for selected activity #{idx}"

    return True, ""
