import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import User, Appraisal
from workflow.states import States

def run():
    try:
        user = User.objects.get(username='judy')
        faculty = getattr(user, 'facultyprofile', None) or getattr(user, 'faculty_profile', None)
        if not faculty:
            print("No faculty profile found.")
            return
        
        apps = Appraisal.objects.filter(faculty=faculty)
        print(f"Found {apps.count()} appraisals for {user.username}:")
        for a in apps:
            print(f"ID: {a.appraisal_id}, Status: {a.status}, Year: {a.academic_year}, HOD Appraisal: {a.is_hod_appraisal}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
