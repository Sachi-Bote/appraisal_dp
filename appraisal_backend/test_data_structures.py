"""
Test with different data structures to find the issue
"""

def _to_bool(value) -> bool:
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


def _build_activity_flags(raw):
    """Current implementation"""
    sources = []
    activities = raw.get("activities", {})
    if isinstance(activities, dict):
        sources.append(activities)

    pbas = raw.get("pbas", {})
    if isinstance(pbas, dict):
        pbas_activities = pbas.get("activities", {})
        if isinstance(pbas_activities, dict):
            sources.append(pbas_activities)
        step2b = pbas.get("step2b", {})
        if isinstance(step2b, dict):
            sources.append(step2b)

    for key in ("step2b", "section_b", "sectionB", "sppu"):
        section = raw.get(key, {})
        if isinstance(section, dict):
            section_activities = section.get("activities", {})
            if isinstance(section_activities, dict):
                sources.append(section_activities)
            sources.append(section)

    key_aliases = {
        "a_administrative": ["administrative_responsibility", "administrativeResponsibilities", "administrative", "a", "activity_a"],
        "b_exam_duties": ["exam_duties", "examDuties", "examination_duties", "examinationDuties", "b", "activity_b"],
        "c_student_related": ["student_related", "studentRelated", "student_related_activities", "studentRelatedActivities", "c", "activity_c"],
        "d_organizing_events": ["organizing_events", "organizingEvents", "organizing_seminars", "organizingSeminars", "d", "activity_d"],
        "e_phd_guidance": ["phd_guidance", "phdGuidance", "guiding_phd_students", "guidingPhdStudents", "e", "activity_e"],
        "f_research_project": ["research_project", "researchProject", "conducting_research_projects", "conductingResearchProjects", "f", "activity_f"],
        "g_sponsored_project": ["sponsored_project", "sponsoredProject", "publication_in_ugc", "publicationInUgc", "g", "activity_g"],
    }

    resolved = {k: None for k in key_aliases}

    for src in sources:
        if not isinstance(src, dict):
            continue
        for target, aliases in key_aliases.items():
            if resolved[target] is not None:
                continue
            for alias in aliases:
                if alias in src:
                    resolved[target] = _to_bool(src.get(alias))
                    break

    return {k: bool(v) for k, v in resolved.items()}


# Test scenarios
print("="*70)
print("TEST 1: Standard structure (working)")
print("="*70)
test1 = {
    "activities": {
        "administrative_responsibility": True,
        "exam_duties": False,
        "student_related": False,
        "organizing_events": True,
        "phd_guidance": False,
        "research_project": False,
        "sponsored_project": False
    }
}
result1 = _build_activity_flags(test1)
print(f"Input: {test1}")
print(f"Result: {result1}")

print("\n" + "="*70)
print("TEST 2: Nested in appraisal_data (possible issue)")
print("="*70)
test2 = {
    "appraisal_data": {
        "activities": {
            "administrative_responsibility": True,
            "exam_duties": False,
            "student_related": False,
            "organizing_events": True,
            "phd_guidance": False,
            "research_project": False,
            "sponsored_project": False
        }
    }
}
result2 = _build_activity_flags(test2)
print(f"Input: {test2}")
print(f"Result: {result2}")

print("\n" + "="*70)
print("TEST 3: Strings instead of booleans")
print("="*70)
test3 = {
    "activities": {
        "administrative_responsibility": "yes",
        "exam_duties": "no",
        "student_related": "no",
        "organizing_events": "yes",
        "phd_guidance": "no",
        "research_project": "no",
        "sponsored_project": "no"
    }
}
result3 = _build_activity_flags(test3)
print(f"Input: {test3}")
print(f"Result: {result3}")

print("\n" + "="*70)
print("TEST 4: Activities with all True (to see if template has hardcoded Yes)")
print("="*70)
test4 = {
    "activities": {
        "administrative_responsibility": True,
        "exam_duties": True,
        "student_related": True,
        "organizing_events": True,
        "phd_guidance": True,
        "research_project": True,
        "sponsored_project": True
    }
}
result4 = _build_activity_flags(test4)
print(f"Result (all should be True): {result4}")
