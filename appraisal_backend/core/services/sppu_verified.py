ALLOWED_VERIFIED_GRADES = {"Good", "Satisfactory", "Not Satisfactory"}

TABLE2_VERIFIED_KEYS = [
    "peer_reviewed_journals",
    "books_international",
    "books_national",
    "chapter_edited_book",
    "editor_book_international",
    "editor_book_national",
    "translation_chapter_or_paper",
    "translation_book",
    "pedagogy_development",
    "curriculum_design",
    "moocs_4quadrant",
    "moocs_single_lecture",
    "moocs_content_writer",
    "moocs_coordinator",
    "econtent_4quadrant_complete",
    "econtent_4quadrant_per_module",
    "econtent_module_contribution",
    "econtent_editor",
    "phd_awarded",
    "phd_submitted",
    "mphil_pg_dissertation",
    "research_project_above_10l",
    "research_project_below_10l",
    "research_project_ongoing_above_10l",
    "research_project_ongoing_below_10l",
    "consultancy",
    "patent_international",
    "patent_national",
    "policy_international",
    "policy_national",
    "policy_state",
    "award_international",
    "award_national",
    "conference_international_abroad",
    "conference_international_country",
    "conference_national",
    "conference_state_university",
    "total",
]


def _sanitize_grade(value):
    if value in ALLOWED_VERIFIED_GRADES:
        return value
    return ""


def _sanitize_score_value(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text


def derive_overall_grade(teaching_grade, activity_grade):
    if teaching_grade == "Good" and activity_grade in {"Good", "Satisfactory"}:
        return "Good"
    if teaching_grade == "Satisfactory" and activity_grade in {"Good", "Satisfactory"}:
        return "Satisfactory"
    return "Not Satisfactory"


def _review_key(is_hod_submission):
    return "principal_review" if is_hod_submission else "hod_review"


def extract_verified_grading(appraisal_data, is_hod_submission):
    data = appraisal_data if isinstance(appraisal_data, dict) else {}
    review = data.get(_review_key(is_hod_submission), {})
    if not isinstance(review, dict):
        review = {}

    table2_scores = review.get("table2_verified_scores", {})
    if not isinstance(table2_scores, dict):
        table2_scores = {}
    clean_table2 = {
        key: _sanitize_score_value(table2_scores.get(key, ""))
        for key in TABLE2_VERIFIED_KEYS
    }

    return {
        "table1_verified_teaching": _sanitize_grade(review.get("table1_verified_teaching")),
        "table1_verified_activities": _sanitize_grade(review.get("table1_verified_activities")),
        "table2_verified_scores": clean_table2,
    }


def merge_verified_grading(appraisal_data, is_hod_submission, payload):
    data = appraisal_data if isinstance(appraisal_data, dict) else {}
    key = _review_key(is_hod_submission)
    review = data.get(key, {})
    if not isinstance(review, dict):
        review = {}

    existing = extract_verified_grading(data, is_hod_submission)
    table1_teaching = existing["table1_verified_teaching"]
    table1_activities = existing["table1_verified_activities"]

    payload_teaching = _sanitize_grade(payload.get("table1_verified_teaching"))
    payload_activities = _sanitize_grade(payload.get("table1_verified_activities"))
    payload_legacy = _sanitize_grade(payload.get("verified_grade"))

    if payload_teaching:
        table1_teaching = payload_teaching
    if payload_activities:
        table1_activities = payload_activities

    # Backward compatibility for older clients that send a single verified_grade.
    if payload_legacy and not payload_teaching and not payload_activities:
        table1_teaching = payload_legacy
        table1_activities = payload_legacy

    table2_scores = existing["table2_verified_scores"].copy()
    payload_table2 = payload.get("table2_verified_scores")
    if isinstance(payload_table2, dict):
        for key_name in TABLE2_VERIFIED_KEYS:
            if key_name in payload_table2:
                table2_scores[key_name] = _sanitize_score_value(payload_table2.get(key_name))

    review["table1_verified_teaching"] = table1_teaching
    review["table1_verified_activities"] = table1_activities
    review["table2_verified_scores"] = table2_scores
    data[key] = review

    return data, {
        "table1_verified_teaching": table1_teaching,
        "table1_verified_activities": table1_activities,
        "table2_verified_scores": table2_scores,
    }
