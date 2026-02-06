import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import User, Appraisal
from workflow.states import States

def debug():
    try:
        user = User.objects.get(username='judy')
        faculty = getattr(user, 'facultyprofile', None) or getattr(user, 'faculty_profile', None)
        if not faculty:
            print("Faculty profile for 'judy' not found.")
            return

        appraisal = Appraisal.objects.filter(
            faculty=faculty, 
            status__in=[
                States.DRAFT, 
                States.RETURNED_BY_HOD, 
                States.RETURNED_BY_PRINCIPAL
            ], 
            is_hod_appraisal=False
        ).first()

        if not appraisal:
            print("No matching appraisal found for 'judy'.")
            return

        result = {
            'id': appraisal.appraisal_id,
            'status': appraisal.status,
            'academic_year': appraisal.academic_year,
            'has_appraisal_data': appraisal.appraisal_data is not None,
            'appraisal_data_keys': list(appraisal.appraisal_data.keys()) if appraisal.appraisal_data else []
        }
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug()
