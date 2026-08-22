import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ProgrammeLevel

level = ProgrammeLevel.objects.get(name='DEGREE')
unmatched = Programme.objects.filter(level=level, cluster=None)
print(f"Unmatched Degree Programmes: {unmatched.count()}")

print("\nSample of unmatched names:")
for p in unmatched[:20]:
    print(f" - {p.name}")

# Check mappings for partial matches
with open('extraction_output/degree_clusters_robust.json', 'r') as f:
    mappings = json.load(f)

json_names = {m['name'].upper() for m in mappings}
print(f"\nUnique names in JSON: {len(json_names)}")

print("\nChecking for 'BACHELOR OF ARTS' in JSON...")
matches = [n for n in json_names if "BACHELOR OF ARTS" in n]
print(f"Found {len(matches)} JSON names containing 'BACHELOR OF ARTS':")
for m in matches[:5]:
    print(f" - {m}")
