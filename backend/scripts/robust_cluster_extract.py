import pdfplumber
import re
import os
import json

def extract_clusters_robustly():
    pdf_path = 'KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return

    mapping = [] # List of {cluster_code, programme_name}
    current_cluster = None
    
    # Regex for cluster code (usually 1, 2, 3, or variants like 2A, 2B, 10C)
    # Looking for a standalone number or alphanumeric code at the start of a block
    # or follow words like CLUSTER
    cluster_pattern = re.compile(r'^(CLUSTER\s+)?(\d{1,2}[A-Z]?)(\s+|$)', re.IGNORECASE)
    
    # Regex for programme names
    prog_pattern = re.compile(r'(Bachelor\s+of\s+[^(\n]+(?:\([^)]*\))?)', re.IGNORECASE)

    print(f"Extraction started for {pdf_path}...")
    
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
                # Headers often look like "1" or "2A" or "CLUSTER 1"
                # They are usually on their own line or at the very start
                match = cluster_pattern.match(line)
                if match:
                    # Heuristic: If the line is very short or has specific keywords
                    # Or if it's "CLUSTER X"
                    potential_code = match.group(2)
                    # Exclude things that are just parts of requirements like "1 Subject 1"
                    if "Subject" not in line and len(line) < 100:
                        current_cluster = potential_code
                        # print(f"Active Cluster: {current_cluster} (Page {i+1})")
                
                # Extract programme names
                if current_cluster:
                    # Some lines have multiple programmes
                    progs = prog_pattern.findall(line)
                    for prog in progs:
                        cleaned = prog.strip().replace('\n', ' ')
                        # Remove trailing spaces and commas
                        cleaned = re.sub(r'\s+', ' ', cleaned).rstrip(', ')
                        mapping.append({
                            'name': cleaned,
                            'cluster_code': current_cluster
                        })

    # Save to a new JSON
    output_path = 'extraction_output/degree_clusters_robust.json'
    with open(output_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nRobust Extraction Complete!")
    print(f"Total mappings found: {len(mapping)}")
    
    # Debug: Check some common ones
    found_arts = [m for m in mapping if "ARTS" in m['name'].upper()]
    print(f"Found {len(found_arts)} variations of 'Bachelor of Arts'")
    if found_arts:
        print(f"Sample: {found_arts[0]}")

if __name__ == "__main__":
    extract_clusters_robustly()
