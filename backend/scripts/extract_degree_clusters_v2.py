"""
Extract Degree Cluster Data with Subcluster Support

Extracts cluster, subcluster, and subject requirement data from 
DEGREE_CLUSTER_DOCUMENT_2025_03.pdf to JSON format for manual verification.

Output JSON structure:
{
  "clusters": [
    {
      "code": "7",
      "name": "Computing Sciences",
      "subject_1": "ENG C+",
      "subject_2": "MAT ALT A - C+",
      "subject_3": "PHY - C+",
      "subject_4": "Any GROUP III - C",
      "subclusters": [
        {
          "code": "7A",
          "subject_1": "ENG C+",
          "subject_2": "MAT A - B",
          "subject_3": "PHY - C+",
          "subject_4": "GEO - C",
          "programmes": [...]
        }
      ]
    }
  ]
}

Usage:
    python scripts/extract_degree_clusters_v2.py
    python scripts/extract_degree_clusters_v2.py --pages 1-3
    python scripts/extract_degree_clusters_v2.py --output custom_output.json
"""

import pdfplumber
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SubCluster:
    """Represents a sub-cluster with its requirements and programmes"""
    code: str
    subject_1: Optional[str] = None
    subject_2: Optional[str] = None
    subject_3: Optional[str] = None
    subject_4: Optional[str] = None
    programmes: List[str] = None
    
    def __post_init__(self):
        if self.programmes is None:
            self.programmes = []


@dataclass
class Cluster:
    """Represents a cluster with optional general requirements"""
    code: str
    name: str
    subject_1: Optional[str] = None
    subject_2: Optional[str] = None
    subject_3: Optional[str] = None
    subject_4: Optional[str] = None
    subclusters: List[SubCluster] = None
    
    def __post_init__(self):
        if self.subclusters is None:
            self.subclusters = []


