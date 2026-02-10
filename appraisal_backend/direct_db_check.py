"""
Direct SQLite query to check activities data - no Django needed
"""
import sqlite3
import json

db_path = "db.sqlite3"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("CHECKING APPRAISAL DATA IN DATABASE")
print("="*80)

# Get latest appraisals
cursor.execute("""
    SELECT appraisal_id, academic_year, semester, status, appraisal_data
    FROM core_appraisal
    ORDER BY created_at DESC
    LIMIT 3
""")

rows = cursor.fetchall()

if not rows:
    print("\nNo appraisals found!")
    conn.close()
    exit(1)

for i, row in enumerate(rows):
    appr_id, year, semester, status, data_json = row
    
    print(f"\n{'-'*80}")
    print(f"APPRAISAL {i+1}")
    print(f"{'-'*80}")
    print(f"ID: {appr_id}")
    print(f"Year: {year}")
    print(f"Semester: {semester}")
    print(f"Status: {status}")
    
    if data_json:
        data = json.loads(data_json)
        print(f"\nTop-level keys: {list(data.keys())}")
        
        # Check for activities
        if "activities" in data:
            print(f"\n✓ 'activities' found at top level!")
            print(f"  Type: {type(data['activities'])}")
            print(f"  Keys: {list(data['activities'].keys()) if isinstance(data['activities'], dict) else 'N/A'}")
            print(f"\n  FULL CONTENT:")
            print(f"  {json.dumps(data['activities'], indent=4)}")
        else:
            print(f"\n✗ No 'activities' at top level")
            
        # Check nested locations
        for key in ["step2b", "section_b", "sectionB", "sppu", "pbas"]:
            if key in data and isinstance(data[key], dict):
                if "activities" in data[key]:
                    print(f"\n✓ Found 'activities' under '{key}':")
                    print(f"  {json.dumps(data[key]['activities'], indent=4)}")
    else:
        print("\n  No data stored yet")

conn.close()
print(f"\n{'='*80}\n")
