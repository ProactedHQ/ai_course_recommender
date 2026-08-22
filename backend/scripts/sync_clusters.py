import pdfplumber
import re
import os
import json
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ClusterGroup, ProgrammeLevel

def sync_clusters_and_programmes():
    pdf_path = 'KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return

    # 1. Robust Extraction
    clusters_info = {} # code -> name
    programme_mappings = [] # {name, cluster_code}
    
    current_cluster = None
    
    # Improved regex for cluster headers
    # Matches patterns like "1", "2A", "CLUSTER 3", "20"
    # and tries to capture the name that usually follows nearby
    cluster_pattern = re.compile(r'^(CLUSTER\s+)?(\d{1,2}[A-Z]?)(\s+|$)', re.IGNORECASE)
    prog_pattern = re.compile(r'(Bachelor\s+of\s+[^(\n]+(?:\([^)]*\))?)', re.IGNORECASE)

    print(f"Syncing data from {pdf_path}...")
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for cluster header
                match = cluster_pattern.match(line)
                if match:
                    # Ignore lines that look like "1 Subject 1"
                    if "Subject" not in line and len(line) < 150:
                        code = match.group(2)
                        # Try to get name from the rest of the line
                        name = line.replace(match.group(0), '').strip()
                        if not name:
                            name = f"Cluster {code}" # Fallback
                        
                        current_cluster = code
                        if code not in clusters_info or len(name) > len(clusters_info[code]):
                            clusters_info[code] = name
                
                # Extract programme names
                if current_cluster:
                    progs = prog_pattern.findall(line)
                    for prog in progs:
                        cleaned = prog.strip().replace('\n', ' ')
                        cleaned = re.sub(r'\s+', ' ', cleaned).rstrip(', ')
                        programme_mappings.append({
                            'name': cleaned.upper(),
                            'cluster_code': current_cluster
                        })

    # 2. Database Sync
    degree_level = ProgrammeLevel.objects.get(name='DEGREE')
    
    # Create missing clusters
    print(f"\nSyncing {len(clusters_info)} cluster definitions...")
    for code, name in clusters_info.items():
        ClusterGroup.objects.get_or_create(
            level=degree_level,
            code=code,
            defaults={'name': name}
        )
    
    # Build maps for speed
    db_clusters = {c.code: c for c in ClusterGroup.objects.filter(level=degree_level)}
    name_to_cluster_code = {p['name']: p['cluster_code'] for p in programme_mappings}
    
    # Update programmes
    print(f"Updating programmes...")
    programmes = Programme.objects.filter(level=degree_level)
    updated_progs = []
    updated_count = 0
    already_correct = 0
    unmatched = 0
    
    for prog in programmes:
        name = prog.name.strip().upper()
        if name in name_to_cluster_code:
            code = name_to_cluster_code[name]
            cluster = db_clusters.get(code)
            if cluster:
                if prog.cluster_id != cluster.id:
                    prog.cluster = cluster
                    updated_progs.append(prog)
                    updated_count += 1
                else:
                    already_correct += 1
            else:
                unmatched += 1
        else:
            unmatched += 1

    # Bulk Update
    if updated_progs:
        print(f"Applying bulk update to {len(updated_progs)} records...")
        Programme.objects.bulk_update(updated_progs, ['cluster'])

    print(f"\nSync Complete!")
    print(f"  ✨ Clusters in DB: {len(db_clusters)}")
    print(f"  ✨ Programmes updated: {updated_count}")
    print(f"  ⏭️  Already correct/assigned: {already_correct}")
    print(f"  ⚠️  Unmatched programmes: {unmatched}")

if __name__ == "__main__":
    sync_clusters_and_programmes()
