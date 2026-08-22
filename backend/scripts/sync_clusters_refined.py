import pdfplumber
import re
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ClusterGroup, ProgrammeLevel

def sync_clusters_refined():
    pdf_path = 'KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return

    # 1. Improved Extraction
    clusters_info = {} # code -> name
    programme_mappings = [] # {name_upper, cluster_code}
    
    current_cluster = None
    
    # Regex for cluster headers
    cluster_pattern = re.compile(r'^(CLUSTER\s+)?(\d{1,2}[A-Z]?)(\s+|$)', re.IGNORECASE)
    # Split keywords
    split_pattern = re.compile(r'(?=(?:Bachelor|Diploma|Certificate|Artisan))')

    print(f"Refined Sync stating for {pdf_path}...")
    
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
                    if "Subject" not in line and len(line) < 150:
                        code = match.group(2)
                        name = line.replace(match.group(0), '').strip()
                        current_cluster = code
                        if code not in clusters_info or len(name) > len(clusters_info[code]):
                            clusters_info[code] = name or f"Cluster {code}"
                
                # Extract programme names by splitting the line
                if current_cluster:
                    parts = split_pattern.split(line)
                    for part in parts:
                        cleaned = part.strip()
                        # Basic validation: must start with Bachelor/Diploma and be long enough
                        if (cleaned.lower().startswith('bachelor') or cleaned.lower().startswith('diploma')) and len(cleaned) > 10:
                            # Cleanup name
                            cleaned = cleaned.replace('\n', ' ')
                            cleaned = re.sub(r'\s+', ' ', cleaned).rstrip(', /')
                            programme_mappings.append({
                                'name': cleaned.upper(),
                                'cluster_code': current_cluster
                            })

    # 2. Database Sync with Fuzzy/Flexible matching
    degree_level = ProgrammeLevel.objects.get(name='DEGREE')
    
    print(f"\nExtracted {len(clusters_info)} clusters and {len(programme_mappings)} mappings.")
    
    # Create/Update clusters
    for code, name in clusters_info.items():
        ClusterGroup.objects.get_or_create(level=degree_level, code=code, defaults={'name': name})
    
    db_clusters = {c.code: c for c in ClusterGroup.objects.filter(level=degree_level)}
    
    # Mapping optimization
    name_to_cluster = {p['name']: p['cluster_code'] for p in programme_mappings}
    
    # Update programmes
    print(f"Updating programmes in DB...")
    programmes = Programme.objects.filter(level=degree_level)
    updated_progs = []
    updated_count = 0
    already_correct = 0
    unmatched = 0
    
    # For reporting unmatched
    unmatched_names = set()

    for prog in programmes:
        name = prog.name.strip().upper()
        
        # Normalize name for matching
        def get_matches(n):
            variants = [n]
            # BA -> BACHELOR OF ARTS
            v = n.replace('BA ', 'BACHELOR OF ARTS ').replace('BA IN ', 'BACHELOR OF ARTS IN ')
            variants.append(v)
            # BSC -> BACHELOR OF SCIENCE
            v = n.replace('BSC ', 'BACHELOR OF SCIENCE ').replace('BSC. ', 'BACHELOR OF SCIENCE ')
            variants.append(v)
            # B.ED -> BACHELOR OF EDUCATION
            v = n.replace('B.ED ', 'BACHELOR OF EDUCATION ').replace('BED ', 'BACHELOR OF EDUCATION ')
            variants.append(v)
            # BACHELOR IN -> BACHELOR OF
            v = n.replace('BACHELOR IN ', 'BACHELOR OF ')
            variants.append(v)
            return list(set(variants))

        cluster_code = None
        for variant in get_matches(name):
            cluster_code = name_to_cluster.get(variant)
            if not cluster_code:
                # Try IN/OF flip on each variant
                cluster_code = name_to_cluster.get(variant.replace(' IN ', ' OF '))
            if not cluster_code:
                cluster_code = name_to_cluster.get(variant.replace(' OF ', ' IN '))
            if cluster_code: break
            
        # 3. Try partial matches if slash present
        if not cluster_code and '/' in name:
            for part in name.split('/'):
                cluster_code = name_to_cluster.get(part.strip())
                if cluster_code: break

        if cluster_code:
            cluster = db_clusters.get(cluster_code)
            if cluster:
                if prog.cluster_id != cluster.id:
                    prog.cluster = cluster
                    updated_progs.append(prog)
                    updated_count += 1
                else:
                    already_correct += 1
                continue

        unmatched += 1
        unmatched_names.add(name)

    # Bulk Update
    if updated_progs:
        print(f"Applying bulk update for {len(updated_progs)} records...")
        Programme.objects.bulk_update(updated_progs, ['cluster'])

    print(f"\nFinal Result:")
    print(f"  ✨ Clusters: {len(db_clusters)}")
    print(f"  ✨ Programmes updated: {updated_count}")
    print(f"  ⏭️  Already assigned: {already_correct}")
    print(f"  ⚠️  Unmatched: {unmatched}")
    
    if unmatched > 0:
        print("\nTop 5 Unmatched Names:")
        for n in sorted(list(unmatched_names))[:5]:
            print(f" - {n}")

if __name__ == "__main__":
    sync_clusters_refined()
