import os
import django
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import ClusterGroup, Programme

def inspect():
    groups = ClusterGroup.objects.all().order_by('code')
    print(f"Total ClusterGroups: {groups.count()}")
    
    parents = {}
    subs = []
    
    for g in groups:
        if g.code.isdigit():
            parents[g.code] = g
        else:
            subs.append(g)
            
    print(f"Primary Clusters Found: {len(parents)}")
    print(f"Sub-clusters Found: {len(subs)}")
    
    print("\nSample Sub-clusters and their Programme Counts:")
    for s in subs[:10]:
        count = Programme.objects.filter(cluster=s).count()
        print(f" - {s.code}: {s.name} ({count} progs)")

if __name__ == "__main__":
    inspect()
