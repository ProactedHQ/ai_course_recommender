"""
Import Degree Clusters Command

Extracts cluster definitions, programme lists, and requirements from 
DEGREE_CLUSTER_DOCUMENT_2025_03.pdf (11 pages).

Creates:
- ClusterGroup records (if not exist)
- Programme records (generic, no institution)
- ProgrammeRequirement records (universal rules)

Usage:
    python manage.py import_degree_clusters
    python manage.py import_degree_clusters --dry-run
    python manage.py import_degree_clusters --output clusters.json
    python manage.py import_degree_clusters --seed
"""
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any

from .base_pdf_extractor import BasePDFExtractor


class Command(BasePDFExtractor):
    help = 'Extract degree cluster data from DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        # Override default PDF path
        parser.set_defaults(
            pdf='KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
        )
    
    def handle(self, *args, **options):
        # Import models here to avoid Django app registry issues
        from universities.models import ClusterGroup, Programme, ProgrammeLevel, ProgrammeRequirement
        from students.models import Subject
        
        # Store as instance variables for use in other methods
        self.ClusterGroup = ClusterGroup
        self.Programme = Programme
        self.ProgrammeLevel = ProgrammeLevel
        self.ProgrammeRequirement = ProgrammeRequirement
        self.Subject = Subject
        pdf_path = options['pdf']
        pages = options.get('pages', 'all')
        output_file = options.get('output') or 'degree_clusters_extracted.json'
        dry_run = options.get('dry_run', False)
        seed = options.get('seed', False)
        
        self.stdout.write(self.style.SUCCESS('\n📚 DEGREE CLUSTER EXTRACTION'))
        self.stdout.write('=' * 60)
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract tables from PDF
        tables = self.extract_tables_from_pdf(pdf_path, pages)
        
        if not tables:
            self.stdout.write(self.style.ERROR('❌ No tables found in PDF'))
            return
        
        # Process extracted tables
        clusters_data = self.process_cluster_tables(tables)
        
        # Export to JSON for validation
        self.export_to_json(
            clusters_data,
            output_file,
            metadata={
                'source_pdf': pdf_path,
                'total_clusters': len(clusters_data.get('clusters', [])),
                'total_programmes': len(clusters_data.get('programmes', [])),
            }
        )
        
        # Seed to database if requested
        if seed and not dry_run:
            self.seed_to_database(clusters_data)
        elif dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No data saved to database'))
            self.print_summary(clusters_data)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Extraction complete!'))
        self.stdout.write('=' * 60)
    
    def process_cluster_tables(self, tables: List) -> Dict[str, Any]:
        """
        Process tables extracted from PDF
        
        Expected structure per cluster:
        - Cluster number and name (header)
        - Subject requirements (columns: Subject 1-4 with codes/grades)
        - Programme list (long column of programme names)
        
        Returns:
            Dict with 'clusters' and 'programmes' lists
        """
        self.stdout.write('\n📊 Processing cluster tables...')
        
        clusters = []
        programmes = []
        current_cluster_code = None
        current_cluster_name = None
        
        for table_num, df in enumerate(tables, 1):
            self.logger.info(f"Processing table {table_num} with shape {df.shape}")
            
            # Clean the dataframe
            df = self.clean_dataframe(df)
            
            # Try to identify cluster header
            # Look for patterns like "CLUSTER 1", "1.", "Cluster 1 -", etc.
            cluster_info = self.extract_cluster_info(df)
            
            if cluster_info:
                current_cluster_code = cluster_info['code']
                current_cluster_name = cluster_info['name']
                
                cluster_data = {
                    'code': current_cluster_code,
                    'name': current_cluster_name,
                    'requirements': cluster_info.get('requirements', [])
                }
                clusters.append(cluster_data)
                
                self.stdout.write(f"  ✓ Found Cluster {current_cluster_code}: {current_cluster_name}")
            
            # Extract programme names from table
            programme_names = self.extract_programme_names(df, current_cluster_code)
            programmes.extend(programme_names)
        
        self.stdout.write(f'\n  📈 Extracted {len(clusters)} clusters')
        self.stdout.write(f'  📈 Extracted {len(programmes)} programmes')
        
        return {
            'clusters': clusters,
            'programmes': programmes
        }
    
    def extract_cluster_info(self, df) -> Dict[str, Any]:
        """
        Extract cluster code, name, and requirements from table
        
        Looks for:
        - Cluster number (1-20)
        - Cluster name (from header or sub-cluster text)
        - Subject requirements (Subject 1-4 columns)
        """
        cluster_info = None
        
        # Search for cluster number in first few rows
        for idx, row in df.head(5).iterrows():
            row_text = ' '.join([str(val) for val in row if val])
            
            # Look for patterns: "CLUSTER 1", "1.", "Cluster 1 -"
            import re
            match = re.search(r'(?:CLUSTER\s+)?(\d{1,2})[\s:\-\.]*(.*)', row_text, re.IGNORECASE)
            
            if match:
                code = match.group(1)
                name = match.group(2).strip() if match.group(2) else ''
                
                # Clean name (remove trailing punctuation, etc.)
                name = re.sub(r'^[\s\-:\.]+|[\s\-:\.]+$', '', name)
                
                if not name:
                    # Try to find name in next rows
                    name = self._find_cluster_name(df, idx + 1)
                
                cluster_info = {
                    'code': code,
                    'name': name or f'Cluster {code}',
                    'requirements': []
                }
                
                # Try to extract subject requirements
                requirements = self.extract_requirements(df)
                if requirements:
                    cluster_info['requirements'] = requirements
                
                break
        
        return cluster_info
    
    def _find_cluster_name(self, df, start_idx: int) -> str:
        """Search subsequent rows for cluster name"""
        for idx in range(start_idx, min(start_idx + 3, len(df))):
            if idx < len(df):
                row_text = ' '.join([str(val) for val in df.iloc[idx] if val and str(val).strip()])
                if row_text and len(row_text) > 5:  # Reasonable name length
                    return row_text.strip()
        return ''
    
    def extract_requirements(self, df) -> List[Dict]:
        """
        Extract subject requirements from table
        
        Looks for columns like "Subject 1", "Subject 2", etc.
        Format: "ENG(101):C+" or "MAT A/B" or "Any Group II"
        """
        requirements = []
        
        # Look for requirement columns
        req_columns = [col for col in df.columns if 'subject' in str(col).lower()]
        
        for col in req_columns:
            for val in df[col].dropna():
                if val and str(val).strip():
                    req_text = str(val).strip()
                    # Parse requirement (simplified for now)
                    requirements.append({
                        'description': req_text,
                        'is_category': 'group' in req_text.lower() or 'any' in req_text.lower()
                    })
        
        return requirements
    
    def extract_programme_names(self, df, cluster_code: str) -> List[Dict]:
        """
        Extract programme names from table, splitting blocks into individual records.
        """
        programmes = []
        import re
        
        # Keywords that indicate a new programme name
        # Using lookahead to split before these keywords
        split_pattern = re.compile(r'(?=(?:Bachelor|Diploma|Certificate|Artisan))')
        
        for col in df.columns:
            for val in df[col].dropna():
                val_str = str(val).strip()
                
                # Basic check for programme list column content
                if len(val_str) > 5 and any(kw in val_str.lower() for kw in ['bachelor', 'diploma', 'degree']):
                    # Split the block into individual names
                    parts = split_pattern.split(val_str)
                    
                    for part in parts:
                        cleaned = part.strip().replace('\n', ' ')
                        # Further cleanup: remove multiple spaces and potential trailing commas
                        cleaned = re.sub(r'\s+', ' ', cleaned)
                        cleaned = cleaned.rstrip(', ')
                        
                        if len(cleaned) > 10 and any(kw in cleaned.lower() for kw in ['bachelor', 'diploma']):
                            programmes.append({
                                'name': cleaned,
                                'cluster_code': cluster_code,
                                'kuccps_code': None
                            })
        
        return programmes
    
    def seed_to_database(self, data: Dict):
        """Seed extracted data to database"""
        self.stdout.write('\n💾 Seeding to database...')
        
        degree_level = self.ProgrammeLevel.objects.get(name='DEGREE')
        
        # Seed clusters
        for cluster_data in data['clusters']:
            cluster, created = self.ClusterGroup.objects.get_or_create(
                level=degree_level,
                code=cluster_data['code'],
                defaults={'name': cluster_data['name']}
            )
            
            status = '✨ Created' if created else '✓ Exists'
            self.stdout.write(f"  {status} Cluster {cluster.code}: {cluster.name}")
        
        # Seed programmes (without KUCCPS codes yet)
        created_count = 0
        skipped_count = 0
        
        for prog_data in data['programmes']:
            cluster_code = prog_data.get('cluster_code')
            cluster = self.ClusterGroup.objects.filter(
                level=degree_level,
                code=cluster_code
            ).first()
            
            if not cluster:
                self.log_error(0, 'cluster', f"Cluster {cluster_code} not found", prog_data)
                continue
            
            # Generate temporary KUCCPS code (will be updated from DEGREE_PROGRAMMES PDF)
            temp_code = f"TEMP_{cluster_code}_{created_count + skipped_count + 1}"
            
            # Check if programme already exists by name
            existing = self.Programme.objects.filter(name=prog_data['name']).first()
            
            if existing:
                skipped_count += 1
                continue
            
            self.Programme.objects.create(
                kuccps_code=temp_code,
                name=prog_data['name'],
                level=degree_level,
                cluster=cluster
            )
            created_count += 1
        
        self.stdout.write(f'\n  ✨ Created {created_count} new programmes')
        self.stdout.write(f'  ⏭️  Skipped {skipped_count} existing programmes')
    
    def print_summary(self, data: Dict):
        """Print summary of extracted data"""
        self.stdout.write('\n📋 EXTRACTION SUMMARY')
        self.stdout.write('-' * 40)
        
        for cluster in data['clusters']:
            self.stdout.write(f"\nCluster {cluster['code']}: {cluster['name']}")
            if cluster.get('requirements'):
                self.stdout.write(f"  Requirements: {len(cluster['requirements'])}")
        
        self.stdout.write(f"\n\nTotal Programmes: {len(data['programmes'])}")
        self.stdout.write(f"Total Errors: {len(self.errors)}")
