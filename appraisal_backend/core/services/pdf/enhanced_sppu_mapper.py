from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal
from core.services.sppu_verified import (
    derive_overall_grade,
    extract_verified_grading,
    TABLE2_VERIFIED_KEYS,
)
from scoring.activity_selection import derive_activity_flags


def _has_meaningful_research_data(entry: Dict) -> bool:
    """Ignore placeholder rows that carry only default structure."""
    if not isinstance(entry, dict):
        return False
    title = str(entry.get("title", "")).strip()
    name = str(entry.get("name", "")).strip()
    activity = str(entry.get("activity", "")).strip()
    year = str(entry.get("year", "")).strip()
    enclosure_no = str(entry.get("enclosure_no", "")).strip()
    enclosure = str(entry.get("enclosure", "")).strip()
    if not any([title, name, activity, year, enclosure_no, enclosure]):
        return False
    if title.lower() == "award" and not any([year, enclosure_no, enclosure]):
        return False
    return True


def _build_activity_flags(raw: Dict) -> Dict[str, bool]:
    combined = {
        "a_administrative": False,
        "b_exam_duties": False,
        "c_student_related": False,
        "d_organizing_events": False,
        "e_phd_guidance": False,
        "f_research_project": False,
        "g_sponsored_project": False,
    }
    sources = []
    for key in ("activities", "step2b", "section_b", "sectionB", "sppu"):
        data = raw.get(key)
        if isinstance(data, dict):
            sources.append(data)
            nested = data.get("activities")
            if isinstance(nested, dict):
                sources.append(nested)

    pbas = raw.get("pbas")
    if isinstance(pbas, dict):
        sources.append(pbas)
        pbas_activities = pbas.get("activities")
        if isinstance(pbas_activities, dict):
            sources.append(pbas_activities)
        step2b = pbas.get("step2b")
        if isinstance(step2b, dict):
            sources.append(step2b)

    for src in sources:
        flags = derive_activity_flags(src)
        for key in combined:
            combined[key] = combined[key] or flags.get(key, False)

    return combined


