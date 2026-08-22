#!/usr/bin/env python
"""Find missing TVET clusters using exact same logic as seed script"""
import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import ClusterGroup, ProgrammeLevel

# Load JSON
json_path = Path(__file__).parent / 'extraction_output' / 'tvet_clusters_MANUAL.json'
with open(json_path, 'r', encoding='utf-8') as f:
    tvet_data = json.load(f)

# Get existing codes from DB
db_codes = set(ClusterGroup.objects.filter(
    level__name__in=['DIPLOMA', 'CERTIFICATE', 'ARTISAN']
).values_list('code', flat=True))

print(f"Database has {len(db_codes)} TVET clusters")

# Generate expected codes using EXACT same logic as seed script
expected_clusters = []

for cluster in tvet_data.get('clusters', []):
    section = cluster.get('section', 'STANDARD')
    cluster_num = cluster.get('cluster_number')
    category = cluster.get('category')
    
    # Determine prefix
    if section == 'KNEC EXAMINATION':
        prefix = 'KNEC'
    elif section == 'INTERNAL EXAMINERS':
        prefix = 'INTERNAL'
    else:
        prefix = 'TVET'
    
    # subcategories vs levels
    if 'subcategories' in cluster:
        for subcat in cluster['subcategories']:
            subcat_name = subcat['subcategory_name']
            for level in subcat['levels']:
                level_name = level['level']
                # Code: prefix-clusternum-subcat-level
                code = f"{prefix}-{cluster_num}-{subcat_name[:3].upper()}-{level_name[:4].upper()}"
                expected_clusters.append({
                    'code': code,
                    'name': f"{category} ({subcat_name}) ({level_name})",
                    'level': level_name,
                    'category': category,
                    'cluster_num': cluster_num,
                    'section': section
                })
    
    elif 'levels' in cluster:
        has_variants =any('variants' in level for level in cluster['levels'])
        
        if has_variants:
            # Create separate cluster for each variant
            for level in cluster['levels']:
                level_name = level['level']
                if 'variants' in level:
                    for variant in level['variants']:
                        variant_name = variant['variant_name']
                        clean_variant = variant_name.replace(' ', '-')
                        # Code: prefix-clusternum-variant
                        code = f"{prefix}-{cluster_num}-{clean_variant[:10].upper()}"
                        expected_clusters.append({
                            'code': code,
                            'name': f"{category} ({level_name}: {variant_name})",
                            'level': level_name,
                            'category': category,
                            'cluster_num': cluster_num,
                            'section': section
                        })
                else:
                    # No variants for this level
                    code = f"{prefix}-{cluster_num}-{level_name[:4].upper()}"
                    expected_clusters.append({
                        'code': code,
                        'name': f"{category} ({level_name})",
                        'level': level_name,
                        'category': category,
                        'cluster_num': cluster_num,
                        'section': section
                    })
        else:
            # Normal case: no variants
            for level in cluster['levels']:
                level_name = level['level']
                # Code: prefix-clusternum-level
                code = f"{prefix}-{cluster_num}-{level_name[:4].upper()}"
                expected_clusters.append({
                    'code': code,
                    'name': f"{category} ({level_name})",
                    'level': level_name,
                    'category': category,
                    'cluster_num': cluster_num,
                    'section': section
                })

expected_codes = {c['code'] for c in expected_clusters}

print(f"Expected {len(expected_codes)} TVET clusters from JSON")
print(f"Missing: {len(expected_codes - db_codes)}")

# Find missing
missing_codes = expected_codes - db_codes
missing_clusters = [c for c in expected_clusters if c['code'] in missing_codes]

if missing_clusters:
    print("\n" + "=" * 70)
    print(f"MISSING CLUSTERS ({len(missing_clusters)})")
    print("=" * 70)
    for i, cluster in enumerate(sorted(missing_clusters, key=lambda x: x['code']), 1):
        print(f"\n{i}. {cluster['code']}")
        print(f"   Name: {cluster['name']}")
        print(f"   Level: {cluster['level']}")
        print(f"   Category: {cluster['category']}")
        print(f"   Section: {cluster['section']}")
    
    # Save for seeding
    output_file = Path(__file__).parent / 'missing_tvet_clusters.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(missing_clusters, f, indent=2)
    print(f"\nSaved to: {output_file}")
else:
    print("\nNo missing clusters!")

# Also check for extra codes
extra_codes = db_codes - expected_codes
if extra_codes:
    print("\n" + "=" * 70)
    print(f"EXTRA CLUSTERS IN DB ({len(extra_codes)})")
    print("=" * 70)
    for code in sorted(extra_codes):
        print(f"  {code}")
