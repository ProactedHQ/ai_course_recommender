"""
Import Degree Cutoffs Command

Extracts historical cutoff data from DEGREE_CUTOFFS_14-07-2025.pdf (44 pages).

Structure:
- Columns: #, PROG CODE, INSTITUTION NAME, PROGRAMME NAME, 
           2018 CUTOFF, 2019 CUTOFF, 2020 CUTOFF, 2021 CUTOFF, 
           2022 CUTOFF, 2023 CUTOFF, 2024 CUTOFF

Creates/Updates:
- CutOffPoint records for years 2018-2024

Usage:
    python manage.py import_degree_cutoffs
    python manage.py import_degree_cutoffs --dry-run
    python manage.py import_degree_cutoffs --seed
"""
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any, Optional

from .base_pdf_extractor import BasePDFExtractor


class Command(BasePDFExtractor):
    help = 'Extract historical cutoff data from DEGREE_CUTOFFS_14-07-2025.pdf'
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(
            pdf='KUCCPS PROGRAMMES PDF/DEGREE_CUTOFFS_14-07-2025.pdf'
        )
    
    def handle(self, *args, **options):
        # Import models
        from universities.models import Institution, ProgrammeOffering, CutOffPoint, Programme
        
        self.Institution = Institution
        self.ProgrammeOffering = ProgrammeOffering
        self.CutOffPoint = CutOffPoint
        self.Programme = Programme
        
        pdf_path = options['pdf']
        pages = options.get('pages', 'all')
        output_file = options.get('output') or 'degree_cutoffs_extracted.json'
        dry_run = options.get('dry_run', False)
        seed = options.get('seed', False)
        
        self.stdout.write(self.style.SUCCESS('\n📊 DEGREE CUTOFFS EXTRACTION'))
        self.stdout.write('=' * 60)
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract tables
        tables = self.extract_tables_from_pdf(pdf_path, pages)
        
        if not tables:
            self.stdout.write(self.style.ERROR('❌ No tables found'))
            return
        
        # Process tables
        cutoffs_data = self.process_cutoff_tables(tables)
        
        # Export to JSON
        self.export_to_json(
            cutoffs_data,
            output_file,
            metadata={
                'source_pdf': pdf_path,
                'total_records': len(cutoffs_data),
            }
        )
        
        # Seed if requested
        if seed and not dry_run:
            self.seed_to_database(cutoffs_data)
        elif dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - No data saved'))
            self.print_summary(cutoffs_data[:10])
        
        self.stdout.write(self.style.SUCCESS('\n✅ Extraction complete!'))
        self.stdout.write('=' * 60)
    
    def process_cutoff_tables(self, tables: List) -> List[Dict]:
        """Process tables and extract cutoff records"""
        self.stdout.write('\n📊 Processing cutoff tables...')
        
        all_cutoffs = []
        
        for table_num, df in enumerate(tables, 1):
            self.logger.info(f"Processing table {table_num} with shape {df.shape}")
            
            # Clean dataframe
            df = self.clean_dataframe(df)
            
            if df.empty:
                continue
            
            # Extract cutoffs from this table
            cutoffs = self.extract_cutoffs_from_table(df)
            all_cutoffs.extend(cutoffs)
        
        self.stdout.write(f'\n  📈 Extracted {len(all_cutoffs)} cutoff records')
        
        return all_cutoffs
    
    def extract_cutoffs_from_table(self, df) -> List[Dict]:
        """Extract cutoff records from a single table"""
        cutoffs = []
        
        # Check if table has expected columns
        has_prog_code = any('PROG' in str(col).upper() and 'CODE' in str(col).upper() for col in df.columns)
        has_cutoff = any('CUTOFF' in str(col).upper() or any(str(year) in str(col) for year in range(2018, 2025)) for col in df.columns)
        
        if not (has_prog_code and has_cutoff):
            self.logger.warning(f"Table doesn't have expected columns")
            return cutoffs
        
        # Process all rows
        for idx, row in df.iterrows():
            # Skip category rows
            if self.is_category_row(row):
                continue
            
            # Extract cutoff data
            cutoff_data = self.parse_cutoff_row(row, idx)
            
            if cutoff_data:
                cutoffs.append(cutoff_data)
        
        return cutoffs
    
    def is_category_row(self, row) -> bool:
        """Check if row is a category header"""
        non_null_count = row.notna().sum()
        
        if non_null_count < 3:
            return True
        
        first_cell = str(row.iloc[1] if len(row) > 1 else row.iloc[0])
        if 'BACHELOR' in first_cell.upper() or 'DIPLOMA' in first_cell.upper():
            second_cell = str(row.iloc[1] if len(row) > 1 else '')
            if not self.looks_like_prog_code(second_cell):
                return True
        
        return False
    
    def looks_like_prog_code(self, value: str) -> bool:
        """Check if value looks like a KUCCPS code"""
        if not value:
            return False
        value_clean = str(value).strip()
        return value_clean.isdigit() and len(value_clean) >= 6
    
    def parse_cutoff_row(self, row, row_idx: int) -> Optional[Dict]:
        """Parse a single cutoff record row"""
        try:
            # Find column indices
            columns = {str(col).upper().replace('\n', ' ').replace('  ', ' '): i 
                      for i, col in enumerate(row.index)}
            
            # Get PROG CODE
            prog_code_idx = None
            for col_name, idx in columns.items():
                if 'PROG' in col_name and 'CODE' in col_name:
                    prog_code_idx = idx
                    break
            
            if prog_code_idx is None:
                return None
            
            prog_code = str(row.iloc[prog_code_idx]).strip() if row.iloc[prog_code_idx] else None
            
            if not prog_code or not self.looks_like_prog_code(prog_code):
                return None
            
            # Get institution and programme name
            institution_name = None
            programme_name = None
            cutoffs_by_year = {}
            
            for col_name, idx in columns.items():
                val = row.iloc[idx]
                # Handle NaN/None correctly
                if pd.isna(val) or val is None:
                    val_str = None
                else:
                    val_str = str(val).strip()
                
                if 'INSTITUTION' in col_name and 'NAME' in col_name:
                    institution_name = val_str
                elif 'PROGRAMME' in col_name and 'NAME' in col_name:
                    programme_name = val_str
                else:
                    # Check if column name contains a year
                    for year in range(2018, 2025):
                        if str(year) in col_name:
                            cutoff_val = self.parse_cutoff_value(val_str)
                            if cutoff_val:
                                cutoffs_by_year[year] = cutoff_val
            
            if not institution_name or not programme_name or not cutoffs_by_year:
                return None
            
            return {
                'kuccps_code': prog_code,
                'institution_name': institution_name,
                'programme_name': programme_name,
                'cutoffs': cutoffs_by_year
            }
            
        except Exception as e:
            self.log_error(row_idx, 'parsing', str(e), {'row': str(row)})
            return None
    
    def seed_to_database(self, cutoffs_data: List[Dict]):
        """Seed extracted cutoffs to database using bulk operations"""
        self.stdout.write('\n💾 Seeding to database (Optimized)...')
        
        # 1. Load caches
        self.stdout.write("  Loading existing data...")
        
        # Cache all programmes by KUCCPS code
        programmes_map = {p.kuccps_code: p for p in self.Programme.objects.all()}
        
        # Cache all institutions
        institutions_map = {}
        for inst in self.Institution.objects.all():
            if inst.code:
                institutions_map[inst.code.upper().strip()] = inst
            if inst.name:
                name_key = inst.name.upper().strip()
                institutions_map[name_key] = inst
                institutions_map[" ".join(name_key.split())] = inst
        
        # Cache all existing offerings
        existing_offerings = {
            (off.programme_id, off.institution_id): off
            for off in self.ProgrammeOffering.objects.select_related('programme', 'institution').all()
        }
        
        self.stdout.write(f"  Loaded {len(programmes_map)} programmes, {len(institutions_map)} institutions, {len(existing_offerings)} offerings")
        
        # 2. Prepare new offerings and cutoffs
        new_offerings = []
        cutoffs_to_create = []
        offerings_for_cutoffs = []  # Track which offering goes with which cutoff data
        
        stats = {
            'offerings_not_found': 0,
            'programmes_not_found': 0,
            'institutions_not_found': 0,
            'errors': 0
        }
        
        for idx, data in enumerate(cutoffs_data, 1):
            try:
                # Find programme
                prog_code = data['kuccps_code']
                if prog_code not in programmes_map:
                    stats['programmes_not_found'] += 1
                    self.log_error(idx, 'programme', f"Programme not found: {prog_code}", data)
                    continue
                
                programme = programmes_map[prog_code]
                
                # Find institution
                inst_name = self.normalize_institution_name(data['institution_name'])
                inst_name_clean = inst_name.strip().upper()
                inst_name_normalized = " ".join(inst_name_clean.split())
                
                institution = None
                if inst_name_clean in institutions_map:
                    institution = institutions_map[inst_name_clean]
                elif inst_name_normalized in institutions_map:
                    institution = institutions_map[inst_name_normalized]
                
                if not institution:
                    stats['institutions_not_found'] += 1
                    self.log_error(idx, 'institution', f"Institution not found: {inst_name}", data)
                    continue
                
                # Check if offering exists
                key = (programme.id, institution.id)
                if key in existing_offerings:
                    offering = existing_offerings[key]
                else:
                    # Create new offering
                    offering = self.ProgrammeOffering(programme=programme, institution=institution)
                    new_offerings.append(offering)
                    existing_offerings[key] = offering
                
                # Track this offering with its cutoff data
                offerings_for_cutoffs.append((offering, data['cutoffs']))
                
            except Exception as e:
                stats['errors'] += 1
                self.log_error(idx, 'processing', str(e), data)
        
        # 3. Bulk create new offerings
        if new_offerings:
            self.stdout.write(f"  Creating {len(new_offerings)} new offerings (ignoring conflicts)...")
            self.ProgrammeOffering.objects.bulk_create(new_offerings, ignore_conflicts=True)
            
            # Reload offerings to get IDs
            self.stdout.write("  Reloading offering IDs...")
            existing_offerings = {
                (off.programme_id, off.institution_id): off
                for off in self.ProgrammeOffering.objects.select_related('programme', 'institution').all()
            }
        
        # 4. Prepare cutoffs for bulk creation
        self.stdout.write("  Preparing cutoffs for bulk insertion...")
        for offering, cutoffs_by_year in offerings_for_cutoffs:
            # Re-bind to DB offering (which has ID)
            key = (offering.programme_id, offering.institution_id)
            if key in existing_offerings:
                real_offering = existing_offerings[key]
                
                for year, cutoff_value in cutoffs_by_year.items():
                    if cutoff_value:  # Skip None values
                        cutoffs_to_create.append(
                            self.CutOffPoint(
                                offering=real_offering,
                                year=int(year),
                                weighted_cluster_points=cutoff_value,
                                cutoff_type='WEIGHTED_POINTS'
                            )
                        )
        
        # 5. Bulk create cutoffs
        if cutoffs_to_create:
            self.stdout.write(f"  Creating {len(cutoffs_to_create)} cutoffs (ignoring conflicts)...")
            self.CutOffPoint.objects.bulk_create(cutoffs_to_create, ignore_conflicts=True)
        
        # Print summary
        self.stdout.write('\n📊 SEEDING SUMMARY:')
        self.stdout.write(f"  ✨ New offerings: {len(new_offerings)}")
        self.stdout.write(f"  ✨ Cutoffs created: {len(cutoffs_to_create)}")
        self.stdout.write(f"  ⚠️  Programmes not found: {stats['programmes_not_found']}")
        self.stdout.write(f"  ⚠️  Institutions not found: {stats['institutions_not_found']}")
        self.stdout.write(f"  ❌ Errors: {stats['errors']}")
    
    def print_summary(self, sample_data: List[Dict]):
        """Print summary of extracted data"""
        self.stdout.write('\n📋 SAMPLE DATA (first 10):')
        self.stdout.write('-' * 60)
        
        for data in sample_data:
            self.stdout.write(f"\n{data['kuccps_code']}: {data['programme_name']}")
            self.stdout.write(f"  Institution: {data['institution_name']}")
            self.stdout.write(f"  Years with cutoffs: {list(data['cutoffs'].keys())}")
