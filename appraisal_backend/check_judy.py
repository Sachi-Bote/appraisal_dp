import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import User, Appraisal
from workflow.states import States

def cleanup():
    try:
        user = User.objects.get(username='judy')
        faculty = getattr(user, 'facultyprofile', None) or getattr(user, 'faculty_profile', None)
        if not faculty:
            print("No faculty profile found for judy.")
            return
        
        apps = Appraisal.objects.filter(faculty=faculty).order_by('appraisal_id')
        print(f"--- Appraisals for {user.username} ---")
        
        by_period = {}
        for a in apps:
            print(f"ID: {a.appraisal_id}, Status: {a.status}, Year: {a.academic_year}, Sem: {a.semester}")
            period = (a.academic_year, a.semester, a.form_type)
            if period not in by_period:
                by_period[period] = []
            by_period[period].append(a)
        
        for period, p_apps in by_period.items():
            if len(p_apps) > 1:
                print(f"Duplicate found for period {period}: {[a.appraisal_id for a in p_apps]}")
                # Keep the one that is NOT draft if possible
                candidates = [a for a in p_apps if a.status != States.DRAFT]
                if candidates:
                    keep = candidates[0]
                    for a in p_apps:
                        if a.appraisal_id != keep.appraisal_id:
                            print(f"Deleting duplicate appraisal {a.appraisal_id} (Status: {a.status})")
                            a.delete()
                else:
                    # All are drafts? Keep the latest
                    keep = p_apps[-1]
                    for a in p_apps[:-1]:
                        print(f"Deleting old draft {a.appraisal_id}")
                        a.delete()
        print("--- Cleanup Complete ---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup()
