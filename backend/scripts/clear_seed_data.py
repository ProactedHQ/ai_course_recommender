from students.models import Subject
from universities.models import Institution, ClusterGroup

print("🗑️  Clearing existing seed data...")

# Delete all existing data
subject_count = Subject.objects.count()
institution_count = Institution.objects.count()
cluster_count = ClusterGroup.objects.count()

print(f"\nBefore deletion:")
print(f"  Subjects: {subject_count}")
print(f"  Institutions: {institution_count}")
print(f"  Clusters: {cluster_count}")

Subject.objects.all().delete()
Institution.objects.all().delete()
ClusterGroup.objects.all().delete()

print(f"\n✅ Deleted:")
print(f"  {subject_count} subjects")
print(f"  {institution_count} institutions")
print(f"  {cluster_count} clusters")

print("\n✅ Database cleared successfully!")
