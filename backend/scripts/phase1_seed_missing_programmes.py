#!/usr/bin/env python
"""Phase 1: Seed 34 missing programmes from cutoff JSON"""
import os
import django
import json
from pathlib import Path
from difflib import SequenceMatcher

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import Programme, Institution, ProgrammeOffering, ProgrammeLevel, ClusterGroup

def fuzzy_match_cluster(programme_name, threshold=0.6):
    """Find best matching cluster for a programme name"""
    best_match = None
    best_score = 0
    
    for cluster in ClusterGroup.objects.filter(level__name='DEGREE').select_related('level'):
        score = SequenceMatcher(None, programme_name.lower(), cluster.name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = cluster
    
    return best_match if best_score >= threshold else None

print("=" * 70)
print("PHASE 1: SEED MISSING PROGRAMMES FROM CUTOFF JSON")
print("=" * 70)

# Load cutoff JSON
cutoff_json = Path(__file__).parent / 'extraction_output' / 'degree_cutoffs_extracted.json'
with open(cutoff_json, 'r', encoding='utf-8') as f:
    cutoff_data = json.load(f)

# Get existing programme codes
existing_codes = set(Programme.objects.values_list('kuccps_code', flat=True))
print(f"\nExisting programmes in database: {len(existing_codes)}")

# Get all codes from cutoff JSON
cutoff_codes = {}
for record in cutoff_data['data']:
    code = record['kuccps_code']
    if code not in cutoff_codes:
        cutoff_codes[code] = record

print(f"Unique programmes in cutoff JSON: {len(cutoff_codes)}")

# Find missing programmes
missing_codes = set(cutoff_codes.keys()) - existing_codes
print(f"Missing programmes to seed: {len(missing_codes)}")

if not missing_codes:
    print("\nNo missing programmes! All cutoff programmes already in database.")
    exit(0)

# Get DEGREE level
degree_level = ProgrammeLevel.objects.get(name='DEGREE')

# Build institution cache
inst_by_name = {inst.name: inst for inst in Institution.objects.all()}
inst_by_code = {inst.code: inst for inst in Institution.objects.all()}

print(f"\nCached {len(inst_by_name)} institutions")

# Prepare programmes and offerings to create
programmes_to_create = []
offerings_to_create = []
stats = {'programmes': 0, 'offerings': 0, 'no_cluster': 0, 'no_institution': 0}

print(f"\nProcessing {len(missing_codes)} missing programmes...")

for i, code in enumerate(sorted(missing_codes), 1):
    record = cutoff_codes[code]
    prog_name = record['programme_name']
    inst_name = record['institution_name']
    inst_code = code[:4]
    
    # Find cluster using fuzzy matching
    cluster = fuzzy_match_cluster(prog_name, threshold=0.4)
    if not cluster:
        stats['no_cluster'] += 1
    
    # Create programme object
    programme = Programme(
        kuccps_code=code,
        name=prog_name,
        level=degree_level,
        cluster=cluster,
        sub_cluster=None  # Don't have subcluster mapping
    )
    programmes_to_create.append(programme)
    
    if i % 10 == 0:
        print(f"  Processed {i}/{len(missing_codes)} programmes...")

# Bulk create programmes
print(f"\nCreating {len(programmes_to_create)} programmes...")
Programme.objects.bulk_create(programmes_to_create, ignore_conflicts=True)
stats['programmes'] = len(programmes_to_create)

# Now create offerings - need to refresh programme cache
print(f"\nBuilding programme cache for offerings...")
prog_cache = {p.kuccps_code: p for p in Programme.objects.filter(kuccps_code__in=missing_codes)}

print(f"Creating offerings for {len(prog_cache)} programmes...")
for code in missing_codes:
    if code not in prog_cache:
        continue
        
    record = cutoff_codes[code]
    inst_name = record['institution_name']
    inst_code = code[:4]
    
    # Find institution
    institution = inst_by_name.get(inst_name) or inst_by_code.get(inst_code)
    
    if not institution:
        stats['no_institution'] += 1
        print(f"  WARNING: No institution found for {code} - {inst_name}")
        continue
    
    # Create offering
    offerings_to_create.append(ProgrammeOffering(
        programme=prog_cache[code],
        institution=institution
    ))

# Bulk create offerings
if offerings_to_create:
    print(f"\nCreating {len(offerings_to_create)} programme offerings...")
    ProgrammeOffering.objects.bulk_create(offerings_to_create, ignore_conflicts=True)
    stats['offerings'] = len(offerings_to_create)

# Summary
print("\n" + "=" * 70)
print("PHASE 1 COMPLETE")
print("=" * 70)
print(f"\nProgrammes created: {stats['programmes']}")
print(f"Offerings created: {stats['offerings']}")
print(f"Programmes without cluster match: {stats['no_cluster']}")
print(f"Programmes without institution: {stats['no_institution']}")

# Final counts
total_progs = Programme.objects.count()
total_offerings = ProgrammeOffering.objects.count()
print(f"\n[FINAL DATABASE STATE]")
print(f"Total Programmes: {total_progs}")
print(f"Total Offerings: {total_offerings}")
