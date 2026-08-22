#!/usr/bin/env python
"""Comprehensive analysis of degree_cutoffs_extracted.json"""
import json
from pathlib import Path
from collections import defaultdict

json_path = Path(__file__).parent / 'extraction_output' / 'degree_cutoffs_extracted.json'

with open(json_path, 'r', encoding='utf-8') as f:
    cutoff_data = json.load(f)

print("=" * 70)
print("CUTOFF DATA ANALYSIS")
print("=" * 70)

total_records = len(cutoff_data.get('data', []))
print(f"\nTotal programme records in JSON: {total_records}")

# Analyze structure
sample_record = cutoff_data['data'][0] if cutoff_data['data'] else {}
print(f"\nSample record structure:")
print(f"  Keys: {list(sample_record.keys())}")
print(f"  KUCCPS Code: {sample_record.get('kuccps_code')}")
print(f"  Programme Name: {sample_record.get('programme_name')}")
print(f"  Institution: {sample_record.get('institution_name')}")
print(f"  Cutoffs keys: {list(sample_record.get('cutoffs', {}).keys()) if 'cutoffs' in sample_record else 'N/A'}")

# Count valid cutoff points
total_valid_cutoffs = 0
total_nan_cutoffs = 0
total_missing_cutoffs = 0
programmes_with_cutoffs = 0
programmes_without_cutoffs = 0
cutoffs_by_year = defaultdict(int)
nan_by_year = defaultdict(int)

for record in cutoff_data['data']:
    cutoffs = record.get('cutoffs', {})
    
    if not cutoffs:
        programmes_without_cutoffs += 1
        continue
    
    has_valid_cutoff = False
    for year, points in cutoffs.items():
        if points is None or points == '' or str(points).upper() == 'NAN':
            total_nan_cutoffs += 1
            nan_by_year[year] += 1
        else:
            try:
                float(points)
                total_valid_cutoffs += 1
                cutoffs_by_year[year] += 1
                has_valid_cutoff = True
            except (ValueError, TypeError):
                total_nan_cutoffs += 1
                nan_by_year[year] += 1
    
    if has_valid_cutoff:
        programmes_with_cutoffs += 1
    else:
        programmes_without_cutoffs += 1

print(f"\n" + "=" * 70)
print("CUTOFF POINTS BREAKDOWN")
print("=" * 70)
print(f"\nProgrammes with at least one valid cutoff: {programmes_with_cutoffs}")
print(f"Programmes with NO valid cutoffs (all NaN): {programmes_without_cutoffs}")
print(f"\nTotal VALID cutoff points: {total_valid_cutoffs}")
print(f"Total NaN/invalid cutoff points: {total_nan_cutoffs}")
print(f"Expected total if all years had data: {total_records * 7} (assuming 7 years)")

print(f"\n" + "=" * 70)
print("CUTOFFS BY YEAR")
print("=" * 70)
for year in sorted(cutoffs_by_year.keys()):
    valid = cutoffs_by_year[year]
    nan = nan_by_year.get(year, 0)
    print(f"  {year}: {valid:4d} valid, {nan:4d} NaN")

# Analyze KUCCPS codes
print(f"\n" + "=" * 70)
print("KUCCPS CODE ANALYSIS")
print("=" * 70)

kuccps_codes = [r.get('kuccps_code') for r in cutoff_data['data']]
unique_codes = set(kuccps_codes)
print(f"Total records: {len(kuccps_codes)}")
print(f"Unique KUCCPS codes: {len(unique_codes)}")
print(f"Duplicate programme entries: {len(kuccps_codes) - len(unique_codes)}")

# Sample some codes
print(f"\nSample KUCCPS codes (first 10):")
for code in list(unique_codes)[:10]:
    print(f"  {code}")

# Check institution codes (first 4 chars)
inst_codes = set(code[:4] for code in kuccps_codes if code)
print(f"\nUnique institution codes: {len(inst_codes)}")

print(f"\n" + "=" * 70)
print("SUMMARY FOR SEEDING")
print("=" * 70)
print(f"Expected cutoff points to seed: {total_valid_cutoffs:,}")
print(f"Currently in database: ~297")
print(f"Missing: ~{total_valid_cutoffs - 297:,}")
