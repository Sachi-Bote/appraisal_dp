# scoring/research.py

# -------------------------------------------------------------------
# POINTS CONFIG (as per provided appraisal tables)
# -------------------------------------------------------------------

POINTS = {

    # 1. Research Papers
    "journal_papers": 8,  # per paper (UGC / Peer-reviewed)

    # 2. Publications (other than research papers)
    # (a) Books
    "book_international": 12,
    "book_national": 10,
    "edited_book_chapter": 5,
    "editor_book_international": 10,
    "editor_book_national": 8,

    # (b) Translation works
    "translation_chapter_or_paper": 3,
    "translation_book": 8,

    # 3. ICT / Pedagogy / MOOCs / E-Content
    # (a) Innovative pedagogy
    "innovative_pedagogy": 5,

    # (b) New curricula / courses
    "new_curriculum": 2,        # per curriculum/course
    "new_course": 2,            # per course

    # MOOCs
    "mooc_complete_4_quadrant": 20,
    "mooc_module": 5,           # per module/lecture
    "mooc_content_writer": 2,   # per module (min one quadrant)
    "mooc_course_coordinator": 8,

    # (d) E-Content
    "econtent_complete_course": 12,
    "econtent_module": 5,
    "econtent_contribution": 2,
    "econtent_editor": 10,

    # 4. Research Guidance
    "phd_awarded": 10,
    "mphil_submitted": 5,
    "pg_dissertation_awarded": 2,

    # Research Projects Completed
    "project_completed_gt_10_lakhs": 10,
    "project_completed_lt_10_lakhs": 5,

    # Research Projects Ongoing
    "project_ongoing_gt_10_lakhs": 5,
    "project_ongoing_lt_10_lakhs": 2,

    # Consultancy
    "consultancy": 3,

    # 5. Patents
    "patent_international": 10,
    "patent_national": 7,

    # Policy Documents
    "policy_international": 10,
    "policy_national": 7,
    "policy_state": 4,

    # Awards / Fellowship
    "award_international": 7,
    "award_national": 5,

    # 6. Invited Lectures / Conferences
    "invited_lecture_international_abroad": 7,
    "invited_lecture_international_india": 5,
    "invited_lecture_national": 3,
    "invited_lecture_state_university": 2,
}

# CALCULATION LOGIC


# scoring/research.py

def calculate_research_score(payload: dict) -> dict:
    """
    Expected input:
    {
        "entries": [
            {"type": "journal_papers"},
            {"type": "journal_papers"},
            {"type": "book_international"},
            {"type": "invited_lecture_national"}
        ]
    }
    """

    entries = payload.get("entries", [])

    breakdown = {}
    total = 0

    # 1️⃣ COUNT how many times each research type appears
    for entry in entries:
        activity_type = entry.get("type")

        if activity_type not in POINTS:
            continue  # ignore unsupported entries safely

        if activity_type not in breakdown:
            breakdown[activity_type] = {
                "count": 0,
                "points_per_unit": POINTS[activity_type],
                "score": 0
            }

        breakdown[activity_type]["count"] += 1

    # 2️⃣ MULTIPLY count × points (THIS is your exact rule)
    for activity_type, data in breakdown.items():
        data["score"] = data["count"] * data["points_per_unit"]
        total += data["score"]

    return {
        "breakdown": breakdown,
        "total": total
    }
