import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ProgrammeLevel

level = ProgrammeLevel.objects.get(name='DEGREE')
null_clusters = Programme.objects.filter(level=level, cluster=None)
print(f"Total Degree Programmes: {Programme.objects.filter(level=level).count()}")
print(f"Programmes with null cluster: {null_clusters.count()}")

print("\nFirst 20 names with null cluster:")
for p in null_clusters[:20]:
    print(f" - {p.name}")

# Check JSON names
json_path = 'extraction_output/degree_clusters_extracted.json'
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f"\nNames in JSON (first 5):")
    progs = data.get('data', {}).get('programmes', [])
    for p in progs[:5]:
        print(f" - {p['name'][:50]}...")
