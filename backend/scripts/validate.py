from students.models import Subject
from universities.models import Institution, ClusterGroup

print("="*70)
print("FINAL DATABASE VALIDATION")
print("="*70)

# Subjects
subjects = Subject.objects.all()
print(f"\nSubjects: {subjects.count()} total")
for cat_code in ['GP1', 'GP2', 'GP3', 'GP4', 'GP5']:
    count = subjects.filter(category=cat_code).count()
    print(f"  {cat_code}: {count}")

print("\nAll Subjects:")
for s in subjects.order_by('code'):
    print(f"  {s.code:5} - {s.name} ({s.category})")

# Institutions
institutions = Institution.objects.all()
print(f"\nInstitutions: {institutions.count()} total")
for inst_type in ['PUBLIC', 'PRIVATE', 'TVET']:
    count = institutions.filter(institution_type=inst_type).count()
    print(f"  {inst_type}: {count}")

# Clusters
clusters = ClusterGroup.objects.all()
print(f"\nClusters: {clusters.count()} total")
for c in clusters.order_by('code'):
    print(f"  {c.code:12} - {c.name}")

print("\n" + "="*70)
