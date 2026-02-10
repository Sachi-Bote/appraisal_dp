"""
Debug script to test activities data mapping
"""

import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.services.pdf.enhanced_sppu_mapper import _build_activity_flags, _to_bool

# Test data from Sample_Payload.json
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

print("=" * 70)
print("DEBUG: Testing Activities Data Mapping")
print("=" * 70)

print("\n1. Input Data:")
print(json.dumps(test_payload, indent=2))

print("\n2. Testing _to_bool function:")
print(f"  _to_bool(True) = {_to_bool(True)}")
print(f"  _to_bool(False) = {_to_bool(False)}")
print(f"  _to_bool('yes') = {_to_bool('yes')}")
print(f"  _to_bool('no') = {_to_bool('no')}")

print("\n3. Testing _build_activity_flags:")
result = _build_activity_flags(test_payload)

print("\nResult:")
print(json.dumps(result, indent=2))

print("\n4. Expected vs Actual:")
expected = {
    "a_administrative": True,  # administrative_responsibility
    "b_exam_duties": True,      # exam_duties
    "c_student_related": False, # student_related
    "d_organizing_events": True,# organizing_events
    "e_phd_guidance": False,    # phd_guidance
    "f_research_project": False,# research_project
    "g_sponsored_project": False# sponsored_project
}

all_correct = True
for key in expected:
    expected_val = expected[key]
    actual_val = result.get(key, None)
    match = "✓" if expected_val == actual_val else "✗"
    status = "PASS" if expected_val == actual_val else "FAIL"
    print(f"  {match} {key}: Expected={expected_val}, Actual={actual_val} [{status}]")
    if expected_val != actual_val:
        all_correct = False

print("\n" + "=" * 70)
if all_correct:
    print("✓ ALL TESTS PASSED")
else:
    print("✗ SOME TESTS FAILED")
print("=" * 70)
