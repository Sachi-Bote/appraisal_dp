# testsuite/test_all_systems.py

from validation.master_validator import validate_full_form
from scoring.engine import calculate_full_score
from workflow.engine import perform_action


def test_entire_pipeline():

    # 1. Dummy input simulating a FULL appraisal
    payload = {
        "faculty_id": 1,
        "year": 2024,

        "teaching": {
            "total_classes_assigned": 100,
            "classes_taught": 90
        },

        "activities": {
            "activity_a": True,
            "activity_b": False,
            "activity_c": True
        },

        "research": {
            "journal_papers": 2,
            "conference_papers": 1
        },

        "pbas": {
            "teaching_process": 20,
            "feedback": 22,
            "department": 15,
            "institute": 8,
            "acr": 8,
            "society": 6
        },

        "submit_action": "submit",
        "role": "faculty"
    }

    # 2. VALIDATION CHECK
    ok, err = validate_full_form(payload)
    assert ok, f"Validation failed: {err}"

    # 3. SCORING CHECK
    score_result = calculate_full_score(payload)
    assert score_result["total_score"] > 0

    # 4. WORKFLOW CHECK
    new_state = perform_action("faculty", "submit", "draft")
    assert new_state == "submitted"
