from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal


def get_enhanced_pbas_pdf_data(appraisal: Appraisal) -> Dict:
    """
    Extract all data for enhanced AICTE PBAS PDF generation with complete fields.
    """
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})
    
    # Calculate scores using the scoring engine
    try:
        calculated_scores = calculate_full_score(raw)
    except Exception as e:
        calculated_scores = {
            "teaching": {},
            "activities": {},
            "student_feedback": {},
            "departmental_activities": {},
            "institute_activities": {},
            "society_activities": {},
            "research": {},
            "pbas": {},
            "acr": {},
           "total_score": Decimal("0.00")
        }
    
    # Extract teaching data
    teaching_courses = raw.get("teaching", {}).get("courses", [])
    total_scheduled = calculated_scores.get("teaching", {}).get("total_scheduled", 0)
    total_held = calculated_scores.get("teaching", {}).get("total_held", 0)
    attendance_percentage = calculated_scores.get("teaching", {}).get("attendance_percentage", 0)
    
    # Extract PBAS sections
    pbas = raw.get("pbas", {})
    student_feedback = pbas.get("student_feedback", [])
    departmental_activities = pbas.get("departmental_activities", [])
    institute_activities = pbas.get("institute_activities", [])
    society_activities = pbas.get("society_activities", [])
    
    # Extract research entries
    research_entries = raw.get("research", {}).get("entries", [])
    journal_count = sum(1 for e in research_entries if "journal" in e.get("type", "").lower())
    conference_count = sum(1 for e in research_entries if "conference" in e.get("type", "").lower())
    
    # Extract ACR data
    acr = raw.get("acr", {})
    
    # Calculate overall grade
    if attendance_percentage >= 80:
        overall_grade = "Good"
    elif attendance_percentage >= 70:
        overall_grade = "Satisfactory"
    else:
        overall_grade = "Not Satisfactory"
    
    return {
        **base,
        
        # Teaching data
        "teaching": {
            "courses": teaching_courses,
            "total_scheduled": total_scheduled,
            "total_held": total_held,
            "attendance_percentage": attendance_percentage,
        },
        
        # PBAS Student Feedback
        "student_feedback": {
            "entries": student_feedback,
            "total_score": sum(float(f.get("feedback_score", 0)) for f in student_feedback),
        },
        
        # PBAS Departmental Activities
        "departmental_activities": {
            "entries": departmental_activities,
            "total_credits": sum(int(a.get("credits_claimed", 0)) for a in departmental_activities),
        },
        
        # PBAS Institute Activities
        "institute_activities": {
            "entries": institute_activities,
            "total_credits": sum(int(a.get("credits_claimed", 0)) for a in institute_activities),
        },
        
        # PBAS Society Activities
        "society_activities": {
            "entries": society_activities,
            "total_credits": sum(int(a.get("credits_claimed", 0)) for a in society_activities),
        },
        
        # Research
        "research": {
            "entries": research_entries,
            "journal_count": journal_count,
            "conference_count": conference_count,
            "total": journal_count + conference_count,
            "verified": "",
        },
        
        # ACR
        "acr": {
            "grade": acr.get("grade", ""),
        },
        
        # Calculated Scores
        "scores": {
            "overall_grade": overall_grade,
            "teaching_score": float(calculated_scores.get("teaching", {}).get("score", 0)),
            "activities_score": float(calculated_scores.get("activities", {}).get("score", 0)),
            "student_feedback_score": float(calculated_scores.get("student_feedback", {}).get("score", 0)),
            "departmental_score": float(calculated_scores.get("departmental_activities", {}).get("total_awarded", 0)),
            "institute_score": float(calculated_scores.get("institute_activities", {}).get("total_awarded", 0)),
            "society_score": float(calculated_scores.get("society_activities", {}).get("total_awarded", 0)),
            "research_score": float(calculated_scores.get("research", {}).get("total", 0)),
            "pbas_score": float(calculated_scores.get("pbas", {}).get("total", 0)),
            "acr_score": float(calculated_scores.get("acr", {}).get("credit_point", 0)),
            "total_score": float(calculated_scores.get("total_score", 0)),
        },
        
        # Metadata
        "academic_year": raw.get("academic_year", ""),
        "semester": raw.get("semester", ""),
        "form_type": "AICTE PBAS",
    }
