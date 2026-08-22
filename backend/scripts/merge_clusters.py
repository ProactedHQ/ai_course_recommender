import os
import django
import re

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ClusterGroup, ProgrammeLevel

def merge_clusters():
    print("🚀 Starting Cluster Merger (1-20)...")
    
    # Get Degree Level
    degree_level = ProgrammeLevel.objects.get(name='DEGREE')
    
    # 1. Fetch all ClusterGroups for Degree
    all_groups = ClusterGroup.objects.filter(level=degree_level)
    print(f"Total Degree clusters found: {all_groups.count()}")
    
    # 2. Identify primary clusters (digits only) and sub-clusters
    primary_clusters = {} # code -> object
    sub_clusters = [] # list of objects
    
    for g in all_groups:
        if g.code.isdigit():
            primary_clusters[g.code] = g
        else:
            sub_clusters.append(g)
            
    print(f"Primary Clusters (1-20): {len(primary_clusters)}")
    print(f"Sub-clusters to merge: {len(sub_clusters)}")
    
    # 3. Process sub-clusters
    updated_progs_total = 0
    deleted_groups_count = 0
    
    for sub in sub_clusters:
        # Extract numeric prefix (e.g., '1A' -> '1', '16C' -> '16')
        match = re.match(r'^(\d+)', sub.code)
        if not match:
            print(f"⚠️  Skipping cluster with non-numeric prefix: {sub.code} ({sub.name})")
            continue
            
        parent_code = match.group(1)
        
        # Ensure parent cluster exists
        if parent_code not in primary_clusters:
            # Create primary cluster if it doesn't exist (e.g., if only '1A' existed but not '1')
            parent_name = sub.name # Use the name of the first sub-cluster found
            parent, created = ClusterGroup.objects.get_or_create(
                level=degree_level,
                code=parent_code,
                defaults={'name': parent_name}
            )
            primary_clusters[parent_code] = parent
            if created:
                print(f"✨ Created missing parent cluster: {parent_code} ({parent_name})")
        
        parent = primary_clusters[parent_code]
        
        # Re-parent all programmes from this sub-cluster
        progs_to_update = list(Programme.objects.filter(cluster=sub))
        if progs_to_update:
            for p in progs_to_update:
                p.cluster = parent
            
            Programme.objects.bulk_update(progs_to_update, ['cluster'])
            updated_progs_total += len(progs_to_update)
            # print(f"  📌 Re-parented {len(progs_to_update)} programmes from {sub.code} -> {parent_code}")
        
        # Safe to delete sub-cluster now
        sub.delete()
        deleted_groups_count += 1

    print(f"\n✅ Merger Complete!")
    print(f"  ✨ Programmes re-parented: {updated_progs_total}")
    print(f"  ♻️  Sub-clusters deleted: {deleted_groups_count}")
    print(f"  📦 Final Primary Clusters: {ClusterGroup.objects.filter(level=degree_level).count()}")

if __name__ == "__main__":
    merge_clusters()
