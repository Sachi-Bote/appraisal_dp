"""
Test script to verify the comprehensive PDF generation functionality.
This script creates a test appraisal with sample data and generates a PDF.
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
from core.services.pdf.comprehensive_mapper import get_comprehensive_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf
import json

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
            }
        ],
        "departmental_activities": [
            {
                "activity": "NBA Coordinator",
                "semester": "1/2024-25",
                "credits_claimed": 3,
                "enclosure_no": "D1"
            }
        ],
        "institute_activities": [
            {
                "activity": "Institute Website Management",
                "semester": "1/2024-25",
                "credits_claimed": 4,
                "enclosure_no": "I1"
            }
        ],
        "society_activities": [
            {
                "activity": "Blood Donation Activity",
                "semester": "2/2024-25",
                "credits_claimed": 5,
                "enclosure_no": "S1"
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

def test_pdf_generation():
    print("=" * 60)
    print("Testing Comprehensive PDF Generation")
    print("=" * 60)
    
    try:
        # Find or create a test faculty
        print("\n1. Setting up test data...")
        
        # Get or create department
        dept, _ = Department.objects.get_or_create(
            department_name="Computer Engineering"
        )
        
        # Get or create user
        user, _ = User.objects.get_or_create(
            username="test_faculty",
            defaults={
                "role": "FACULTY",
                "full_name": "Dr ABC",
                "designation": "Assistant Professor",
                "department": "Computer Engineering"
            }
        )
        
        # Get or create faculty profile
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
        
        # Create or get test appraisal
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
        
        if created:
            print(f"✓ Created new test appraisal (ID: {appraisal.appraisal_id})")
        else:
            print(f"✓ Using existing appraisal (ID: {appraisal.appraisal_id})")
        
        # Test data mapper
        print("\n2. Testing data mapper...")
        context = get_comprehensive_pdf_data(appraisal)
        print(f"✓ Data mapper executed successfully")
        print(f"  - Faculty: {context.get('faculty', {}).get('name')}")
        print(f"  - Teaching courses: {len(context.get('teaching', {}).get('courses', []))}")
        print(f"  - Research entries: {len(context.get('research', {}).get('entries', []))}")
        print(f"  - Total Score: {context.get('scores', {}).get('total_score')}")
        
        # Test PDF generation
        print("\n3. Generating PDF...")
        pdf_response = render_to_pdf("pdf/comprehensive_appraisal.html", context)
        
        if pdf_response.status_code == 200:
            # Save PDF to file
            output_dir = r"d:\appraisal_dp\appraisal_backend\generated_pdfs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"comprehensive_test_{appraisal.appraisal_id}.pdf")
            
            with open(output_path, 'wb') as f:
                f.write(pdf_response.content)
            
            print(f"✓ PDF generated successfully!")
            print(f"  - Saved to: {output_path}")
            print(f"  - Size: {len(pdf_response.content)} bytes")
        else:
            print(f"✗ PDF generation failed with status code: {pdf_response.status_code}")
            return False
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)
