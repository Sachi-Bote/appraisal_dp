from typing import Dict, List
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal


def _to_bool(value) -> bool:
    """
    Normalize frontend payload values to boolean.
    Handles bool, int, and string values like Yes/No, True/False, 1/0.
    """
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


def _get_first_key(data: Dict, keys: List[str], default=False):
    for key in keys:
        if key in data:
            return data.get(key)
    return default


def _build_activity_flags(raw: Dict) -> Dict[str, bool]:
    """
    Resolve activity flags from multiple payload shapes used by frontend versions.
    Priority: explicit per-activity fields. Category-derived mapping is optional.
    """
    # DEBUG: Log input structure
    print("\n" + "="*80)
    print("DEBUG: _build_activity_flags called")
    print("="*80)
    print(f"Raw dict keys: {list(raw.keys())}")
    
    activities = raw.get("activities", {})
    print(f"\nActivities section type: {type(activities)}")
    if isinstance(activities, dict):
        print(f"Activities keys: {list(activities.keys())}")
        print(f"Activities values: {activities}")
    
    sources = []
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

    print(f"\nTotal sources to search: {len(sources)}")
    
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

    for idx, src in enumerate(sources):
        print(f"\nSearching source {idx}: {type(src)}")
        if isinstance(src, dict):
            print(f"  Source keys: {list(src.keys())}")
        
        if not isinstance(src, dict):
            continue
        for target, aliases in key_aliases.items():
            if resolved[target] is not None:
                continue
            for alias in aliases:
                if alias in src:
                    value = src.get(alias)
                    resolved[target] = _to_bool(value)
                    print(f"  FOUND: {alias} = {value} -> {resolved[target]} (for {target})")
                    break

    # Optional legacy mapping: derive from departmental/institute/society if explicit flags are absent.
    if all(v is None for v in resolved.values()):
        print("\n*** WARNING: No individual activities found!")
        print("This shouldn't happen with current frontend - check data structure")
        use_legacy_derivation = False  # DISABLED - frontend should send individual flags
        if use_legacy_derivation and isinstance(activities, dict):
            departmental = _to_bool(_get_first_key(activities, ["departmental", "departmental_activities", "departmentalActivities"], False))
            institute = _to_bool(_get_first_key(activities, ["institute", "institute_activities", "instituteActivities"], False))
            society = _to_bool(_get_first_key(activities, ["society", "society_activities", "societyActivities"], False))
            
            print(f"  Departmental flag: {departmental}")
            print(f"  Institute flag: {institute}")
            print(f"  Society flag: {society}")
            
            resolved = {
                "a_administrative": departmental,
                "b_exam_duties": departmental,
                "c_student_related": society,
                "d_organizing_events": institute,
                "e_phd_guidance": departmental,
                "f_research_project": departmental or institute,
                "g_sponsored_project": institute,
            }

    print(f"\nFinal resolved values: {resolved}")
    print("="*80 + "\n")
    
    # Ensure None values are converted to False
    return {k: bool(v) if v is not None else False for k, v in resolved.items()}


def get_enhanced_sppu_pdf_data(appraisal: Appraisal) -> Dict:
    """
    Extract data for SPPU PDF matching official format with Table 1 & Table 2.
    """
    print(f"\n*** PROCESSING APPRAISAL ID: {appraisal.appraisal_id} ***")
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
