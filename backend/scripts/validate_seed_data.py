#!/usr/bin/env python
"""
Validate seeded data
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from students.models import Subject
from universities.models import Institution, ClusterGroup

print("="*70)
print("DATABASE VALIDATION REPORT")
print("="*70)

# Subjects
subjects = Subject.objects.all()
print(f"\n📚 SUBJECTS: {subjects.count()} total")
print("\nBy Category:")
for cat_code, cat_name in [('GP1', 'Group 1'), ('GP2', 'Group 2'), ('GP3', 'Group 3'), ('GP4', 'Group 4'), ('GP5', 'Group 5')]:
    count = subjects.filter(category=cat_code).count()
    print(f"  {cat_name} ({cat_code}): {count}")

print("\nAll Subjects:")
for s in subjects.order_by('code'):
    print(f"  {s.code} - {s.name} ({s.category})")

# Institutions
institutions = Institution.objects.all()
print(f"\n🏫 INSTITUTIONS: {institutions.count()} total")
print("\nBy Type:")
for inst_type in ['PUBLIC', 'PRIVATE', 'TVET']:
    count = institutions.filter(institution_type=inst_type).count()
    print(f"  {inst_type}: {count}")

# Clusters
clusters = ClusterGroup.objects.all()
print(f"\n📊 CLUSTERS: {clusters.count()} total")
print("\nAll Clusters:")
for c in clusters.order_by('code'):
    print(f"  {c.code} - {c.name}")

print("\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)
