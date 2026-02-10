import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal, FacultyProfile, Department, User

def check_hod_visibility():
    print("Checking HOD Visibility Logic...\n")

    # 1. Get the most recent non-HOD appraisal
    appraisal = Appraisal.objects.filter(is_hod_appraisal=False).order_by('-updated_at').first()

    if not appraisal:
        print("❌ No faculty appraisals found.")
        return

    print(f"📄 Latest Appraisal ID: {appraisal.appraisal_id}")
    print(f"   Faculty: {appraisal.faculty.full_name} ({appraisal.faculty.user.email})")
    print(f"   Status: {appraisal.status}")
    print(f"   Academic Year: {appraisal.academic_year}")

    # 2. Check Faculty's Department
    department = appraisal.faculty.department
    if not department:
        print("❌ Faculty is NOT assigned to any department!")
        return

    print(f"   Department: {department.department_name}")

    # 3. Check Department HOD
    hod = department.hod
    if not hod:
        print("❌ Department has NO HOD assigned!")
    else:
        print(f"   assigned HOD: {hod.username} ({hod.email})")

    # 4. Check if HOD can see this appraisal
    # Logic from HODAppraisalList.get
    try:
        if hod:
            # Simulate HOD query
            user_department = Department.objects.get(hod=hod)
            print(f"   HOD '{hod.username}' manages department: {user_department.department_name}")

            if user_department != department:
                print("❌ Mismatch: HOD manages a different department than the faculty's department.")
            
            # Check query filter
            visible = Appraisal.objects.filter(
                faculty__department=department,
                is_hod_appraisal=False,
                status__in=["SUBMITTED", "REVIEWED_BY_HOD", "HOD_APPROVED", "REVIEWED_BY_PRINCIPAL", "PRINCIPAL_APPROVED", "FINALIZED"]
            ).filter(pk=appraisal.pk).exists()

            if visible:
                print("✅ Appraisal SHOULD be visible to HOD.")
            else:
                print("❌ Appraisal is NOT picked up by the query.")
                if appraisal.status not in ["SUBMITTED", "REVIEWED_BY_HOD", "HOD_APPROVED", "REVIEWED_BY_PRINCIPAL", "PRINCIPAL_APPROVED", "FINALIZED"]:
                    print(f"      Reason: Status '{appraisal.status}' is not in the allowed list.")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    check_hod_visibility()
