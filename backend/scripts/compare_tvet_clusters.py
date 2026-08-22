#!/usr/bin/env python
"""Compare TVET clusters in database vs JSON file to find missing ones"""
import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import ClusterGroup, ProgrammeLevel

print("=" * 70)
print("TVET CLUSTER COMPARISON - DATABASE VS JSON")
print("=" * 70)

# Load JSON file
json_path = Path(__file__).parent / 'extraction_output' / 'tvet_clusters_MANUAL.json'

if not json_path.exists():
    print(f"ERROR: {json_path} not found")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    tvet_data = json.load(f)

print(f"\nLoaded TVET data from JSON: {len(tvet_data['clusters'])} clusters")

# Get programme levels
try:
    diploma_level = ProgrammeLevel.objects.get(name='DIPLOMA')
    certificate_level = ProgrammeLevel.objects.get(name='CERTIFICATE')
    artisan_level = ProgrammeLevel.objects.get(name='ARTISAN')
except ProgrammeLevel.DoesNotExist as e:
    print(f"ERROR: {e}")
    exit(1)

# Get existing TVET clusters from DB
db_clusters = ClusterGroup.objects.filter(
    level__in=[diploma_level, certificate_level, artisan_level]
).values_list('code', 'name', 'level__name')

db_cluster_codes = {code for code, name, level in db_clusters}

print(f"\nTVET Clusters in Database: {len(db_cluster_codes)}")
print(f"Expected from JSON: Need to calculate...")

# Parse JSON to generate expected cluster codes
# Using same logic as seed_complete_data.py
expected_clusters = []

for cluster in tvet_data.get('clusters', []):
    section = cluster.get('section', 'STANDARD')
    cluster_num = cluster.get('cluster_number')
    category = cluster.get('category')
    
    # Determine prefix based on section
    if section == 'KNEC EXAMINATION':
        prefix = 'KNEC'
    elif section == 'INTERNAL EXAMINERS':
        prefix = 'INTERNAL'
    else:
        prefix = 'TVET'
    
    # Handle subcategories vs levels
    if 'subcategories' in cluster:
        # Has subcategories (e.g., Architecture)
        for subcat in cluster['subcategories']:
            subcat_name = subcat['subcategory_name']
            for level in subcat['levels']:
                level_name = level['level']
                code = f"{prefix}-{cluster_num}-{subcat_name[:3].upper()}-{level_name[:4].upper()}"
                expected_clusters.append({
                    'code': code,
                    'name': f"{category} ({subcat_name}) ({level_name})",
                    'level': level_name,
                    'section': section,
                    'cluster_num': cluster_num
                })
    elif 'levels' in cluster:
        # Check for variants within levels
        has_variants = any('variants' in level for level in cluster['levels'])
        
        if has_variants:
            # Create separate cluster for each variant
            for level in cluster['levels']:
                if 'variants' in level:
                    for variant in level['variants']:
                        variant_name = variant['variant_name']
                        clean_variant = variant_name.replace(' ', '-')
                        code = f"{prefix}-{cluster_num}-{clean_variant[:10].upper()}"
                        expected_clusters.append({
                            'code': code,
                            'name': f"{category} ({level['level']}: {variant_name})",
                            'level': level['level'],
                            'section': section,
                            'cluster_num': cluster_num
                        })
                else:
                    # No variants, create normally
                    code = f"{prefix}-{cluster_num}-{level['level'][:4].upper()}"
                    expected_clusters.append({
                        'code': code,
                        'name': f"{category} ({level['level']})",
                        'level': level['level'],
                        'section': section,
                        'cluster_num': cluster_num
                    })
        else:
            # No variants, create normally
            for level in cluster['levels']:
                code = f"{prefix}-{cluster_num}-{level['level'][:4].upper()}"
                expected_clusters.append({
                    'code': code,
                    'name': f"{category} ({level['level']})",
                    'level': level['level'],
                    'section': section,
                    'cluster_num': cluster_num
                })

print(f"\nExpected clusters from JSON: {len(expected_clusters)}")
print(f"Clusters in database: {len(db_cluster_codes)}")
print(f"Missing clusters: {len(expected_clusters) - len(db_cluster_codes)}")

# Find missing clusters
expected_codes = {c['code'] for c in expected_clusters}
missing_codes = expected_codes - db_cluster_codes
extra_codes = db_cluster_codes - expected_codes

print("\n" + "=" * 70)
print("MISSING CLUSTERS (in JSON but not in DB)")
print("=" * 70)

missing_clusters = [c for c in expected_clusters if c['code'] in missing_codes]

if missing_clusters:
    for i, cluster in enumerate(missing_clusters, 1):
        print(f"\n{i}. Code: {cluster['code']}")
        print(f"   Name: {cluster['name']}")
        print(f"   Level: {cluster['level']}")
        print(f"   Section: {cluster['section']}")
else:
    print("No missing clusters found!")

if extra_codes:
    print("\n" + "=" * 70)
    print("EXTRA CLUSTERS (in DB but not in expected list)")
    print("=" * 70)
    for code in sorted(extra_codes):
        print(f"  - {code}")

# Save missing clusters for seeding
if missing_clusters:
    print("\n" + "=" * 70)
    print("SAVING MISSING CLUSTERS TO FILE")
    print("=" * 70)
    
    output_file = Path(__file__).parent / 'missing_tvet_clusters.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(missing_clusters, f, indent=2)
    
    print(f"Saved {len(missing_clusters)} missing clusters to: {output_file}")
