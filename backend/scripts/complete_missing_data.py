#!/usr/bin/env python
"""Complete missing programme offerings and cutoff points"""
import os
import django
import json
from pathlib import Path
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import Programme, Institution, ProgrammeOffering, CutOffPoint

print("=" * 70)
print("COMPLETING MISSING DATA - OFFERINGS & CUTOFFS")
print("=" * 70)

# Load degree_programmes_full.json for offerings
json_path = Path(__file__).parent / 'extraction_output' / 'degree_programmes_full.json'

if not json_path.exists():
    print(f"ERROR: {json_path} not found")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    prog_data = json.load(f)

print(f"\nLoaded {len(prog_data['data'])} programme records")

# Build caches
print("\nBuilding institution cache...")
inst_cache_by_code = {inst.code: inst for inst in Institution.objects.all()}
inst_cache_by_name = {inst.name: inst for inst in Institution.objects.all()}

print(f"Cached {len(inst_cache_by_code)} institutions")

print("\nBuilding programme cache...")
prog_cache = {prog.kuccps_code: prog for prog in Programme.objects.all()}
print(f"Cached {len(prog_cache)} programmes")

# Get existing offerings to avoid duplicates
print("\nChecking existing offerings...")
existing_offerings = set(
    ProgrammeOffering.objects.values_list('programme_id', 'institution_id')
)
print(f"Found {len(existing_offerings)} existing offerings")

# Collect new offerings
new_offerings = []
for record in prog_data['data']:
    kuccps_code = record.get('kuccps_code')
    inst_name = record.get('institution_name')
    inst_code = kuccps_code[:4]
    
    programme = prog_cache.get(kuccps_code)
    institution = inst_cache_by_name.get(inst_name) or inst_cache_by_code.get(inst_code)
    
    if programme and institution:
        # Check if offering already exists
        if (programme.id, institution.id) not in existing_offerings:
            new_offerings.append(ProgrammeOffering(
                programme=programme,
                institution=institution
            ))

print(f"\nCreating {len(new_offerings)} new programme offerings...")
ProgrammeOffering.objects.bulk_create(new_offerings, batch_size=500, ignore_conflicts=True)
print("Programme offerings completed!")

# Now cutoff points
print("\n" + "=" * 70)
print("SEEDING CUTOFF POINTS")
print("=" * 70)

cutoff_json = Path(__file__).parent / 'extraction_output' / 'degree_cutoffs_extracted.json'

if not cutoff_json.exists():
    print(f"ERROR: {cutoff_json} not found")
    exit(1)

with open(cutoff_json, 'r', encoding='utf-8') as f:
    cutoff_data = json.load(f)

print(f"\nLoaded {len(cutoff_data['data'])} cutoff records")

# Build offering cache
print("\nBuilding programme offering cache...")
offering_cache = {}
for offering in ProgrammeOffering.objects.select_related('programme', 'institution').all():
    key = (offering.programme.kuccps_code, offering.institution.code)
    offering_cache[key] = offering

print(f"Cached {len(offering_cache)} programme offerings")

# Collect cutoff points
cutoff_points = []
processed = 0
skipped = 0

for record in cutoff_data['data']:
    kuccps_code = record.get('kuccps_code')
    inst_code = kuccps_code[:4]
    cutoffs = record.get('cutoffs', {})
    
    # Find offering
    offering = offering_cache.get((kuccps_code, inst_code))
    
    if not offering:
        skipped += 1
        continue
    
    # Create cutoffs for each year
    for year, points in cutoffs.items():
        try:
            # Skip if points is None, NaN, or invalid
            if points is None or points == '' or str(points).upper() == 'NAN':
                continue
                
            year_int = int(year)
            points_decimal = Decimal(str(points))
            
            cutoff_points.append(CutOffPoint(
                offering=offering,
                year=year_int,
                weighted_cluster_points=points_decimal,
                cutoff_type='WEIGHTED_POINTS'
            ))
        except (ValueError, TypeError, Exception):
            continue
    
    processed += 1
    if processed % 500 == 0:
        print(f"   Processed {processed}/{len(cutoff_data['data'])} records...")

print(f"\nCreating {len(cutoff_points)} cutoff points...")
print(f"Skipped {skipped} records (no matching offering)")

# Use batches for large insert
batch_size = 1000
for i in range(0, len(cutoff_points), batch_size):
    batch = cutoff_points[i:i+batch_size]
    CutOffPoint.objects.bulk_create(batch, ignore_conflicts=True)
    print(f"   Created batch {i//batch_size + 1}/{(len(cutoff_points) + batch_size - 1)//batch_size}")

print("\n" + "=" * 70)
print("COMPLETION SUCCESSFUL!")
print("=" * 70)

# Final counts
print(f"\nFinal Counts:")
print(f"Programme Offerings: {ProgrammeOffering.objects.count()}")
print(f"Cutoff Points: {CutOffPoint.objects.count()}")
