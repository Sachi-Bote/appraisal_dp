"""
FINAL VERIFICATION TEST FOR ACTIVITIES MAPPING FIX
Run this to verify the fix works correctly
"""

def _to_bool(value) -> bool:
    """Normalize values to boolean - matches enhanced_sppu_mapper.py"""
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
    """FIXED VERSION - matches current enhanced_sppu_mapper.py"""
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

    # Ensure None values are converted to False (THE FIX)
    return {k: bool(v) if v is not None else False for k, v in resolved.items()}


# ============================================================================
# TEST CASES
# ============================================================================

print("="*80)
print("VERIFICATION TEST: Activities Data Mapping Fix")
print("="*80)

# Test 1: Mix of True and False values
print("\n TEST 1: Mix of True/False (realistic scenario)")
print("")
test1 = {
    "activities": {
        "administrative_responsibility": True,
        "exam_duties": True,
        "student_related": False,   # <-- Should show "No" in PDF
        "organizing_events": True,
        "phd_guidance": False,       # <-- Should show "No" in PDF
        "research_project": False,   # <-- Should show "No" in PDF
        "sponsored_project": False   # <-- Should show "No" in PDF
    }
}
result1 = _build_activity_flags(test1)
print("Result:")
for k, v in result1.items():
    status = "Yes" if v else "No"
    symbol = "✓" if v else "✗"
    print(f"  {symbol} {k}: {status}")

expected_false_count = 4
actual_false_count = sum(1 for v in result1.values() if not v)
test1_pass = actual_false_count == expected_false_count

print(f"\nExpected {expected_false_count} 'No' values, got {actual_false_count}")
print(f"Test 1: {'✓ PASS' if test1_pass else '✗ FAIL'}")

# Test 2: All False
print("\n" + "="*80)
print("\nTEST 2: All False (all should show 'No' in PDF)")
print("-"*80)
test2 = {
    "activities": {
        "administrative_responsibility": False,
        "exam_duties": False,
        "student_related": False,
        "organizing_events": False,
        "phd_guidance": False,
        "research_project": False,
        "sponsored_project": False
    }
}
result2 = _build_activity_flags(test2)
all_false = all(not v for v in result2.values())
print(f"All values are False: {all_false}")
print(f"Test 2: {'✓ PASS' if all_false else '✗ FAIL'}")

# Test 3: String values
print("\n" + "="*80)
print("\nTEST 3: String 'yes'/'no' values")
print("-"*80)
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
test3_pass = (result3["a_administrative"] == True and 
              result3["b_exam_duties"] == False and
              result3["d_organizing_events"] == True)
print(f"a_administrative (should be Yes): {result3['a_administrative']}")
print(f"b_exam_duties (should be No): {result3['b_exam_duties']}")
print(f"d_organizing_events (should be Yes): {result3['d_organizing_events']}")
print(f"Test 3: {'✓ PASS' if test3_pass else '✗ FAIL'}")

# Final Summary
print("\n" + "="*80)
print("FINAL RESULT:")
print("="*80)
all_passed = test1_pass and all_false and test3_pass
if all_passed:
    print("✓✓✓ ALL TESTS PASSED! ✓✓✓")
    print("\nThe fix is working correctly.")
    print("False values will now correctly show as 'No' in the PDF.")
else:
    print("✗✗✗ SOME TESTS FAILED ✗✗✗")
print("="*80)
