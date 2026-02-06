import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import User, Department, FacultyProfile, Appraisal

print("--- USERS ---")
for u in User.objects.all():
    print(f"User: {u.username}, Role: {u.role}, Dept: {u.department}")

print("\n--- DEPARTMENTS ---")
for d in Department.objects.all():
    print(f"Dept: {d.department_name}, HOD: {d.hod.username if d.hod else 'None'}")

print("\n--- FACULTY PROFILES ---")
for f in FacultyProfile.objects.all():
    print(f"Faculty: {f.user.username}, Dept Object: {f.department.department_name if f.department else 'None'}")

print("\n--- APPRAISALS ---")
for a in Appraisal.objects.all():
    print(f"ID: {a.appraisal_id}, Status: {a.status}, Faculty: {a.faculty.user.username}, Dept: {a.faculty.department.department_name if a.faculty.department else 'None'}")
