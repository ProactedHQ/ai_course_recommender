#!/usr/bin/env python
"""List all TVET cluster codes in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import ClusterGroup, ProgrammeLevel

# Get programme levels
diploma_level = ProgrammeLevel.objects.get(name='DIPLOMA')
certificate_level = ProgrammeLevel.objects.get(name='CERTIFICATE')
artisan_level = ProgrammeLevel.objects.get(name='ARTISAN')

# Get all TVET clusters
tvet_clusters = ClusterGroup.objects.filter(
    level__in=[diploma_level, certificate_level, artisan_level]
).order_by('code').values('code', 'name', 'level__name')

print("=" * 70)
print(f"ALL TVET CLUSTERS IN DATABASE ({len(tvet_clusters)} total)")
print("=" * 70)

by_level = {}
for cluster in tvet_clusters:
    level = cluster['level__name']
    if level not in by_level:
        by_level[level] = []
    by_level[level].append(cluster)

for level in ['DIPLOMA', 'CERTIFICATE', 'ARTISAN']:
    if level in by_level:
        print(f"\n{level} ({len(by_level[level])} clusters):")
        print("-" * 70)
        for cluster in by_level[level]:
            print(f"  {cluster['code']:30s} | {cluster['name']}")
