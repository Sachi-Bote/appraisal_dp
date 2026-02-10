"""
Test script to verify the enhanced SPPU and PBAS PDF generation functionality.
This script creates test appraisals with sample data and generates both PDF types.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, r'd:\appraisal_dp\appraisal_backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal, FacultyProfile, Department, User
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from core.services.pdf.enhanced_pbas_mapper import get_enhanced_pbas_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf

# Sample payload matching the Sample_Payload.json structure
sample_data = {
    "academic_year": "2024-25",
    "semester": "Odd",
    "form_type": "PBAS",
    "general": {
        "faculty_name": "Dr ABC",
        "department": "Computer Engineering",
        "designation": "Assistant Professor"
    },
    "teaching": {
        "courses": [
            {
                "semester": "1/2024-25",
                "course_code": "CS101",
                "course_name": "Data Structures",
                "scheduled_classes": 48,
                "held_classes": 45
            },
            {
                "semester": "1/2024-25",
                "course_code": "CS102",
                "course_name": "Algorithms",
                "scheduled_classes": 56,
                "held_classes": 52
            }
        ]
    },
    "activities": {
        "administrative_responsibility": True,
        "exam_duties": True,
        "student_related": False,
        "organizing_events": True,
        "phd_guidance": False,
        "research_project": False,
        "sponsored_project": False
    },
    "research": {
        "entries": [
            {
                "type": "journal_papers",
                "count": 2,
                "title": "Efficient Graph Algorithms",
                "year": 2024,
                "enclosure_no": "R1"
            },
            {
                "type": "book_national",
                "count": 1,
                "title": "Computer Networks",
                "year": 2023,
                "enclosure_no": "R2"
            },
            {
                "type": "conference_papers",
                "count": 3,
                "title": "Machine Learning Applications",
                "year": 2024,
                "enclosure_no": "R3"
            }
        ]
    },
    "pbas": {
        "student_feedback": [
            {
                "semester": "1/2024-25",
                "course_code": "CS301",
                "course_name": "Data Structures",
                "feedback_score": 18.5,
                "enclosure_no": "FB1"
            },
            {
                "semester": "1/2024-25",
                "course_code": "CS302",
                "course_name": "Algorithms",
                "feedback_score": 17.5,
                "enclosure_no": "FB2"
            }
        ],
        "departmental_activities": [
            {
                "activity": "NBA Coordinator",
                "semester": "1/2024-25",
                "credits_claimed": 3,
                "enclosure_no": "D1"
            },
            {
                "activity": "NAAC Committee Member",
                "semester": "1/2024-25",
                "credits_claimed": 2,
                "enclosure_no": "D2"
            }
        ],
        "institute_activities": [
            {
                "activity": "Institute Website Management",
                "semester": "1/2024-25",
                "credits_claimed": 4,
                "enclosure_no": "I1"
            },
            {
                "activity": "Library Committee",
                "semester": "1/2024-25",
                "credits_claimed": 2,
                "enclosure_no": "I2"
            }
        ],
        "society_activities": [
            {
                "activity": "Blood Donation Activity",
                "semester": "2/2024-25",
                "credits_claimed": 5,
                "enclosure_no": "S1"
            },
            {
                "activity": "Tree Plantation Drive",
                "semester": "2/2024-25",
                "credits_claimed": 3,
                "enclosure_no": "S2"
            }
        ],
        "teaching_process": 18,
        "feedback": 17,
        "department": 14,
        "institute": 8,
        "acr": 9,
        "society": 6
    },
    "acr": {
        "grade": "Outstanding"
    }
}

def test_enhanced_pdfs():
    print("=" * 70)
    print("Testing Enhanced SPPU and PBAS PDF Generation")
    print("=" * 70)
    
    try:
        # Setup test data
        print("\n1. Setting up test data...")
        
        dept, _ = Department.objects.get_or_create(
            department_name="Computer Engineering"
        )
        
        user, _ = User.objects.get_or_create(
            username="test_faculty_enhanced",
            defaults={
                "role": "FACULTY",
                "full_name": "Dr ABC",
                "designation": "Assistant Professor",
                "department": "Computer Engineering"
            }
        )
        
        faculty, _ = FacultyProfile.objects.get_or_create(
            user=user,
            defaults={
                "department": dept,
                "full_name": "Dr ABC",
                "designation": "Assistant Professor",
                "email": "test@example.com",
                "mobile": "9876543210"
            }
        )
        
        appraisal, created = Appraisal.objects.update_or_create(
            faculty=faculty,
            academic_year="2024-25",
            semester="Odd",
            form_type="PBAS",
            defaults={
                "appraisal_data": sample_data,
                "status": "DRAFT"
            }
        )
        
        print(f"✓ Test appraisal ready (ID: {appraisal.appraisal_id})")
        
        # Test SPPU PDF
        print("\n2. Testing Enhanced SPPU PDF...")
        sppu_context = get_enhanced_sppu_pdf_data(appraisal)
        print(f"  ✓ SPPU data mapper executed")
        print(f"    - Teaching courses: {len(sppu_context.get('teaching', {}).get('courses', []))}")
        print(f"    - Activities: {len(sppu_context.get('activities', {}).get('list', []))}")
        print(f"    - Research entries: {len(sppu_context.get('research', {}).get('entries', []))}")
        print(f"    - Teaching score: {sppu_context.get('scores', {}).get('teaching_score')}")
        print(f"    - Total score: {sppu_context.get('scores', {}).get('total_score')}")
        
        sppu_pdf = render_to_pdf("pdf/enhanced_sppu.html", sppu_context)
        
        if sppu_pdf.status_code == 200:
            output_dir = r"d:\appraisal_dp\appraisal_backend\generated_pdfs"
            os.makedirs(output_dir, exist_ok=True)
            sppu_path = os.path.join(output_dir, f"enhanced_sppu_{appraisal.appraisal_id}.pdf")
            
            with open(sppu_path, 'wb') as f:
                f.write(sppu_pdf.content)
            
            print(f"  ✓ SPPU PDF generated successfully!")
            print(f"    - Saved to: {sppu_path}")
            print(f"    - Size: {len(sppu_pdf.content)} bytes")
        else:
            print(f"  ✗ SPPU PDF generation failed!")
            return False
        
        # Test PBAS PDF
        print("\n3. Testing Enhanced PBAS PDF...")
        pbas_context = get_enhanced_pbas_pdf_data(appraisal)
        print(f"  ✓ PBAS data mapper executed")
        print(f"    - Teaching courses: {len(pbas_context.get('teaching', {}).get('courses', []))}")
        print(f"    - Student feedback: {len(pbas_context.get('student_feedback', {}).get('entries', []))}")
        print(f"    - Departmental activities: {len(pbas_context.get('departmental_activities', {}).get('entries', []))}")
        print(f"    - Institute activities: {len(pbas_context.get('institute_activities', {}).get('entries', []))}")
        print(f"    - Society activities: {len(pbas_context.get('society_activities', {}).get('entries', []))}")
        print(f"    - Research entries: {len(pbas_context.get('research', {}).get('entries', []))}")
        print(f"    - ACR Grade: {pbas_context.get('acr', {}).get('grade')}")
        print(f"    - Total score: {pbas_context.get('scores', {}).get('total_score')}")
        
        pbas_pdf = render_to_pdf("pdf/enhanced_pbas.html", pbas_context)
        
        if pbas_pdf.status_code == 200:
            pbas_path = os.path.join(output_dir, f"enhanced_pbas_{appraisal.appraisal_id}.pdf")
            
            with open(pbas_path, 'wb') as f:
                f.write(pbas_pdf.content)
            
            print(f"  ✓ PBAS PDF generated successfully!")
            print(f"    - Saved to: {pbas_path}")
            print(f"    - Size: {len(pbas_pdf.content)} bytes")
        else:
            print(f"  ✗ PBAS PDF generation failed!")
            return False
        
        print("\n" + "=" * 70)
        print("All tests passed! ✓")
        print("=" * 70)
        print("\nGenerated PDFs:")
        print(f"  1. Enhanced SPPU: {sppu_path}")
        print(f"  2. Enhanced PBAS: {pbas_path}")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_pdfs()
    sys.exit(0 if success else 1)
