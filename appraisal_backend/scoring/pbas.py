from scoring.research import POINTS


def calculate_pbas_score(appraisal_data: dict) -> dict:
    breakdown = {}
    total = 0

    # 1. Research Papers
    research = appraisal_data.get("research", {})
    journal = research.get("journal_papers", 0)
    conference = research.get("conference_papers", 0)

    breakdown["journal_papers"] = journal * POINTS["journal_papers"]
    breakdown["conference_papers"] = conference * POINTS["journal_papers"]

    total += breakdown["journal_papers"] + breakdown["conference_papers"]

    # 2. Publications
    publications = appraisal_data.get("publications", {})
    for key in [
        "book_international",
        "book_national",
        "edited_book_chapter",
        "editor_book_international",
        "editor_book_national",
        "translation_chapter_or_paper",
        "translation_book"
    ]:
        count = publications.get(key, 0)
        breakdown[key] = count * POINTS[key]
        total += breakdown[key]

    # 3. ICT / MOOCs / E-Content
    ict = appraisal_data.get("ict", {})
    breakdown["innovative_pedagogy"] = (
        ict.get("innovative_pedagogy", 0) * POINTS["innovative_pedagogy"]
    )
    total += breakdown["innovative_pedagogy"]

    mooc = ict.get("mooc", {})
    breakdown["mooc_module"] = mooc.get("module", 0) * POINTS["mooc_module"]
    total += breakdown["mooc_module"]

    # 4. Research Guidance
    guidance = appraisal_data.get("research_guidance", {})
    breakdown["phd_awarded"] = guidance.get("phd_awarded", 0) * POINTS["phd_awarded"]
    total += breakdown["phd_awarded"]

    # 5. Patents
    patents = appraisal_data.get("patents", {})
    breakdown["patent_international"] = (
        patents.get("international", 0) * POINTS["patent_international"]
    )
    total += breakdown["patent_international"]

    # 6. Invited Lectures
    invited = appraisal_data.get("invited_lectures", {})
    breakdown["invited_lecture_national"] = (
        invited.get("national", 0) * POINTS["invited_lecture_national"]
    )
    total += breakdown["invited_lecture_national"]

    return {
        "breakdown": breakdown,
        "total": total
    }
