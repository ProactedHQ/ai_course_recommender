import pdfplumber
import re
import os
import json

def extract_cluster_prog_mapping():
    pdf_path = 'KUCCPS PROGRAMMES PDF/DEGREE_PROGRAMMES_2025.pdf'
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return

    mapping = {}
    current_cluster = None
    
    # regex for Cluster Header e.g. "CLUSTER 1 - LAW"
    cluster_pattern = re.compile(r'CLUSTER\s+(\d+)\s*[-:]\s*(.*)', re.IGNORECASE)
    # regex for KUCCPS PROG CODE (7 digits)
    code_pattern = re.compile(r'\b\d{7}\b')

    print(f"Opening {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            for line in lines:
                # Check for cluster header
                cluster_match = cluster_pattern.search(line)
                if cluster_match:
                    cluster_code = cluster_match.group(1)
                    cluster_name = cluster_match.group(2).strip()
                    current_cluster = cluster_code
                    print(f"Found Cluster {cluster_code} on page {i+1}")
                
                # Look for programme codes in this line if we have an active cluster
                if current_cluster:
                    codes = code_pattern.findall(line)
                    for code in codes:
                        mapping[code] = current_cluster
            
            if (i+1) % 10 == 0:
                print(f"Processed {i+1}/{total_pages} pages...")

    output_path = 'extraction_output/programme_cluster_map.json'
    with open(output_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nExtraction Complete!")
    print(f"Total mappings found: {len(mapping)}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    extract_cluster_prog_mapping()
