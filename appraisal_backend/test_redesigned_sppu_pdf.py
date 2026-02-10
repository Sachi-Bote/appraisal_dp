"""
Test script for the redesigned SPPU PDF generator.
Generates an enhanced SPPU PDF with official format.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal, FacultyProfile, User, Department
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf
import json


def test_redesigned_sppu_pdf():
    print("\n" + "="*70)
    print("TESTING REDESIGNED SPPU PDF GENERATOR")
    print("="*70 + "\n")
    
    # Load sample appraisal data
    print("1. Setting up test data...")
    
    # Get or create test user and faculty
    dept, _ = Department.objects.get_or_create(
        department_name="Computer Engineering",
        defaults={"hod_email": "hod@test.com"}
    )
    
    user, _ = User.objects.get_or_create(
        username="test_faculty_redesign",
        defaults={
            "email": "test_redesign@example.com",
            "role": "FACULTY",
            "full_name": "Dr. Test Faculty Redesign",
            "designation": "Assistant Professor",
            "department": "Computer Engineering"
        }
    )
    
    faculty, _ = FacultyProfile.objects.get_or_create(
        user=user,
        defaults={
            "department": dept,
            "full_name": "Dr. Test Faculty Redesign",
            "designation": "Assistant Professor",
            "email": "test_redesign@example.com",
            "mobile": "9876543210"
        }
    )
    
    # Load sample payload
    sample_file_path = os.path.join(os.path.dirname(__file__), 'Sample_Payload.json')
    with open(sample_file_path, 'r') as f:
        sample_data = json.load(f)
    
    # Create or update appraisal
    appraisal, created = Appraisal.objects.update_or_create(
        faculty=faculty,
        academic_year="2024-25",
        semester="Both",
        defaults={
            "appraisal_data": sample_data,
            "status": "FINALIZED"
        }
    )
    
    print(f"  ✓ Appraisal ID: {appraisal.appraisal_id}")
    print(f"  ✓ Faculty: {faculty.full_name}")
    print(f"  ✓ Academic Year: {appraisal.academic_year}\n")
    
    # Test the redesigned SPPU mapper
    print("2. Testing Enhanced SPPU Data Mapper...")
    sppu_context = get_enhanced_sppu_pdf_data(appraisal)
    
    # Print mapper output summary
    print(f"  ✓ Faculty Name: {sppu_context['faculty']['name']}")
    print(f"  ✓ Department: {sppu_context['faculty']['department']}")
    print(f"\n  TABLE 1 - Teaching:")
    print(f"    - Total Assigned: {sppu_context['table1_teaching']['total_assigned']}")
    print(f"    - Total Taught: {sppu_context['table1_teaching']['total_taught']}")
    print(f"    - Percentage: {sppu_context['table1_teaching']['percentage']}%")
    print(f"    - Self Grade: {sppu_context['table1_teaching']['self_grade']}")
    
    print(f"\n  TABLE 1 - Activities:")
    print(f"    - Checked Activities: {sppu_context['table1_activities']['count']}")
    print(f"    - Self Grade: {sppu_context['table1_activities']['self_grade']}")
    print(f"    - Checkboxes:")
    for key, value in sppu_context['table1_activities']['checkboxes'].items():
        if value:
            print(f"      ✓ {key}")
    
    print(f"\n  TABLE 2 - Research Scoring:")
    print(f"    - Total Table 2 Score: {sppu_context['table2_total_score']}")
    
    # Show some key research categories
    research_data = sppu_context['table2_research']
    if research_data['peer_reviewed_journals']['count'] > 0:
        print(f"    - Peer-Reviewed Journals: {research_data['peer_reviewed_journals']['count']} (Score: {research_data['peer_reviewed_journals']['total_score']})")
    if research_data['conference_international_abroad']['count'] > 0:
        print(f"    - International Conferences (Abroad): {research_data['conference_international_abroad']['count']} (Score: {research_data['conference_international_abroad']['total_score']})")
    if research_data['books_international']['count'] > 0:
        print(f"    - International Books: {research_data['books_international']['count']} (Score: {research_data['books_international']['total_score']})")
    
    print(f"\n  PART B - Assessment:")
    print(f"    - Overall Grade: {sppu_context['part_b']['overall_grade']}")
    
    # Generate PDF
    print("\n3. Generating PDF...")
    pdf_response = render_to_pdf("pdf/enhanced_sppu.html", sppu_context)
    
    if pdf_response.status_code == 200:
        # Save PDF to file
        output_dir = os.path.join(os.path.dirname(__file__), "generated_pdfs")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"REDESIGNED_SPPU_appraisal_{appraisal.appraisal_id}.pdf")
        
        with open(output_path, "wb") as pdf_file:
            pdf_file.write(pdf_response.content)
        
        file_size_kb = len(pdf_response.content) / 1024
        print(f"  ✓ PDF generated successfully!")
        print(f"  ✓ File size: {file_size_kb:.2f} KB")
        print(f"  ✓ Saved to: {output_path}")
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        print(f"\nYou can now open the PDF at:\n{output_path}\n")
        
        return True
    else:
        print(f"  ✗ PDF generation failed!")
        print(f"  Status code: {pdf_response.status_code}")
        print(f"  Response: {pdf_response.content.decode('utf-8') if pdf_response.content else 'No content'}")
        
        print("\n" + "="*70)
        print("✗ TEST FAILED")
        print("="*70)
        
        return False


if __name__ == "__main__":
    success = test_redesigned_sppu_pdf()
    sys.exit(0 if success else 1)
