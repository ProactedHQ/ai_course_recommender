#!/usr/bin/env python
"""Check database seeding status"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from universities.models import *
from students.models import Subject
from django.db.models import Count

print("=" * 70)
print("COMPREHENSIVE DATABASE STATE")
print("=" * 70)

# Foundation Data
print("\n[FOUNDATION DATA]")
subject_count = Subject.objects.count()
level_count = ProgrammeLevel.objects.count()
inst_count = Institution.objects.count()
print(f"Subjects: {subject_count} (Expected: 31)")
print(f"Programme Levels: {level_count} (Expected: 4)")
print(f"Institutions: {inst_count} (Expected: 499)")

# Degree Data
print("\n[DEGREE DATA]")
degree_clusters = ClusterGroup.objects.filter(level__name='DEGREE').count()
subclusters = SubClusterGroup.objects.count()
print(f"Degree Clusters: {degree_clusters} (Expected: 20)")
print(f"Degree Subclusters: {subclusters} (Expected: 62)")

# TVET Data
print("\n[TVET DATA]")
diploma_clusters = ClusterGroup.objects.filter(level__name='DIPLOMA').count()
cert_clusters = ClusterGroup.objects.filter(level__name='CERTIFICATE').count()
artisan_clusters = ClusterGroup.objects.filter(level__name='ARTISAN').count()
total_tvet = diploma_clusters + cert_clusters + artisan_clusters
print(f"TVET Clusters (Diploma): {diploma_clusters}")
print(f"TVET Clusters (Certificate): {cert_clusters}")
print(f"TVET Clusters (Artisan): {artisan_clusters}")
print(f"Total TVET Clusters: {total_tvet} (Expected: 72)")

# Programmes
print("\n[PROGRAMMES]")
prog_count = Programme.objects.count()
offering_count = ProgrammeOffering.objects.count()
cutoff_count = CutOffPoint.objects.count()
print(f"Programmes: {prog_count} (Expected: 2016)")
print(f"Programme Offerings: {offering_count} (Expected: 2489)")
print(f"Cutoff Points: {cutoff_count} (Expected: 17675)")

# Check for duplicates
print("\n" + "=" * 70)
print("DUPLICATE CHECK")
print("=" * 70)

# Subjects
subject_dups = Subject.objects.values('code').annotate(count=Count('code')).filter(count__gt=1)
if subject_dups.exists():
    print(f"\n[SUBJECTS] Found {subject_dups.count()} duplicate codes:")
    for dup in subject_dups[:5]:
        print(f"  - Code '{dup['code']}': {dup['count']} occurrences")
else:
    print("\n[SUBJECTS] No duplicates found [OK]")

# Institutions
inst_dups = Institution.objects.values('code').annotate(count=Count('code')).filter(count__gt=1)
if inst_dups.exists():
    print(f"\n[INSTITUTIONS] Found {inst_dups.count()} duplicate codes:")
    for dup in inst_dups[:5]:
        print(f"  - Code '{dup['code']}': {dup['count']} occurrences")
else:
    print("\n[INSTITUTIONS] No duplicate codes [OK]")

# Institution names (check for duplicates)
inst_name_dups = Institution.objects.values('name').annotate(count=Count('name')).filter(count__gt=1)
if inst_name_dups.exists():
    print(f"\n[INSTITUTIONS] Found {inst_name_dups.count()} duplicate names:")
    for dup in inst_name_dups[:5]:
        print(f"  - Name '{dup['name']}': {dup['count']} occurrences")
else:
    print("\n[INSTITUTIONS] No duplicate names [OK]")

# Programmes
prog_dups = Programme.objects.values('kuccps_code').annotate(count=Count('kuccps_code')).filter(count__gt=1)
if prog_dups.exists():
    print(f"\n[PROGRAMMES] Found {prog_dups.count()} duplicate KUCCPS codes:")
    for dup in prog_dups[:5]:
        print(f"  - Code '{dup['kuccps_code']}': {dup['count']} occurrences")
else:
    print("\n[PROGRAMMES] No duplicate KUCCPS codes [OK]")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
total_seeded = subject_count + level_count + inst_count + degree_clusters + subclusters + total_tvet + prog_count + offering_count + cutoff_count
total_expected = 31 + 4 + 499 + 20 + 62 + 72 + 2016 + 2489 + 17675
completion = (total_seeded / total_expected * 100) if total_expected > 0 else 0

print(f"\nTotal Records Seeded: {total_seeded:,}")
print(f"Total Records Expected: {total_expected:,}")
print(f"Completion: {completion:.1f}%")

# What's missing
print("\n[MISSING DATA]")
if prog_count == 0:
    print("- All Programmes (0/2016)")
    print("- All Programme Offerings (0/2489)")
    print("- All Cutoff Points (0/17675)")
elif prog_count < 2016:
    print(f"- {2016 - prog_count} Programmes")
if offering_count < 2489:
    print(f"- {2489 - offering_count} Programme Offerings")
if cutoff_count == 0:
    print("- All Cutoff Points (0/17675)")
