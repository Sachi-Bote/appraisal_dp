"""
Script to inspect actual appraisal data from the database
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal
import json

print("="*70)
print("INSPECTING AP PRAISAL DATA FROM DATABASE")
print("="*70)

# Get the most recent appraisal
appraisals = Appraisal.objects.all().order_by('-created_at')[:5]

if not appraisals:
    print("\nNo appraisals found in database!")
    sys.exit(1)

for i, appraisal in enumerate(appraisals):
    print(f"\n{i+1}. Appraisal ID: {appraisal.appraisal_id}")
    print(f"   Faculty: {appraisal.faculty.full_name}")
    print(f"   Academic Year: {appraisal.academic_year}")
    print(f"   Status: {appraisal.status}")
    
    data = appraisal.appraisal_data or {}
    
    # Check for activities section
    if "activities" in data:
        print(f"\n   Activities section found:")
        print(f"   {json.dumps(data['activities'], indent=6)}")
    else:
        print(f"\n   No 'activities' key in appraisal_data")
        print(f"   Available keys: {list(data.keys())}")

print("\n" + "="*70)
