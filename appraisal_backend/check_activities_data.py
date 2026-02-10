"""
Quick script to inspect what's actually in your appraisals table
Run with: python check_activities_data.py
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal
import json

print("="*80)
print("CHECKING ACTUAL APPRAISAL DATA STRUCTURE")
print("="*80)

# Get most recent appraisal
appraisals = Appraisal.objects.filter(status='FINALIZED').order_by('-created_at')[:3]

if not appraisals.exists():
    print("\nNo finalized appraisals found. Checking any status...")
    appraisals = Appraisal.objects.all().order_by('-created_at')[:3]

if not appraisals.exists():
    print("\nNo appraisals found at all!")
    sys.exit(1)

for i, appr in enumerate(appraisals):
    print(f"\n{'-'*80}")
    print(f"APPRAISAL {i+1}")
    print(f"{'-'*80}")
    print(f"ID: {appr.appraisal_id}")
    print(f"Faculty: {appr.faculty.full_name}")
    print(f"Year: {appr.academic_year}")
    print(f"Status: {appr.status}")
    
    data = appr.appraisal_data or {}
    
    print(f"\nTop-level keys: {list(data.keys())}")
    
    if "activities" in data:
        activities = data["activities"]
        print(f"\n✓ 'activities' key found!")
        print(f"  Type: {type(activities)}")
        print(f"  Content: {json.dumps(activities, indent=4)}")
    else:
        print(f"\n✗ No 'activities' key in top level")
        
    # Check if it's nested elsewhere
    for key in ["step2b", "section_b", "sectionB", "sppu", "pbas"]:
        if key in data and isinstance(data[key], dict):
            if "activities" in data[key]:
                print(f"\n✓ Found 'activities' under '{key}':")
                print(f"  {json.dumps(data[key]['activities'], indent=4)}")

print(f"\n{'='*80}\n")
