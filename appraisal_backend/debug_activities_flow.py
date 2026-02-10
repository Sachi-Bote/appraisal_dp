"""
Debug script to inspect what's happening with activities data
"""
import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal_backend.settings')
django.setup()

from core.models import Appraisal
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data

print("="*80)
print("ACTIVITIES DATA FLOW DEBUG")
print("="*80)

# Get the most recent appraisal
appraisal = Appraisal.objects.all().order_by('-updated_at').first()

if not appraisal:
    print("No appraisals found!")
    sys.exit(1)

print(f"\nAppraisal ID: {appraisal.appraisal_id}")
print(f"Status: {appraisal.status}")
print(f"Updated: {appraisal.updated_at}")

# Show what's ACTUALLY in the database
raw_data = appraisal.appraisal_data or {}
print(f"\n{'='*80}")
print("STEP 1: RAW DATA FROM DATABASE")
print(f"{'='*80}")
print(f"Top-level keys: {list(raw_data.keys())}")

if "activities" in raw_data:
    print(f"\n'activities' section:")
    print(json.dumps(raw_data["activities"], indent=2))
else:
    print("\nNO 'activities' key found!")

# Now trace through the PDF generation
print(f"\n{'='*80}")
print("STEP 2: GENERATING PDF DATA")
print(f"{'='*80}")

try:
    pdf_data = get_enhanced_sppu_pdf_data(appraisal)
    
    print(f"\nPDF generation completed")
    print(f"Activities checkboxes in PDF:")
    checkboxes = pdf_data.get("table1_activities", {}).get("checkboxes", {})
    for key, value in checkboxes.items():
        print(f"  {key}: {'Yes' if value else 'No'}")
        
except Exception as e:
    print(f"\nERROR during PDF generation: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}\n")
