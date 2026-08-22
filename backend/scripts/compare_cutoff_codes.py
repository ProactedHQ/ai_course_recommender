#!/usr/bin/env python
"""Compare KUCCPS codes in cutoff JSON vs programme database"""
import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import Programme, ProgrammeOffering

# Load cutoff JSON
cutoff_json = Path(__file__).parent / 'extraction_output' / 'degree_cutoffs_extracted.json'
with open(cutoff_json, 'r', encoding='utf-8') as f:
    cutoff_data = json.load(f)

cutoff_codes = set(r['kuccps_code'] for r in cutoff_data['data'])
print(f"Cutoff JSON has {len(cutoff_codes)} unique KUCCPS codes")

# Get programme codes from database
db_prog_codes = set(Programme.objects.values_list('kuccps_code', flat=True))
print(f"Programme database has {len(db_prog_codes)} unique KUCCPS codes")

# Get offering codes (programme + institution)
db_offering_codes = set()
for offering in ProgrammeOffering.objects.select_related('programme').all():
    db_offering_codes.add(offering.programme.kuccps_code)

print(f"Programme Offerings cover {len(db_offering_codes)} unique KUCCPS codes")

# Find mismatches
in_cutoff_not_in_db = cutoff_codes - db_prog_codes
in_db_not_in_cutoff = db_prog_codes - cutoff_codes

print(f"\n" + "=" * 70)
print("MISMATCH ANALYSIS")
print("=" * 70)
print(f"\nCodes in cutoff JSON but NOT in programme database: {len(in_cutoff_not_in_db)}")
print(f"Codes in programme database but NOT in cutoff JSON: {len(in_db_not_in_cutoff)}")

if in_cutoff_not_in_db:
    print(f"\nSample codes in cutoff but not in DB (first 20):")
    for code in sorted(in_cutoff_not_in_db)[:20]:
        # Find the record
        record = next(r for r in cutoff_data['data'] if r['kuccps_code'] == code)
        print(f"  {code} - {record['institution_name']} - {record['programme_name']}")

if in_db_not_in_cutoff:
    print(f"\nSample codes in DB but not in cutoff (first 10):")
    for code in sorted(in_db_not_in_cutoff)[:10]:
        prog = Programme.objects.get(kuccps_code=code)
        print(f"  {code} - {prog.name}")

# Check institution codes
print(f"\n" + "=" * 70)
print("INSTITUTION CODE ANALYSIS")
print("=" * 70)

cutoff_inst_codes = set(code[:4] for code in cutoff_codes)
db_inst_codes = set(code[:4] for code in db_prog_codes)

print(f"\nInstitution codes in cutoff JSON: {len(cutoff_inst_codes)}")
print(f"Institution codes in programme DB: {len(db_inst_codes)}")

inst_in_cutoff_not_db = cutoff_inst_codes - db_inst_codes
inst_in_db_not_cutoff = db_inst_codes - cutoff_inst_codes

if inst_in_cutoff_not_db:
    print(f"\nInstitution codes in cutoff but not in DB: {sorted(inst_in_cutoff_not_db)}")

if inst_in_db_not_cutoff:
    print(f"\nInstitution codes in DB but not in cutoff: {sorted(inst_in_db_not_cutoff)[:10]}")

# Summary
print(f"\n" + "=" * 70)
print("ROOT CAUSE")
print("=" * 70)
print(f"\nThe {len(in_cutoff_not_in_db)} programmes in cutoff JSON but not in database")
print(f"represent the missing cutoff points.")
print(f"\nSolution: We need to either:")
print(f"  1. Use different source files (cutoff uses different programme list)")
print(f"  2. Seed programmes from cutoff JSON that are missing")
print(f"  3. Skip cutoffs for programmes not in our database")
