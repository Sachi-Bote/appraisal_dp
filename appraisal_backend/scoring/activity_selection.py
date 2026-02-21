from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Tuple


PBAS_SCOPE_DEPARTMENTAL = "departmental"
PBAS_SCOPE_INSTITUTE = "institute"
PBAS_SCOPE_SOCIETY = "society"


ACTIVITY_SECTIONS: List[Dict[str, Any]] = [
    {
        "section_key": "a_administrative",
        "label": "Administrative responsibilities (HOD / Dean / Coordinator etc.)",
        "legacy_flag": "administrative_responsibility",
        "activities": [
            {"label": "Lab In charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Departmental Library in charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Cleanliness in charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Departmental store/Purchase in-charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Student Feedback in charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "In-charge/Member of AICTE/State Govt./University statutory committee", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "NBA/NACC coordinator", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Rector/Warden/Canteen", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Scholarship in-charge", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Any other administrative activity", "scope": PBAS_SCOPE_INSTITUTE},
        ],
    },
    {
        "section_key": "b_exam_duties",
        "label": "Examination & evaluation duties",
        "legacy_flag": "exam_duties",
        "activities": [
            {"label": "Practical/Exam timetable in charge", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Internal/External academic monitoring coordinator", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Exam activities/duties", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Any other examination/evaluation duty", "scope": PBAS_SCOPE_INSTITUTE},
        ],
    },
    {
        "section_key": "c_student_related",
        "label": "Student related co-curricular / extension activities",
        "legacy_flag": "student_related",
        "activities": [
            {"label": "Student Association (Chapter co-coordinator)", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Project mentoring for project competition", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Student counseling", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Sports in charge and co-coordinator", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "PRO/Gymkhana/Gathering/Publicity/student club activity", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Blood donation activity organization", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Yoga classes", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Medical camp/health camp organization", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Literacy camp organization", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Environmental awareness camp", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Swachh Bharat mission / NCC / NSS activity", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Any other student-related activity", "scope": PBAS_SCOPE_SOCIETY},
        ],
    },
    {
        "section_key": "d_organizing_events",
        "label": "Organizing seminars / workshops / conferences",
        "legacy_flag": "organizing_events",
        "activities": [
            {"label": "Initiative for CEP/STTP/testing consultancy", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Organization of MOOCS/NPTEL/spoken tutorials/webinars", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Organization of FDP/Conference/Training/Workshop", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Induction program in charge", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Any other event organization activity", "scope": PBAS_SCOPE_INSTITUTE},
        ],
    },
    {
        "section_key": "e_phd_guidance",
        "label": "Guiding PhD students",
        "legacy_flag": "phd_guidance",
        "activities": [
            {"label": "Evidence of activity involved in guiding PhD students", "scope": PBAS_SCOPE_DEPARTMENTAL},
            {"label": "Any other PhD guidance activity", "scope": PBAS_SCOPE_DEPARTMENTAL},
        ],
    },
    {
        "section_key": "f_research_project",
        "label": "Conducting minor / major research projects",
        "legacy_flag": "research_project",
        "activities": [
            {"label": "Conducting minor research project", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Conducting major research project", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Any other research project activity", "scope": PBAS_SCOPE_INSTITUTE},
        ],
    },
    {
        "section_key": "g_sponsored_project",
        "label": "Sponsored projects (national/international agencies)",
        "legacy_flag": "sponsored_project",
        "activities": [
            {"label": "Sponsored project funded by national agency", "scope": PBAS_SCOPE_INSTITUTE},
            {"label": "Sponsored project funded by international agency", "scope": PBAS_SCOPE_SOCIETY},
            {"label": "Any other sponsored project activity", "scope": PBAS_SCOPE_SOCIETY},
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
    "sponsored_projects": "g_sponsored_project",
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


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("&", "and")
    text = " ".join(text.split())
    return text


def _build_activity_lookup() -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for section in ACTIVITY_SECTIONS:
        section_key = section["section_key"]
        for activity in section["activities"]:
            label = str(activity.get("label", "")).strip()
            if not label:
                continue
            lookup[_normalize_text(label)] = {
                "section_key": section_key,
                "activity_name": label,
                "scope": activity.get("scope", PBAS_SCOPE_INSTITUTE),
            }
    return lookup


ACTIVITY_LOOKUP = _build_activity_lookup()

ACTIVITY_NAME_ALIASES = {
    _normalize_text("Lab In charge"): _normalize_text("Departmental Library in charge"),
    _normalize_text("Departmental Library In charge"): _normalize_text("Departmental Library in charge"),
    _normalize_text("Departmental store / Purchase in charge"): _normalize_text("Departmental store/Purchase in-charge"),
    _normalize_text("Practical / Exam Time table in charge"): _normalize_text("Practical/Exam timetable in charge"),
    _normalize_text("Internal / External Academic Monitoring Co-coordinator"): _normalize_text("Internal/External academic monitoring coordinator"),
    _normalize_text("Student Feedback In charge"): _normalize_text("Student Feedback in charge"),
    _normalize_text("Blood Donation Activity organization"): _normalize_text("Blood donation activity organization"),
    _normalize_text("Organization of FDP / Conference / Training / Workshop"): _normalize_text("Organization of FDP/Conference/Training/Workshop"),
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


def _extract_selected_activity_name(item: Dict[str, Any]) -> str:
    for key in ("activity", "activity_name", "label", "name", "title", "selected_activity"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_selected_entry(item: Any) -> Dict[str, Any] | None:
    section_key = None
    activity_name = ""
    scope = ""
    semester = ""
    enclosure_no = ""
    credits_claimed = 0.0

    if isinstance(item, dict):
        activity_name = _extract_selected_activity_name(item)
        section_key = normalize_section_key(
            item.get("section_key")
            or item.get("section")
            or item.get("category_key")
            or item.get("category")
            or item.get("bucket")
        )
        scope = str(item.get("scope") or item.get("pbas_scope") or "").strip().lower()
        semester = str(item.get("semester") or item.get("term") or "").strip()
        enclosure_no = str(item.get("enclosure_no") or item.get("enclosure") or "").strip()
        raw_credits = item.get("credits_claimed", item.get("credit_point", 0))
        try:
            credits_claimed = float(raw_credits or 0)
        except (TypeError, ValueError):
            credits_claimed = 0.0
    elif isinstance(item, str):
        normalized_text = _normalize_text(item)
        normalized_text = ACTIVITY_NAME_ALIASES.get(normalized_text, normalized_text)
        lookup = ACTIVITY_LOOKUP.get(normalized_text)
        if lookup:
            section_key = lookup["section_key"]
            activity_name = lookup["activity_name"]
            scope = lookup["scope"]
    else:
        return None

    if activity_name:
        normalized_activity_name = _normalize_text(activity_name)
        normalized_activity_name = ACTIVITY_NAME_ALIASES.get(normalized_activity_name, normalized_activity_name)
        lookup = ACTIVITY_LOOKUP.get(normalized_activity_name)
        if lookup:
            section_key = section_key or lookup["section_key"]
            scope = scope or lookup["scope"]

    scope_map = {
        "department": PBAS_SCOPE_DEPARTMENTAL,
        "departmental": PBAS_SCOPE_DEPARTMENTAL,
        "institute": PBAS_SCOPE_INSTITUTE,
        "institution": PBAS_SCOPE_INSTITUTE,
        "institutional": PBAS_SCOPE_INSTITUTE,
        "society": PBAS_SCOPE_SOCIETY,
    }
    scope = scope_map.get(scope, scope)

    if not section_key:
        return None
    if not activity_name:
        activity_name = section_key
    if scope not in {PBAS_SCOPE_DEPARTMENTAL, PBAS_SCOPE_INSTITUTE, PBAS_SCOPE_SOCIETY}:
        scope = PBAS_SCOPE_INSTITUTE

    return {
        "section_key": section_key,
        "activity_name": activity_name,
        "scope": scope,
        "semester": semester,
        "enclosure_no": enclosure_no,
        "credits_claimed": credits_claimed,
    }


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
            if not section_key:
                normalized_item = _normalize_text(item)
                normalized_item = ACTIVITY_NAME_ALIASES.get(normalized_item, normalized_item)
                lookup = ACTIVITY_LOOKUP.get(normalized_item)
                if lookup:
                    section_key = lookup["section_key"]

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


def _derive_pbas_activities_from_selection(activities_payload: Dict[str, Any]) -> Dict[str, Any]:
    departmental: List[Dict[str, Any]] = []
    institute: List[Dict[str, Any]] = []
    society: List[Dict[str, Any]] = []
    normalized_selection: List[Dict[str, Any]] = []

    for item in _extract_selection_list(activities_payload):
        normalized = _normalize_selected_entry(item)
        if not normalized:
            continue
        normalized_selection.append(normalized)
        mapped_entry = {
            "activity": normalized["activity_name"],
            "activity_name": normalized["activity_name"],
            "semester": normalized["semester"],
            "credits_claimed": normalized["credits_claimed"],
            "enclosure_no": normalized["enclosure_no"],
            "mapped_from_section": normalized["section_key"],
            "mapped_scope": normalized["scope"],
        }
        if normalized["scope"] == PBAS_SCOPE_DEPARTMENTAL:
            departmental.append(mapped_entry)
        elif normalized["scope"] == PBAS_SCOPE_INSTITUTE:
            institute.append(mapped_entry)
        else:
            society.append(mapped_entry)

    return {
        "departmental_activities": departmental,
        "institute_activities": institute,
        "society_activities": society,
        "normalized_selection": normalized_selection,
    }


def normalize_appraisal_activity_mapping(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized_payload = dict(payload or {})

    activities_payload = normalize_activity_payload(normalized_payload.get("activities", {}))
    normalized_payload["activities"] = activities_payload

    pbas_payload = normalized_payload.get("pbas", {})
    if not isinstance(pbas_payload, dict):
        pbas_payload = {}

    derived = _derive_pbas_activities_from_selection(activities_payload)
    has_selected_activities = bool(derived["normalized_selection"])

    if has_selected_activities:
        pbas_payload["departmental_activities"] = derived["departmental_activities"]
        pbas_payload["institute_activities"] = derived["institute_activities"]
        pbas_payload["society_activities"] = derived["society_activities"]
        activities_payload["selected_activities_normalized"] = derived["normalized_selection"]
        activities_payload["pbas_classification"] = {
            "departmental_count": len(derived["departmental_activities"]),
            "institute_count": len(derived["institute_activities"]),
            "society_count": len(derived["society_activities"]),
        }

    normalized_payload["pbas"] = pbas_payload
    return normalized_payload


@lru_cache(maxsize=1)
def get_activity_sections() -> List[Dict[str, Any]]:
    return [
        {
            "section_key": section["section_key"],
            "label": section["label"],
            "legacy_flag": section["legacy_flag"],
            "activities": [activity["label"] for activity in section["activities"]],
            "activities_with_scope": [
                {
                    "label": activity["label"],
                    "scope": activity["scope"],
                }
                for activity in section["activities"]
            ],
        }
        for section in ACTIVITY_SECTIONS
    ]


def validate_activity_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Activities payload must be a JSON object"

    selected = _extract_selection_list(payload)
    for idx, item in enumerate(selected, start=1):
        if isinstance(item, str):
            normalized_item = _normalize_text(item)
            normalized_item = ACTIVITY_NAME_ALIASES.get(normalized_item, normalized_item)
            if not normalize_section_key(item) and normalized_item not in ACTIVITY_LOOKUP:
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
