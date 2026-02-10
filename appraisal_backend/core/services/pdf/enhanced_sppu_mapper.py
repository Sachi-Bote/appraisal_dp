from typing import Dict, List
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal


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
    activities_dict = raw.get("activities", {})
    
    # Check if using detailed structure or general categories
    has_detailed_flags = "administrative_responsibility" in activities_dict
    
    if has_detailed_flags:
        # Use detailed boolean flags (if available)
        activities_checkboxes = {
            "a_administrative": activities_dict.get("administrative_responsibility", False),
            "b_exam_duties": activities_dict.get("exam_duties", False),
            "c_student_related": activities_dict.get("student_related", False),
            "d_organizing_events": activities_dict.get("organizing_events", False),
            "e_phd_guidance": activities_dict.get("phd_guidance", False),
            "f_research_project": activities_dict.get("research_project", False),
            "g_sponsored_project": activities_dict.get("sponsored_project", False),
        }
    else:
        # Map from general categories (departmental, institute, society)
        departmental = activities_dict.get("departmental", False)
        institute = activities_dict.get("institute", False)
        society = activities_dict.get("society", False)
        
        activities_checkboxes = {
            "a_administrative": departmental,  # Administrative work is departmental
            "b_exam_duties": departmental,     # Exam duties are departmental
            "c_student_related": society,      # Student activities are society work
            "d_organizing_events": institute,  # Institute events
            "e_phd_guidance": departmental,    # PhD guidance is departmental
            "f_research_project": departmental or institute,  # Research can be both
            "g_sponsored_project": institute,  # Sponsored projects are institute level
        }
    
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
        "translation_works": {"count": 0, "score_per": 3, "total_score": 0},
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
        "policy_international": {"count": 0, "score_per": 7, "total_score": 0},
        "policy_national": {"count": 0, "score_per": 4, "total_score": 0},
        
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
    for entry in research_entries:
        entry_type = entry.get("type", "").lower()
        count = int(entry.get("count", 1))
        
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
            table2_categories["translation_works"]["count"] += count
        
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
                if ">10" in entry_type or "above" in entry_type:
                    table2_categories["research_project_ongoing_above_10l"]["count"] += count
                else:
                    table2_categories["research_project_ongoing_below_10l"]["count"] += count
            else:
                if ">10" in entry_type or "above" in entry_type:
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
            else:
                table2_categories["policy_national"]["count"] += count
        
        # Category 7: Awards
        elif "award" in entry_type or "fellowship" in entry_type:
            if "international" in entry_type:
                table2_categories["award_international"]["count"] += count
            else:
                table2_categories["award_national"]["count"] += count
        
        # Category 8: Conferences
        elif "conference" in entry_type or "presentation" in entry_type:
            if "international" in entry_type:
                if "abroad" in entry_type:
                    table2_categories["conference_international_abroad"]["count"] += count
                else:
                    table2_categories["conference_international_country"]["count"] += count
            elif "national" in entry_type:
                table2_categories["conference_national"]["count"] += count
            elif "state" in entry_type or "university" in entry_type:
                table2_categories["conference_state_university"]["count"] += count
    
    # Calculate scores for each category
    for category_data in table2_categories.values():
        category_data["total_score"] = category_data["count"] * category_data["score_per"]
    
    # Calculate total Table 2 score
    table2_total_score = sum(cat["total_score"] for cat in table2_categories.values())
    
    # ========== OVERALL GRADING ==========
    if teaching_grade == "Good" and activities_grade in ["Good", "Satisfactory"]:
        overall_grade = "Good"
    elif teaching_grade == "Satisfactory" and activities_grade in ["Good", "Satisfactory"]:
        overall_grade = "Satisfactory"
    else:
        overall_grade = "Not Satisfactory"
    
    return {
        **base,
        
        # TABLE 1 - Teaching
        "table1_teaching": {
            "courses": teaching_courses,
            "total_assigned": total_scheduled,
            "total_taught": total_held,
            "percentage": f"{attendance_percentage:.2f}",
            "self_grade": teaching_grade,
            "verified_grade": "",
        },
        
        # TABLE 1 - Activities
        "table1_activities": {
            "checkboxes": activities_checkboxes,
            "count": activity_count,
            "self_grade": activities_grade,
            "verified_grade": "",
        },
        
        # TABLE 2 - Research Scoring
        "table2_research": table2_categories,
        "table2_total_score": table2_total_score,
        
        # PART B - Assessment
        "part_b": {
            "overall_grade": overall_grade,
            "hod_assessment": "",
            "justification": "",
            "hod_comments_table1": "",
            "hod_comments_table2": "",
        },
        
        # Metadata
        "academic_year": raw.get("academic_year", ""),
        "semester": raw.get("semester", ""),
        "form_type": "SPPU",
    }
