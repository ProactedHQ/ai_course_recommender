import os
import json
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ClusterGroup, ProgrammeLevel

def update_clusters():
    # Load JSON data
    json_path = 'extraction_output/degree_clusters_robust.json'
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    # Get Degree Level
    degree_level = ProgrammeLevel.objects.get(name='DEGREE')

    # Map ClusterGroup code -> ID
    clusters = {c.code: c for c in ClusterGroup.objects.filter(level=degree_level)}
    print(f"Loaded {len(clusters)} clusters from DB")

    # Build name -> cluster_code map from JSON
    name_to_cluster = {}
    for item in json_data:
        name = item.get('name', '').strip().upper()
        cluster_code = item.get('cluster_code')
        if name:
            name_to_cluster[name] = cluster_code
            
            # Simple normalization: handle "(With IT)" variations
            norm_name = name.replace(' (WITH IT)', ' (WITH IT)').replace('(WITH IT)', ' (WITH IT)')
            name_to_cluster[norm_name] = cluster_code

    print(f"Extracted {len(name_to_cluster)} unique programme names from JSON")

    # Update programmes in DB
    programmes = Programme.objects.filter(level=degree_level)
    print(f"Found {programmes.count()} total degree programmes in DB")

    updated_count = 0
    not_found_count = 0
    already_set_count = 0

    for prog in programmes:
        prog_name_upper = prog.name.strip().upper()
        if prog_name_upper in name_to_cluster:
            cluster_code = name_to_cluster[prog_name_upper]
            cluster = clusters.get(cluster_code)
            
            if cluster:
                if prog.cluster_id != cluster.id:
                    prog.cluster = cluster
                    prog.save()
                    updated_count += 1
                else:
                    already_set_count += 1
            else:
                print(f"Warning: Cluster code {cluster_code} from JSON not found in DB")
        else:
            not_found_count += 1

    print(f"\nUpdate Summary:")
    print(f"  ✨ Programmes updated: {updated_count}")
    print(f"  ⏭️  Already correct: {already_set_count}")
    print(f"  ⚠️  Names not matched in JSON: {not_found_count}")

if __name__ == "__main__":
    update_clusters()
