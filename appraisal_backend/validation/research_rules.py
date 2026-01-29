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
from scoring.research import POINTS


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

def validate_research_payload(payload: dict):
    if not isinstance(payload, dict):
        return False, "research must be an object"

    entries = payload.get("entries")
    if not isinstance(entries, list):
        return False, "research.entries must be a list"

    if len(entries) == 0:
        return True, ""  # research is optional

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return False, f"Research entry {i+1} must be an object"

        activity_type = entry.get("type")
        if not activity_type:
            return False, f"Research entry {i+1} missing 'type'"

        if activity_type not in POINTS:
            return False, f"Unknown research activity '{activity_type}'"

    return True, ""

