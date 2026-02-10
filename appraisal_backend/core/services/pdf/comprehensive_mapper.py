from typing import Dict
from core.models import Appraisal
from .data_mapper import get_common_pdf_data
from scoring.engine import calculate_full_score
from decimal import Decimal


def get_comprehensive_pdf_data(appraisal: Appraisal) -> Dict:
    """
    Extract all input data and calculated scores for comprehensive PDF generation.
    """
    base = get_common_pdf_data(appraisal)
    raw = base.get("raw", {})
    
    # Calculate scores using the scoring engine
    try:
        calculated_scores = calculate_full_score(raw)
    except Exception as e:
        # Fallback if scoring fails
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
    
    # Extract general info
    general = raw.get("general", {})
    
    # Extract teaching data
    teaching_courses = raw.get("teaching", {}).get("courses", [])
    
    # Extract activities
    activities = raw.get("activities", {})
    
    # Extract research entries
    research_entries = raw.get("research", {}).get("entries", [])
    
    # Extract PBAS sections
    pbas = raw.get("pbas", {})
    student_feedback = pbas.get("student_feedback", [])
    departmental_activities = pbas.get("departmental_activities", [])
    institute_activities = pbas.get("institute_activities", [])
    society_activities = pbas.get("society_activities", [])
    
    # Extract ACR data
    acr = raw.get("acr", {})
    
    # Format teaching data
    teaching_data = {
        "courses": teaching_courses,
        "total_scheduled": calculated_scores.get("teaching", {}).get("total_scheduled", 0),
        "total_held": calculated_scores.get("teaching", {}).get("total_held", 0),
        "attendance_percentage": calculated_scores.get("teaching", {}).get("attendance_percentage", 0),
        "course_count": calculated_scores.get("teaching", {}).get("course_count", 0),
    }
    
    # Format activities data
    activities_data = {
        "administrative_responsibility": activities.get("administrative_responsibility", False),
        "exam_duties": activities.get("exam_duties", False),
        "student_related": activities.get("student_related", False),
        "organizing_events": activities.get("organizing_events", False),
        "phd_guidance": activities.get("phd_guidance", False),
        "research_project": activities.get("research_project", False),
        "sponsored_project": activities.get("sponsored_project", False),
    }
    
    # Format research data
    research_data = {
        "entries": research_entries,
        "total_count": len(research_entries),
    }
    
    # Format PBAS data
    pbas_data = {
        "student_feedback": student_feedback,
        "departmental_activities": departmental_activities,
        "institute_activities": institute_activities,
        "society_activities": society_activities,
    }
    
    # Format ACR data
    acr_data = {
        "grade": acr.get("grade", ""),
    }
    
    # Format calculated scores
    scores = {
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
    }
    
    return {
        **base,
        "general": general,
        "teaching": teaching_data,
        "activities": activities_data,
        "research": research_data,
        "pbas": pbas_data,
        "acr": acr_data,
        "scores": scores,
        "academic_year": raw.get("academic_year", ""),
        "semester": raw.get("semester", ""),
        "form_type": raw.get("form_type", ""),
    }