class DegreeClusterExtractor:
    """Extract cluster/subcluster data from DEGREE_CLUSTER_DOCUMENT_2025_03.pdf"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.clusters: List[Cluster] = []
        
        # Regex patterns
        self.cluster_pattern = re.compile(r'^(\d{1,2})\s*[.\-:]?\s*(.+)?$')
        self.subcluster_pattern = re.compile(r'^(\d{1,2}[A-Z])\b')
        self.programme_pattern = re.compile(r'Bachelor\s+of\s+[^(]+(?:\([^)]*\))?', re.IGNORECASE)
        
    def extract(self, page_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract cluster data from PDF
        
        Args:
            page_range: Optional page range like "1-5" or "all"
        
        Returns:
            Dictionary with extracted cluster data
        """
        print(f"Opening PDF: {self.pdf_path}")
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")
            
            # Determine pages to process
            if page_range and page_range != "all":
                start, end = map(int, page_range.split('-'))
                pages_to_process = pdf.pages[start-1:end]
            else:
                pages_to_process = pdf.pages
            
            for page_num, page in enumerate(pages_to_process, 1):
                print(f"\nProcessing page {page_num}...")
                self._process_page(page, page_num)
        
        print(f"\nExtraction complete!")
        print(f"   Clusters found: {len(self.clusters)}")
        
        return self._to_dict()
    
    def _process_page(self, page, page_num: int):
        """Process a single PDF page"""
        # Extract tables from page
        tables = page.extract_tables()
        
        if not tables:
            print(f"  WARNING: No tables found on page {page_num}")
            return
        
        print(f"  Found {len(tables)} table(s)")
        
        for table_idx, table in enumerate(tables):
            self._process_table(table, page_num, table_idx)
    
    def _process_table(self, table: List[List[str]], page_num: int, table_idx: int):
        """Process a single table to extract cluster/subcluster data"""
        if not table or len(table) < 3:
            return
        
        # Try to find cluster information
        cluster_info = self._find_cluster_in_table(table)
        
        if cluster_info:
            print(f"    Found Cluster {cluster_info['code']}: {cluster_info.get('name', 'Unknown')}")
            
            # Create or get existing cluster
            cluster = self._get_or_create_cluster(cluster_info['code'], cluster_info.get('name', f"Cluster {cluster_info['code']}"))
            
            # Extract subclusters
            subclusters = self._extract_subclusters_from_table(table)
            
            for subcluster in subclusters:
                print(f"      Subcluster {subcluster.code}: {len(subcluster.programmes)} programmes")
                cluster.subclusters.append(subcluster)
    
    def _find_cluster_in_table(self, table: List[List[str]]) -> Optional[Dict]:
        """Find cluster code and name in table"""
        # Check first few rows for cluster header
        for row_idx, row in enumerate(table[:5]):
            if not row or not row[0]:
                continue
            
            cell_text = str(row[0]).strip()
            
            # Look for cluster code (1-20)
            match = self.cluster_pattern.match(cell_text)
            if match:
                code = match.group(1)
                name = match.group(2) if match.group(2) else ""
                
                # If name is empty, try to find it in adjacent cells or next row
                if not name and len(row) > 1 and row[1]:
                    name = str(row[1]).strip()
                
                if not name and row_idx + 1 < len(table):
                    next_row = table[row_idx + 1]
                    if next_row and next_row[0]:
                        potential_name = str(next_row[0]).strip()
                        if len(potential_name) > 5 and not potential_name[0].isdigit():
                            name = potential_name
                
                return {'code': code, 'name': name}
        
        return None
    
    def _extract_subclusters_from_table(self, table: List[List[str]]) -> List[SubCluster]:
        """Extract all subclusters from table"""
        subclusters = []
        current_subcluster = None
        yellow_row = None
        
        for row_idx, row in enumerate(table):
            if not row:
                continue
            
            # Check if this row has a subcluster code
            first_cell = str(row[0]).strip() if row[0] else ""
            second_cell = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            
            # Look for subcluster code in first or second column
            subcluster_match = self.subcluster_pattern.match(first_cell) or self.subcluster_pattern.match(second_cell)
            
            if subcluster_match:
                # Save previous subcluster if exists
                if current_subcluster:
                    subclusters.append(current_subcluster)
                
                # Create new subcluster
                code = subcluster_match.group(1)
                current_subcluster = SubCluster(code=code)
                
                # Try to extract grade requirements from this row (green row)
                # This is the row with specific grades like "C+", "B", etc.
                self._extract_grades_to_subcluster(current_subcluster, row, yellow_row)
                
            # Check if this is a yellow header row (subject categories)
            elif self._is_subject_header_row(row):
                yellow_row = row
            
            # Extract programme names if we have an active subcluster
            elif current_subcluster:
                programmes = self._extract_programmes_from_row(row)
                current_subcluster.programmes.extend(programmes)
        
        # Don't forget the last subcluster
        if current_subcluster:
            subclusters.append(current_subcluster)
        
        return subclusters
    
    def _is_subject_header_row(self, row: List[str]) -> bool:
        """Check if row is a yellow header row with subject categories"""
        row_text = ' '.join([str(cell) for cell in row if cell]).upper()
        # Yellow rows typically contain "SUBJECT" or subject codes
        return 'SUBJECT' in row_text or any(code in row_text for code in ['ENG', 'MAT', 'KIS', 'PHY', 'CHE', 'BIO', 'GROUP'])
    
    def _extract_grades_to_subcluster(self, subcluster: SubCluster, green_row: List[str], yellow_row: Optional[List[str]]):
        """Extract subject requirements by combining yellow row and green row"""
        # If we have both rows, combine them
        if yellow_row and len(green_row) >= 4:
            # Try to map yellow (categories) + green (grades)
            # This is a simplified approach - may need adjustment based on actual PDF structure
            for i in range(min(4, len(green_row))):
                if i < len(yellow_row) and yellow_row[i]:
                    category = str(yellow_row[i]).strip()
                    grade = str(green_row[i]).strip() if green_row[i] else ""
                    
                    # Combine: "MAT ALT A" + "C+" = "MAT ALT A - C+"
                    if category and grade:
                        combined = f"{category} - {grade}" if ' - ' not in category else category
                        setattr(subcluster, f'subject_{i+1}', combined)
        else:
            # Fallback: just use green row values directly
            for i, cell in enumerate(green_row[:4]):
                if cell:
                    setattr(subcluster, f'subject_{i+1}', str(cell).strip())
    
    def _extract_programmes_from_row(self, row: List[str]) -> List[str]:
        """Extract programme names from a table row"""
        programmes = []
        
        for cell in row:
            if not cell:
                continue
            
            cell_text = str(cell).strip()
            
            # Find all programme names in this cell
            matches = self.programme_pattern.findall(cell_text)
            for match in matches:
                cleaned = re.sub(r'\s+', ' ', match.strip())
                if len(cleaned) > 10:  # Reasonable minimum length
                    programmes.append(cleaned)
        
        return programmes
    
    def _get_or_create_cluster(self, code: str, name: str) -> Cluster:
        """Get existing cluster or create new one"""
        for cluster in self.clusters:
            if cluster.code == code:
                return cluster
        
        cluster = Cluster(code=code, name=name)
        self.clusters.append(cluster)
        return cluster
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert extracted data to dictionary"""
        return {
            'clusters': [
                {
                    **asdict(cluster),
                    'subclusters': [asdict(sc) for sc in cluster.subclusters]
                }
                for cluster in self.clusters
            ]
        }
    
    def save_to_json(self, output_path: str):
        """Save extracted data to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._to_dict()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract degree cluster data from PDF')
    parser.add_argument(
        '--pdf',
        default='KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf',
        help='Path to PDF file'
    )
    parser.add_argument(
        '--pages',
        default='all',
        help='Page range to process (e.g., "1-5" or "all")'
    )
    parser.add_argument(
        '--output',
        default='extraction_output/degree_clusters_v2.json',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("DEGREE CLUSTER EXTRACTION V2")
    print("="*60)
    
    extractor = DegreeClusterExtractor(args.pdf)
    data = extractor.extract(page_range=args.pages)
    extractor.save_to_json(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    for cluster in data['clusters']:
        print(f"\nCluster {cluster['code']}: {cluster['name']}")
        print(f"  Subclusters: {len(cluster['subclusters'])}")
        total_programmes = sum(len(sc['programmes']) for sc in cluster['subclusters'])
        print(f"  Total programmes: {total_programmes}")


if __name__ == "__main__":
    main()