def get_enhanced_sppu_pdf_data(appraisal: Appraisal) -> Dict:
    """
    Extract data for SPPU PDF matching official format with Table 1 & Table 2.
    """
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})
    
    # Calculate scores using the scoring engine
    try:
        calculated_scores = calculate_full_score(raw)
    except Exception:
        calculated_scores = {
            "teaching": {},
            "activities": {},
            "research": {},
            "total_score": Decimal("0.00")
        }
    
    # ========== TABLE 1: TEACHING ========== 
    teaching_courses = raw.get("teaching", {}).get("courses", [])
    
    # Directly sum teaching data from courses
    total_scheduled = 0
    total_held = 0
    
    for course in teaching_courses:
        # Handle all field name variations
        scheduled = course.get("total_classes_assigned", course.get("scheduled_classes", 0))
        taught = course.get("classes_taught", course.get("held_classes", course.get("total_classes_taught", 0)))
        
        total_scheduled += int(scheduled)
        total_held += int(taught)
    
    # Calculate attendance percentage
    if total_scheduled > 0:
        attendance_percentage = (total_held / total_scheduled) * 100
    else:
        attendance_percentage = 0
    
    # Teaching grade based on SPPU criteria
    if attendance_percentage >= 80:
        teaching_grade = "Good"
    elif attendance_percentage >= 70:
        teaching_grade = "Satisfactory"
    else:
        teaching_grade = "Not Satisfactory"
    
    # ========== TABLE 1: ACTIVITIES (with checkboxes a-g) ==========
    activities_checkboxes = _build_activity_flags(raw)
    
    # Count checked activities
    activity_count = sum(1 for v in activities_checkboxes.values() if v)
    
    # Activities grade
    if activity_count >= 3:
        activities_grade = "Good"
    elif activity_count >= 1:
        activities_grade = "Satisfactory"
    else:
        activities_grade = "Not Satisfactory"
    
    # ========== TABLE 2: RESEARCH SCORING ==========
    research_entries = raw.get("research", {}).get("entries", [])
    
    # Initialize Table 2 categories with counts and scores
    table2_categories = {
        # 1. Research Papers
        "peer_reviewed_journals": {"count": 0, "score_per": 8, "total_score": 0},
        
        # 2. Publications
        "books_international": {"count": 0, "score_per": 12, "total_score": 0},
        "books_national": {"count": 0, "score_per": 10, "total_score": 0},
        "chapter_edited_book": {"count": 0, "score_per": 5, "total_score": 0},
        "editor_book_international": {"count": 0, "score_per": 10, "total_score": 0},
        "editor_book_national": {"count": 0, "score_per": 8, "total_score": 0},
        "translation_chapter_or_paper": {"count": 0, "score_per": 3, "total_score": 0},
        "translation_book": {"count": 0, "score_per": 8, "total_score": 0},
        "chapter_research_compilation": {"count": 0, "score_per": 3, "total_score": 0},
        
        # 3. ICT Mediated Teaching
        "pedagogy_development": {"count": 0, "score_per": 5, "total_score": 0},
        "curriculum_design": {"count": 0, "score_per": 2, "total_score": 0},
        "moocs_4quadrant": {"count": 0, "score_per": 20, "total_score": 0},
        "moocs_single_lecture": {"count": 0, "score_per": 5, "total_score": 0},
        "moocs_content_writer": {"count": 0, "score_per": 2, "total_score": 0},
        "moocs_coordinator": {"count": 0, "score_per": 8, "total_score": 0},
        "econtent_4quadrant_complete": {"count": 0, "score_per": 12, "total_score": 0},
        "econtent_4quadrant_per_module": {"count": 0, "score_per": 5, "total_score": 0},
        "econtent_module_contribution": {"count": 0, "score_per": 2, "total_score": 0},
        "econtent_editor": {"count": 0, "score_per": 10, "total_score": 0},
        
        # 4. Research Guidance
        "phd_awarded": {"count": 0, "score_per": 10, "total_score": 0},
        "phd_submitted": {"count": 0, "score_per": 5, "total_score": 0},
        "mphil_pg_dissertation": {"count": 0, "score_per": 2, "total_score": 0},
        "research_project_above_10l": {"count": 0, "score_per": 10, "total_score": 0},
        "research_project_below_10l": {"count": 0, "score_per": 5, "total_score": 0},
        "research_project_ongoing_above_10l": {"count": 0, "score_per": 5, "total_score": 0},
        "research_project_ongoing_below_10l": {"count": 0, "score_per": 2, "total_score": 0},
        "consultancy": {"count": 0, "score_per": 3, "total_score": 0},
        
        # 5. Patents
        "patent_international": {"count": 0, "score_per": 10, "total_score": 0},
        "patent_national": {"count": 0, "score_per": 7, "total_score": 0},
        
        # 6. Policy Documents
        "policy_international": {"count": 0, "score_per": 10, "total_score": 0},
        "policy_national": {"count": 0, "score_per": 7, "total_score": 0},
        "policy_state": {"count": 0, "score_per": 4, "total_score": 0},
        
        # 7. Awards/Fellowship
        "award_international": {"count": 0, "score_per": 7, "total_score": 0},
        "award_national": {"count": 0, "score_per": 5, "total_score": 0},
        
        # 8. Conference Presentations
        "conference_international_abroad": {"count": 0, "score_per": 7, "total_score": 0},
        "conference_international_country": {"count": 0, "score_per": 5, "total_score": 0},
        "conference_national": {"count": 0, "score_per": 3, "total_score": 0},
        "conference_state_university": {"count": 0, "score_per": 2, "total_score": 0},
    }
    
    # Map research entries to Table 2 categories
    explicit_type_map = {
        "mooc_complete_4_quadrant": "moocs_4quadrant",
        "mooc_per_module": "moocs_single_lecture",
        "mooc_content_writer": "moocs_content_writer",
        "mooc_course_coordinator": "moocs_coordinator",
        "econtent_complete_course": "econtent_4quadrant_complete",
        "econtent_4quadrant_per_module": "econtent_4quadrant_per_module",
        "econtent_module_contribution": "econtent_module_contribution",
        "econtent_editor": "econtent_editor",
        "innovative_pedagogy_development": "pedagogy_development",
        "pedagogy_development": "pedagogy_development",
        "new_curriculum": "curriculum_design",
        "curriculum_design": "curriculum_design",
    }

    for entry in research_entries:
        if not isinstance(entry, dict):
            continue
        entry_type = str(entry.get("type", "")).strip().lower()
        if not entry_type or not _has_meaningful_research_data(entry):
            continue
        try:
            count = int(float(entry.get("count", 0)))
        except (TypeError, ValueError):
            count = 0
        if count <= 0:
            continue

        mapped_key = explicit_type_map.get(entry_type)
        if mapped_key:
            table2_categories[mapped_key]["count"] += count
            continue
        
        # Category 1: Research Papers (handle various journal naming patterns)
        if ("journal" in entry_type or "paper" in entry_type) and not ("book" in entry_type):
            table2_categories["peer_reviewed_journals"]["count"] += count
        
        # Category 2: Publications
        elif "book" in entry_type:
            if "international" in entry_type:
                if "editor" in entry_type:
                    table2_categories["editor_book_international"]["count"] += count
                else:
                    table2_categories["books_international"]["count"] += count
            elif "national" in entry_type:
                if "editor" in entry_type:
                    table2_categories["editor_book_national"]["count"] += count
                else:
                    table2_categories["books_national"]["count"] += count
        
        elif "chapter" in entry_type:
            if "compilation" in entry_type or "research" in entry_type:
                table2_categories["chapter_research_compilation"]["count"] += count
            else:
                table2_categories["chapter_edited_book"]["count"] += count
        
        elif "translation" in entry_type:
            if "book" in entry_type:
                table2_categories["translation_book"]["count"] += count
            else:
                table2_categories["translation_chapter_or_paper"]["count"] += count
        
        # Category 3: ICT/MOOCs/e-Content
        elif "mooc" in entry_type:
            if "4" in entry_type or "quadrant" in entry_type:
                table2_categories["moocs_4quadrant"]["count"] += count
            elif "lecture" in entry_type:
                table2_categories["moocs_single_lecture"]["count"] += count
            elif "writer" in entry_type or "content" in entry_type:
                table2_categories["moocs_content_writer"]["count"] += count
            elif "coordinator" in entry_type:
                table2_categories["moocs_coordinator"]["count"] += count
        
        elif "pedagogy" in entry_type or "innovative" in entry_type:
            table2_categories["pedagogy_development"]["count"] += count
        
        elif "curriculum" in entry_type or "course" in entry_type:
            table2_categories["curriculum_design"]["count"] += count
        
        elif "econtent" in entry_type or "e-content" in entry_type:
            if "4quadrant" in entry_type or "complete" in entry_type:
                table2_categories["econtent_4quadrant_complete"]["count"] += count
            elif "module" in entry_type and "per" in entry_type:
                table2_categories["econtent_4quadrant_per_module"]["count"] += count
            elif "contribution" in entry_type:
                table2_categories["econtent_module_contribution"]["count"] += count
            elif "editor" in entry_type:
                table2_categories["econtent_editor"]["count"] += count
        
        # Category 4: Research Guidance
        elif "phd" in entry_type:
            if "awarded" in entry_type or "degree" in entry_type:
                table2_categories["phd_awarded"]["count"] += count
            elif "submitted" in entry_type or "thesis" in entry_type:
                table2_categories["phd_submitted"]["count"] += count
        
        elif "mphil" in entry_type or "pg" in entry_type or "dissertation" in entry_type:
            table2_categories["mphil_pg_dissertation"]["count"] += count
        
        elif "project" in entry_type:
            if "ongoing" in entry_type:
                # Support "gt_10", "above_10", ">10", etc.
                if any(k in entry_type for k in [">10", "above", "gt_10"]):
                    table2_categories["research_project_ongoing_above_10l"]["count"] += count
                else:
                    table2_categories["research_project_ongoing_below_10l"]["count"] += count
            else:
                if any(k in entry_type for k in [">10", "above", "gt_10"]):
                    table2_categories["research_project_above_10l"]["count"] += count
                else:
                    table2_categories["research_project_below_10l"]["count"] += count
        
        elif "consultancy" in entry_type:
            table2_categories["consultancy"]["count"] += count
        
        # Category 5: Patents
        elif "patent" in entry_type:
            if "international" in entry_type:
                table2_categories["patent_international"]["count"] += count
            else:
                table2_categories["patent_national"]["count"] += count
        
        # Category 6: Policy
        elif "policy" in entry_type:
            if "international" in entry_type:
                table2_categories["policy_international"]["count"] += count
            elif "national" in entry_type:
                table2_categories["policy_national"]["count"] += count
            else:
                table2_categories["policy_state"]["count"] += count
        
        # Category 7: Awards
        elif "award" in entry_type or "fellowship" in entry_type:
            if "international" in entry_type:
                table2_categories["award_international"]["count"] += count
            else:
                table2_categories["award_national"]["count"] += count
        
        # Category 8: Conferences / Invited Lectures
        elif any(k in entry_type for k in ["conference", "presentation", "lecture", "talk", "resource", "invited"]):
            if "international" in entry_type:
                if "abroad" in entry_type:
                    table2_categories["conference_international_abroad"]["count"] += count
                else:
                    table2_categories["conference_international_country"]["count"] += count
            elif "national" in entry_type:
                table2_categories["conference_national"]["count"] += count
            elif any(k in entry_type for k in ["state", "university"]):
                table2_categories["conference_state_university"]["count"] += count
    
    # Calculate scores for each category
    for category_data in table2_categories.values():
        category_data["total_score"] = category_data["count"] * category_data["score_per"]
    
    # Calculate total Table 2 score
    table2_total_score = sum(cat["total_score"] for cat in table2_categories.values())
    
    # ========== OVERALL / VERIFIED GRADING ==========
    overall_grade = derive_overall_grade(teaching_grade, activities_grade)

    show_verified_grade = appraisal.status in {
        "REVIEWED_BY_HOD",
        "HOD_APPROVED",
        "REVIEWED_BY_PRINCIPAL",
        "PRINCIPAL_APPROVED",
        "FINALIZED",
    }

    verified_grading = extract_verified_grading(raw, appraisal.is_hod_appraisal is True)
    table1_verified_teaching = verified_grading.get("table1_verified_teaching", "")
    table1_verified_activities = verified_grading.get("table1_verified_activities", "")
    table2_verified_scores = verified_grading.get("table2_verified_scores", {})

    if not table1_verified_teaching and hasattr(appraisal, "appraisalscore"):
        table1_verified_teaching = appraisal.appraisalscore.verified_grade or ""
    if not table1_verified_activities and hasattr(appraisal, "appraisalscore"):
        table1_verified_activities = appraisal.appraisalscore.verified_grade or ""

    if not show_verified_grade:
        table1_verified_teaching = ""
        table1_verified_activities = ""
        table2_verified_scores = {key: "" for key in TABLE2_VERIFIED_KEYS}

    verified_overall_grade = derive_overall_grade(
        table1_verified_teaching or teaching_grade,
        table1_verified_activities or activities_grade,
    )

    hod_review = raw.get("hod_review", {})
    if not isinstance(hod_review, dict):
        hod_review = {}
    hod_comments_table1 = hod_review.get("comments_table1", "") or ""
    hod_comments_table2 = hod_review.get("comments_table2", "") or ""
    hod_remarks = hod_review.get("remarks_suggestions", "") or ""
    justification = (
        hod_review.get("justification", "")
        or raw.get("justification", "")
        or (raw.get("pbas", {}) or {}).get("justification", "")
        or ""
    )
    principal_remarks = (base.get("remarks", {}) or {}).get("principal", "")
    
    return {
        **base,
        
        # TABLE 1 - Teaching
        "table1_teaching": {
            "courses": teaching_courses,
            "total_assigned": total_scheduled,
            "total_taught": total_held,
            "percentage": f"{attendance_percentage:.2f}",
            "self_grade": teaching_grade,
            "verified_grade": table1_verified_teaching,
        },
        
        # TABLE 1 - Activities
        "table1_activities": {
            "checkboxes": activities_checkboxes,
            "count": activity_count,
            "self_grade": activities_grade,
            "verified_grade": table1_verified_activities,
        },

        # TABLE 2 - Research Scoring
        "table2_research": table2_categories,
        "table2_verified": table2_verified_scores,
        "table2_total_score": table2_total_score,
        
        # PART B - Assessment
        "part_b": {
            "overall_grade": overall_grade,
            "verified_grade": verified_overall_grade if show_verified_grade else "",
            "hod_assessment": "",
            "justification": justification,
            "hod_comments_table1": hod_comments_table1,
            "hod_comments_table2": hod_comments_table2,
            "hod_remarks": hod_remarks,
            "principal_remarks": principal_remarks,
        },
        
        # Metadata
        "academic_year": raw.get("academic_year") or appraisal.academic_year or base.get("period", ""),
        "semester": raw.get("semester") or appraisal.semester or "",
        "form_type": "SPPU",
    }
