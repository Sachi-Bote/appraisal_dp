# validation/research_rules.py
"""
Validations for research/publication-related fields (PBAS – Section C).
Expected payload example:

{
  "journal_papers": 3,
  "book_international": 1,
  "edited_book_chapter": 2,
  "translation_book": 1,
  "mooc_complete_4_quadrant": 1,
  "phd_awarded": 1,
  "project_completed_gt_10_lakhs": 1,
  "patent_national": 1,
  "invited_lecture_national": 2
}
"""

from typing import Dict, Tuple
from .global_rules import is_non_negative_int


# ============================================================
# ALLOWED RESEARCH KEYS (MUST MATCH scoring/research.py)
# ============================================================

ALLOWED_KEYS = {

    # 1. Research Papers
    "journal_papers",

    # 2. Publications – Books
    "book_international",
    "book_national",
    "edited_book_chapter",
    "editor_book_international",
    "editor_book_national",

    # Translation Works
    "translation_chapter_or_paper",
    "translation_book",

    # 3. ICT / MOOCs / E-Content
    "innovative_pedagogy",
    "new_curriculum",
    "new_course",

    "mooc_complete_4_quadrant",
    "mooc_module",
    "mooc_content_writer",
    "mooc_course_coordinator",

    "econtent_complete_course",
    "econtent_module",
    "econtent_contribution",
    "econtent_editor",

    # 4. Research Guidance
    "phd_awarded",
    "mphil_submitted",
    "pg_dissertation_awarded",

    # Research Projects
    "project_completed_gt_10_lakhs",
    "project_completed_lt_10_lakhs",
    "project_ongoing_gt_10_lakhs",
    "project_ongoing_lt_10_lakhs",

    # Consultancy
    "consultancy",

    # 5. Patents
    "patent_international",
    "patent_national",

    # Policy Documents
    "policy_international",
    "policy_national",
    "policy_state",

    # Awards / Fellowship
    "award_international",
    "award_national",

    # 6. Invited Lectures / Conferences
    "invited_lecture_international_abroad",
    "invited_lecture_international_india",
    "invited_lecture_national",
    "invited_lecture_state_university",
}


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate_research_payload(payload: Dict) -> Tuple[bool, str]:

    if not isinstance(payload, dict):
        return False, "Research payload must be a JSON object."

    if not payload:
        return False, "At least one research activity must be provided."

    for key, value in payload.items():
        if key not in ALLOWED_KEYS:
            return (
                False,
                f"Unknown research field '{key}'. "
                f"Allowed fields: {sorted(ALLOWED_KEYS)}"
            )

        if not is_non_negative_int(value):
            return False, f"Research field '{key}' must be a non-negative integer."

    return True, ""
