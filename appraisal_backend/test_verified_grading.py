
import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "appraisal_backend.settings")
django.setup()

from rest_framework.test import APIClient
from core.models import User, FacultyProfile, Department, Appraisal, AppraisalScore
from workflow.states import States

def setup_users():
    # 1. Create Department
    dept, _ = Department.objects.get_or_create(department_name="Computer Engineering")

    # 2. HOD User
    hod_user, _ = User.objects.get_or_create(username="hod_test", email="hod@test.com", role="HOD")
    dept.hod = hod_user
    dept.save()

    # 3. Faculty User
    fac_user, _ = User.objects.get_or_create(username="faculty_test", email="fac@test.com", role="FACULTY")
    faculty, _ = FacultyProfile.objects.get_or_create(
        user=fac_user, 
        defaults={"department": dept, "designation": "Assistant Professor"}
    )
    
    # 4. Principal User
    principal_user, _ = User.objects.get_or_create(username="principal_test", email="principal@test.com", role="PRINCIPAL")

    return faculty, hod_user, principal_user

from django.test import override_settings

@override_settings(ALLOWED_HOSTS=['*'])
def test_verified_grading():
    print("--- Starting Verified Grading Test (APIClient) ---")
    faculty, hod_user, principal_user = setup_users()

    # 1. Cleanup and Create Appraisal
    Appraisal.objects.filter(faculty=faculty, academic_year="2024-2025").delete()

    appraisal = Appraisal.objects.create(
        faculty=faculty,
        academic_year="2024-2025",
        status=States.SUBMITTED,
        appraisal_data={"dummy": "data"} 
    )
    print(f"Created Appraisal {appraisal.appraisal_id} in state {appraisal.status}")

    client = APIClient()

    # 2. HOD Starts Review
    client.force_authenticate(user=hod_user)
    response = client.post(
        f"/api/hod/appraisal/{appraisal.appraisal_id}/start-review/",
        format="json",
        HTTP_ACCEPT="application/json"
    )
    
    appraisal.refresh_from_db()
    print(f"HOD Start Review Response: {response.status_code}, State: {appraisal.status}")
    if response.status_code != 200:
        try:
            print(response.data)
        except:
            print(response.content)
    assert appraisal.status == States.REVIEWED_BY_HOD

    # 3. HOD Approves with Verified Grade
    verified_grade = "Outstanding"
    data = {"verified_grade": verified_grade}
    response = client.post(
        f"/api/hod/appraisal/{appraisal.appraisal_id}/approve/",
        data=data,
        format="json",
        HTTP_ACCEPT="application/json"
    )
    
    appraisal.refresh_from_db()
    print(f"HOD Approve Response: {response.status_code}, State: {appraisal.status}")
    if response.status_code != 200:
        try:
            print(response.data)
        except:
            print(response.content)
    assert appraisal.status == States.HOD_APPROVED
    
    # 4. Verify Grade in DB
    score = AppraisalScore.objects.get(appraisal=appraisal)
    print(f"Stored Verified Grade: {score.verified_grade}")
    assert score.verified_grade == verified_grade

    # 5. Check PDF Mapper Data
    from core.services.pdf.enhanced_pbas_mapper import get_enhanced_pbas_pdf_data
    pdf_context = get_enhanced_pbas_pdf_data(appraisal)
    print(f"PDF Context Verified Grade: {pdf_context.get('verified_grade')}")
    assert pdf_context.get("verified_grade") == verified_grade
    
    print("--- Test Passed ---")

if __name__ == "__main__":
    try:
        test_verified_grading()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
