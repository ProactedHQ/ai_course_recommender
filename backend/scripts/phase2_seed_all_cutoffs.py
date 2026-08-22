#!/usr/bin/env python
"""Phase 2: Seed all cutoff points from cutoff JSON"""
import os
import django
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import Programme, Institution, ProgrammeOffering, CutOffPoint

print("=" * 70)
print("PHASE 2: SEED ALL CUTOFF POINTS")
print("=" * 70)

# Load cutoff JSON
cutoff_json = Path(__file__).parent / 'extraction_output' / 'degree_cutoffs_extracted.json'
with open(cutoff_json, 'r', encoding='utf-8') as f:
    cutoff_data = json.load(f)

print(f"\nLoaded {len(cutoff_data['data'])} cutoff records from JSON")

# Build offering cache by (kuccps_code, institution_name)
print("\nBuilding offering cache...")
offering_cache = {}
for offering in ProgrammeOffering.objects.select_related('programme', 'institution').all():
    key = (offering.programme.kuccps_code, offering.institution.name)
    offering_cache[key] = offering
    
print(f"Cached {len(offering_cache)} programme offerings")

# Also try by normalized institution names (uppercase, stripped)
print("Building normalized institution name cache...")
offering_cache_normalized = {}
for offering in ProgrammeOffering.objects.select_related('programme', 'institution').all():
    key = (offering.programme.kuccps_code, offering.institution.name.strip().upper())
    offering_cache_normalized[key] = offering

# Collect cutoff points
cutoff_points = []
stats = {
    'total_records': 0,
    'matched_offerings': 0,
    'no_offering': 0,
    'valid_cutoffs': 0,
    'null_cutoffs': 0,
    'invalid_cutoffs': 0
}

unmatched_institutions = set()

print(f"\nProcessing cutoff records...")
for idx, record in enumerate(cutoff_data['data'], 1):
    stats['total_records'] += 1
    
    kuccps_code = record.get('kuccps_code')
    inst_name = record.get('institution_name')
    cutoffs = record.get('cutoffs', {})
    
    # Progress indicator
    if idx % 500 == 0:
        print(f"  Processed {idx}/{len(cutoff_data['data'])} records...")
    
    # Find offering - try exact match first
    key = (kuccps_code, inst_name)
    offering = offering_cache.get(key)
    
    # Try normalized match if exact failed
    if not offering:
        key_normalized = (kuccps_code, inst_name.strip().upper())
        offering = offering_cache_normalized.get(key_normalized)
    
    if not offering:
        stats['no_offering'] += 1
        unmatched_institutions.add((kuccps_code, inst_name))
        continue
    
    stats['matched_offerings'] += 1
    
    # Process each year's cutoff
    for year, points in cutoffs.items():
        try:
            year_int = int(year)
            
            # Check if value is NaN/null - preserve as NULL in database
            if points is None or points == '' or str(points).strip().upper() == 'NAN':
                # Create cutoff with NULL value to show "no data for this year"
                cutoff_points.append(CutOffPoint(
                    offering=offering,
                    year=year_int,
                    weighted_cluster_points=None,  # NULL in database
                    cutoff_type='WEIGHTED_POINTS'
                ))
                stats['null_cutoffs'] += 1
            else:
                # Valid value - convert to Decimal
                try:
                    points_decimal = Decimal(str(points))
                    cutoff_points.append(CutOffPoint(
                        offering=offering,
                        year=year_int,
                        weighted_cluster_points=points_decimal,
                        cutoff_type='WEIGHTED_POINTS'
                    ))
                    stats['valid_cutoffs'] += 1
                except (ValueError, InvalidOperation):
                    # Truly invalid value (not a number at all)
                    stats['invalid_cutoffs'] += 1
                    continue
        except (ValueError, TypeError):
            stats['invalid_cutoffs'] += 1
            continue

print(f"\nProcessing complete!")
print(f"\nStatistics:")
print(f"  Total records processed: {stats['total_records']}")
print(f"  Matched to offerings: {stats['matched_offerings']}")
print(f"  No offering found: {stats['no_offering']}")
print(f"  Valid cutoff points: {stats['valid_cutoffs']}")
print(f"  NULL cutoff points (NaN preserved): {stats['null_cutoffs']}")
print(f"  Invalid/skipped: {stats['invalid_cutoffs']}")
print(f"\nTotal cutoffs to insert: {len(cutoff_points)}")

# Show sample of unmatched
if unmatched_institutions:
    print(f"\nSample unmatched (first 10):")
    for code, inst in sorted(unmatched_institutions)[:10]:
        print(f"  {code} - {inst}")

# Bulk create cutoff points
if cutoff_points:
    print(f"\n" + "=" * 70)
    print("INSERTING CUTOFF POINTS")
    print("=" * 70)
    
    batch_size = 1000
    total_batches = (len(cutoff_points) + batch_size - 1) // batch_size
    
    for i in range(0, len(cutoff_points), batch_size):
        batch = cutoff_points[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        CutOffPoint.objects.bulk_create(batch, ignore_conflicts=True)
        print(f"  Inserted batch {batch_num}/{total_batches} ({len(batch)} cutoffs)")
    
    print(f"\nAll cutoff points inserted!")

# Final verification
print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

final_count = CutOffPoint.objects.count()
print(f"\nTotal cutoff points in database: {final_count:,}")
print(f"Expected: ~{stats['valid_cutoffs'] + stats['null_cutoffs']:,}")

# Check by year
print(f"\nCutoffs by year:")
from django.db.models import Count
cutoffs_by_year = CutOffPoint.objects.values('year').annotate(count=Count('id')).order_by('year')
for item in cutoffs_by_year:
    year_count = item['count']
    null_count = CutOffPoint.objects.filter(year=item['year'], weighted_cluster_points__isnull=True).count()
    valid_count = year_count - null_count
    print(f"  {item['year']}: {year_count:,} total ({valid_count:,} valid, {null_count:,} NULL)")

print("\n" + "=" * 70)
print("PHASE 2 COMPLETE!")
print("=" * 70)
