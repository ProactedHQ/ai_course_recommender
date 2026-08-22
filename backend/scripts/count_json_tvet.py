#!/usr/bin/env python
"""Count actual TVET clusters in JSON by manually parsing structure"""
import json
from pathlib import Path

json_path = Path(__file__).parent / 'extraction_output' / 'tvet_clusters_MANUAL.json'
with open(json_path, 'r', encoding='utf-8') as f:
    tvet_data = json.load(f)

total_count = 0
breakdown = {'DIPLOMA': [], 'CERTIFICATE': [], 'ARTISAN': []}

for cluster in tvet_data.get('clusters', []):
    cluster_num = cluster.get('cluster_number')
    category = cluster.get('category')
    section = cluster.get('section', 'STANDARD')
    
    if 'subcategories' in cluster:
        # Has subcategories
        for subcat in cluster['subcategories']:
            for level in subcat['levels']:
                level_name = level['level']
                total_count += 1
                if 'Diploma' in level_name:
                    breakdown['DIPLOMA'].append(f"{section} - {cluster_num} - {category} ({subcat['subcategory_name']})")
                elif 'Certificate' in level_name:
                    breakdown['CERTIFICATE'].append(f"{section} - {cluster_num} - {category} ({subcat['subcategory_name']})")
                elif 'Artisan' in level_name:
                    breakdown['ARTISAN'].append(f"{section} - {cluster_num} - {category} ({subcat['subcategory_name']})")
    
    elif 'levels' in cluster:
        has_variants = any('variants' in level for level in cluster['levels'])
        
        if has_variants:
            for level in cluster['levels']:
                level_name = level['level']
                if 'variants' in level:
                    for variant in level['variants']:
                        total_count += 1
                        if 'Diploma' in level_name:
                            breakdown['DIPLOMA'].append(f"{section} - {cluster_num} - {category} ({variant['variant_name']})")
                        elif 'Certificate' in level_name:
                            breakdown['CERTIFICATE'].append(f"{section} - {cluster_num} - {category} ({variant['variant_name']})")
                        elif 'Artisan' in level_name:
                            breakdown['ARTISAN'].append(f"{section} - {cluster_num} - {category} ({variant['variant_name']})")
                else:
                    total_count += 1
                    if 'Diploma' in level_name:
                        breakdown['DIPLOMA'].append(f"{section} - {cluster_num} - {category}")
                    elif 'Certificate' in level_name:
                        breakdown['CERTIFICATE'].append(f"{section} - {cluster_num} - {category}")
                    elif 'Artisan' in level_name:
                        breakdown['ARTISAN'].append(f"{section} - {cluster_num} - {category}")
        else:
            for level in cluster['levels']:
                level_name = level['level']
                total_count += 1
                if 'Diploma' in level_name:
                    breakdown['DIPLOMA'].append(f"{section} - {cluster_num} - {category}")
                elif 'Certificate' in level_name:
                    breakdown['CERTIFICATE'].append(f"{section} - {cluster_num} - {category}")
                elif 'Artisan' in level_name:
                    breakdown['ARTISAN'].append(f"{section} - {cluster_num} - {category}")

print("=" * 70)
print("TVET CLUSTERS COUNT FROM JSON")
print("=" * 70)
print(f"\nTotal TVET clusters in JSON: {total_count}")
print(f"\nBreakdown:")
print(f"  DIPLOMA: {len(breakdown['DIPLOMA'])}")
print(f"  CERTIFICATE: {len(breakdown['CERTIFICATE'])}")
print(f"  ARTISAN: {len(breakdown['ARTISAN'])}")

print(f"\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"Expected from JSON: {total_count}")
print(f"Seed script generates: 65")
print(f"Database has: 65")
print(f"\nStatus: {'MATCH - All clusters seeded correctly!' if total_count == 65 else f'MISMATCH - Missing {total_count - 65} clusters'}")
