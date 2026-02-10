"""
Simplified debug script - just test the function logic without Django
"""

# Simulate the _to_bool function
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


def _get_first_key(data, keys, default=False):
    for key in keys:
        if key in data:
            return data.get(key)
    return default


def _build_activity_flags(raw):
    """Current implementation from enhanced_sppu_mapper.py"""
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

    print("\nDEBUG: Processing sources...")
    for idx, src in enumerate(sources):
        print(f"\n  Source {idx}: {src}")
        if not isinstance(src, dict):
            continue
        for target, aliases in key_aliases.items():
            if resolved[target] is not None:
                print(f"    {target}: Already resolved to {resolved[target]}, skipping")
                continue
            for alias in aliases:
                if alias in src:
                    resolved[target] = _to_bool(src.get(alias))
                    print(f"    {target}: Found '{alias}' = {src.get(alias)} -> {resolved[target]}")
                    break

    # Optional legacy mapping
    if all(v is None for v in resolved.values()):
        use_legacy_derivation = False
        if use_legacy_derivation and isinstance(activities, dict):
            departmental = _to_bool(_get_first_key(activities, ["departmental", "departmental_activities", "departmentalActivities"], False))
            institute = _to_bool(_get_first_key(activities, ["institute", "institute_activities", "instituteActivities"], False))
            society = _to_bool(_get_first_key(activities, ["society", "society_activities", "societyActivities"], False))
            resolved = {
                "a_administrative": departmental,
                "b_exam_duties": departmental,
                "c_student_related": society,
                "d_organizing_events": institute,
                "e_phd_guidance": departmental,
                "f_research_project": departmental or institute,
                "g_sponsored_project": institute,
            }

    return {k: bool(v) for k, v in resolved.items()}


# Test with sample data
test_payload = {
    "activities": {
        "administrative_responsibility": True,
        "exam_duties": True,
        "student_related": False,
        "organizing_events": True,
        "phd_guidance": False,
        "research_project": False,
        "sponsored_project": False
    }
}

print("="*70)
print("TESTING ACTIVITIES DATA MAPPING")
print("="*70)
print("\nInput payload:")
print(test_payload)

result = _build_activity_flags(test_payload)

print("\n" + "="*70)
print("FINAL RESULT:")
print(result)

print("\n" + "="*70)
print("EXPECTED vs ACTUAL:")
expected = {
    "a_administrative": True,
    "b_exam_duties": True,
    "c_student_related": False,
    "d_organizing_events": True,
    "e_phd_guidance": False,
    "f_research_project": False,
    "g_sponsored_project": False
}

all_correct = True
for key in expected:
    exp = expected[key]
    act = result.get(key)
    match = "✓" if exp == act else "✗"
    print(f"  {match} {key}: Expected={exp}, Actual={act}")
    if exp != act:
        all_correct = False

print("\n" + "="*70)
if all_correct:
    print("✓ ALL TESTS PASSED!")
else:
    print("✗ TESTS FAILED - Issue found!")
print("="*70)
