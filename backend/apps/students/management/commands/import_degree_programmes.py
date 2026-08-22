"""
Import Degree Programmes Command

Extracts programme data from DEGREE_PROGRAMMES_2025.pdf (78 pages).

Structure:
- Headers: #, PROG CODE, INSTITUTION NAME, PROGRAMME NAME, CUTOFF-2023, CUTOFF-2022, SUBJECT 1-4
- Merged category rows (skip): "BACHELOR OF ARTS", etc.
- Data rows: Individual programme records with all details

Creates/Updates:
- Programme records (with KUCCPS codes)
- Institution records (match to existing)
- ProgrammeOffering records
- CutOffPoint records (2023, 2022)
- ProgrammeRequirement records

Usage:
    python manage.py import_degree_programmes
    python manage.py import_degree_programmes --dry-run
    python manage.py import_degree_programmes --seed
"""
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any, Optional
import re
import pandas as pd

from .base_pdf_extractor import BasePDFExtractor


class Command(BasePDFExtractor):
    help = 'Extract degree programme data from DEGREE_PROGRAMMES_2025.pdf'
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(
            pdf='KUCCPS PROGRAMMES PDF/DEGREE_PROGRAMMES_2025.pdf'
        )
    
    def handle(self, *args, **options):
        # Import models here
        from universities.models import (
            ClusterGroup, Programme, ProgrammeLevel, 
            ProgrammeRequirement, Institution, ProgrammeOffering, CutOffPoint
        )
        from students.models import Subject
        
        # Store as instance variables
        self.ClusterGroup = ClusterGroup
        self.Programme = Programme
        self.ProgrammeLevel = ProgrammeLevel
        self.ProgrammeRequirement = ProgrammeRequirement
        self.Institution = Institution
        self.ProgrammeOffering = ProgrammeOffering
        self.CutOffPoint = CutOffPoint
        self.Subject = Subject
        
        pdf_path = options['pdf']
        pages = options.get('pages', 'all')
        output_file = options.get('output') or 'degree_programmes_extracted.json'
        dry_run = options.get('dry_run', False)
        seed = options.get('seed', False)
        
        self.stdout.write(self.style.SUCCESS('\nDEGREE PROGRAMMES EXTRACTION'))
        self.stdout.write('=' * 60)
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract tables
        tables = self.extract_tables_from_pdf(pdf_path, pages)
        
        if not tables:
            self.stdout.write(self.style.ERROR('ERROR: No tables found'))
            return
        
        # Process tables
        programmes_data = self.process_programme_tables(tables)
        
        # Export to JSON
        self.export_to_json(
            programmes_data,
            output_file,
            metadata={
                'source_pdf': pdf_path,
                'total_programmes': len(programmes_data),
            }
        )
        
        # Seed if requested
        if seed and not dry_run:
            self.seed_to_database(programmes_data)
        elif dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No data saved'))
            self.print_summary(programmes_data[:10])  # Show first 10
        
        self.stdout.write(self.style.SUCCESS('\nExtraction complete!'))
        self.stdout.write('=' * 60)
    
    def process_programme_tables(self, tables: List) -> List[Dict]:
        """Process tables and extract programme records"""
        self.stdout.write('\nProcessing programme tables...')
        
        all_programmes = []
        
        for table_num, df in enumerate(tables, 1):
            self.logger.info(f"Processing table {table_num} with shape {df.shape}")
            
            # Clean dataframe
            df = self.clean_dataframe(df)
            
            # Skip if empty
            if df.empty:
                continue
            
            # Extract programmes from this table
            programmes = self.extract_programmes_from_table(df)
            all_programmes.extend(programmes)
        
        self.stdout.write(f'\n  Extracted {len(all_programmes)} programme records')
        
        return all_programmes
    
    def extract_programmes_from_table(self, df) -> List[Dict]:
        """Extract programme records from a single table"""
        programmes = []
        
        # The header is already the DataFrame columns (from pdfplumber)
        # Check if we have the expected columns
        has_prog_code = any('PROG' in str(col).upper() and 'CODE' in str(col).upper() for col in df.columns)
        has_programme = any('PROGRAMME' in str(col).upper() for col in df.columns)
        
        if not (has_prog_code and has_programme):
            self.logger.warning(f"Table doesn't have expected columns: {list(df.columns)}")
            return programmes
        
        # Process all rows
        for idx, row in df.iterrows():
            # Skip category rows
            if self.is_category_row(row):
                continue
            
            # Extract programme data
            prog_data = self.parse_programme_row(row, idx)
            
            if prog_data:
                programmes.append(prog_data)
        
        return programmes
    
    def find_header_row(self, df) -> Optional[int]:
        """Find the row containing headers (DEPRECATED - headers are DataFrame columns)"""
        # Not needed anymore - pdfplumber puts headers as column names
        return 0
    
    def is_category_row(self, row) -> bool:
        """Check if row is a merged category header (to skip)"""
        # Category rows typically have:
        # - Very few non-null cells
        # - Text like "BACHELOR OF ..."
        # - No PROG CODE (numeric code)
        
        non_null_count = row.notna().sum()
        
        # If less than 3 cells filled, likely a category row
        if non_null_count < 3:
            return True
        
        # Check first cell - if it's text like "BACHELOR", it's a category
        first_cell = str(row.iloc[1] if len(row) > 1 else row.iloc[0])
        if 'BACHELOR' in first_cell.upper() or 'DIPLOMA' in first_cell.upper():
            # But make sure there's no PROG CODE
            second_cell = str(row.iloc[1] if len(row) > 1 else '')
            if not self.looks_like_prog_code(second_cell):
                return True
        
        return False
    
    def looks_like_prog_code(self, value: str) -> bool:
        """Check if value looks like a KUCCPS programme code"""
        if not value:
            return False
        
        # PROG CODES are typically numeric, 6-8 digits
        value_clean = str(value).strip()
        return value_clean.isdigit() and len(value_clean) >= 6
    
    def parse_programme_row(self, row, row_idx: int) -> Optional[Dict]:
        """Parse a single programme record row"""
        try:
            # Find column indices by name (handling newlines in column names)
            columns = {str(col).upper().replace('\n', ' ').replace('  ', ' '): i 
                      for i, col in enumerate(row.index)}
            
            # Get PROG CODE column
            prog_code_idx = None
            for col_name, idx in columns.items():
                if 'PROG' in col_name and 'CODE' in col_name:
                    prog_code_idx = idx
                    break
            
            if prog_code_idx is None:
                return None
            
            prog_code = str(row.iloc[prog_code_idx]).strip() if row.iloc[prog_code_idx] else None
            
            # Validate prog code
            if not prog_code or not self.looks_like_prog_code(prog_code):
                return None
            
            # Get other fields by column name patterns
            institution_name = None
            programme_name = None
            cutoff_2023 = None
            cutoff_2022 = None
            subjects = []
            
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
                elif '2023' in col_name:
                    cutoff_2023 = self.parse_cutoff_value(val_str)
                elif '2022' in col_name:
                    cutoff_2022 = self.parse_cutoff_value(val_str)
                elif 'SUBJECT' in col_name and val_str:
                    subjects.append(val_str)
            
            # Validate minimum required fields
            if not programme_name or not institution_name:
                return None
            
            return {
                'kuccps_code': prog_code,
                'institution_name': institution_name,
                'programme_name': programme_name,
                'cutoff_2023': cutoff_2023,
                'cutoff_2022': cutoff_2022,
                'subjects': subjects
            }
            
        except Exception as e:
            self.log_error(row_idx, 'parsing', str(e), {'row': str(row)})
            return None
    
    def seed_to_database(self, programmes_data: List[Dict]):
        """Seed extracted programmes to database using bulk operations"""
        self.stdout.write('\nSeeding to database (Optimized)...')
        
        degree_level = self.ProgrammeLevel.objects.get(name='DEGREE')
        
        # 1. Load Caches
        self.stdout.write("  Loading existing data...")
        institutions_map = self.load_institutions_map()
        existing_programmes = {p.kuccps_code: p for p in self.Programme.objects.filter(level=degree_level)}
        
        # 2. Prepare new Programmes
        new_programmes = []
        programme_updates = [] # If needed, though bulk update is tricky without ID match
        
        # Dedup extracted programmes by code
        unique_extracted = {d['kuccps_code']: d for d in programmes_data}
        
        for code, data in unique_extracted.items():
            if code not in existing_programmes:
                new_programmes.append(
                    self.Programme(
                        kuccps_code=code,
                        name=data['programme_name'],
                        level=degree_level
                    )
                )
        
        # Bulk Create Programmes
        if new_programmes:
            self.stdout.write(f"  Creating {len(new_programmes)} new programmes...")
            created_progs = self.Programme.objects.bulk_create(new_programmes)
            # Add to cache (Postgres returns IDs)
            for p in created_progs:
                existing_programmes[p.kuccps_code] = p
                
        # 3. Process Offerings & Cutoffs
        self.stdout.write("  Processing offerings and cutoffs...")
        
        # Prefetch existing offerings to avoid duplicates
        existing_offerings = {
            (off.programme_id, off.institution_id): off 
            for off in self.ProgrammeOffering.objects.filter(programme__level=degree_level)
        }
        
        new_offerings = []
        cutoffs_to_create = []
        requirements_to_create = []
        
        # We need to track which offering object corresponds to which data to link cutoffs
        # So we'll process in two passes: 
        # Pass 1: Create missing offerings
        # Pass 2: Create cutoffs using offering IDs
        
        offering_data_map = [] # Tuple of (programme, institution, data)
        
        for data in programmes_data:
            code = data['kuccps_code']
            if code not in existing_programmes:
                continue # Should trigger error but we skip for speed
                
            programme = existing_programmes[code]
            inst_name = self.normalize_institution_name(data['institution_name'])
            
            # Find institution (cached)
            institution = self.find_institution(inst_name, institutions_map)
            
            if not institution:
                 # Try creating it? Or skip?
                 # For bulk speed, we might skip or fail.
                 # Let's create it on the fly if really needed, but it kills bulk.
                 # Better to log error.
                 self.log_error(0, 'institution', f"Institution not found: {data['institution_name']}", data)
                 continue

            key = (programme.id, institution.id)
            
            # Check against both DB and currently accumulating list
            if key in existing_offerings:
                offering = existing_offerings[key]
                offering_data_map.append((offering, data))
            else:
                # New offering
                offering = self.ProgrammeOffering(programme=programme, institution=institution)
                new_offerings.append(offering)
                # Add to existing_offerings to prevent future duplicates in this loop
                existing_offerings[key] = offering
                
                offering_data_map.append((offering, data))

        # Bulk Create Offerings
        if new_offerings:
            self.stdout.write(f"  Creating {len(new_offerings)} new offerings (ignoring conflicts)...")
            self.ProgrammeOffering.objects.bulk_create(new_offerings, ignore_conflicts=True)
            
            # Since ignore_conflicts=True creates mappings but doesn't return IDs,
            # and we need IDs for cutoffs, we MUST reload the entire offerings map from DB.
            self.stdout.write("  Reloading offering IDs from database...")
            existing_offerings = {
                (off.programme_id, off.institution_id): off 
                for off in self.ProgrammeOffering.objects.filter(programme__level=degree_level)
            }
            
        # 4. Prepare Cutoffs & Requirements
        for offering, data in offering_data_map:
            # We need to re-bind the offering object to the one from DB (which has ID)
            key = (offering.programme_id, offering.institution_id)
            if key in existing_offerings:
                real_offering = existing_offerings[key]
                # Update our map so we use the real one for cutoffs
                offering = real_offering
            else:
                # This shouldn't happen if creation worked or existed
                self.logger.warning(f"  Offering not found after creation: {data['programme_name']} at {data['institution_name']}")
                continue
                
            # Cutoffs
            for year in [2022, 2023]:
                field = f'cutoff_{year}'
                val = data.get(field)
                if val:
                    cutoffs_to_create.append(
                        self.CutOffPoint(
                            offering=offering,
                            year=year,
                            weighted_cluster_points=val,
                            cutoff_type='WEIGHTED_POINTS'
                        )
                    )
            
            # Requirements
            for subj in data.get('subjects', []):
                if subj:
                    requirements_to_create.append(
                        self.ProgrammeRequirement(
                            programme=offering.programme, # Linked to Programme not Offering
                            description=subj,
                            is_category=True,
                            minimum_grade='C+'
                        )
                    )

        # Bulk Create Cutoffs
        # Note: bulk_create doesn't handle conflicts (update_or_create logic).
        # Since we just created offerings, we assume no cutoffs exist for them?
        # But for EXISTING offerings, cutoffs might exist.
        # We should use ignore_conflicts=True for cutoffs to rely on unique constraints (if any)
        # Or checking existence. Checking existence is expensive.
        # We'll use ignore_conflicts=True
        
        if cutoffs_to_create:
            self.stdout.write(f"  Creating {len(cutoffs_to_create)} cutoffs...")
            self.CutOffPoint.objects.bulk_create(cutoffs_to_create, ignore_conflicts=True)

        # Bulk Create Requirements
        # Requirements are linked to Programme, so duplicated across offerings.
        # We need to dedup requirements by (prog_id, description)
        unique_reqs = {}
        for req in requirements_to_create:
            key = (req.programme_id, req.description)
            if key not in unique_reqs:
                unique_reqs[key] = req
        
        final_reqs = list(unique_reqs.values())
        if final_reqs:
            self.stdout.write(f"  Creating {len(final_reqs)} requirements...")
            self.ProgrammeRequirement.objects.bulk_create(final_reqs, ignore_conflicts=True)
            
        self.stdout.write(self.style.SUCCESS('\nBulk seeding complete!'))

    def load_institutions_map(self):
        """Load institutions into memory for fast lookup"""
        # Mapping logic reused from base extract but returns objects
        mapping = {}
        # We essentially need name -> Institution Object
        all_insts = self.Institution.objects.all()
        for inst in all_insts:
            # Add all variants
            if inst.code:
                mapping[inst.code.upper().strip()] = inst
            if inst.name:
                name_key = inst.name.upper().strip()
                mapping[name_key] = inst
                mapping[" ".join(name_key.split())] = inst
        return mapping

    def find_institution(self, name, mapping):
        if not name: return None
        name_clean = name.strip().upper()
        # Direct lookup
        if name_clean in mapping:
            return mapping[name_clean]
        # Normalized lookup
        normalized = " ".join(name_clean.split())
        if normalized in mapping:
            return mapping[normalized]
        return None
    
    def print_summary(self, sample_data: List[Dict]):
        """Print summary of extracted data"""
        self.stdout.write('\nSAMPLE DATA (first 10 records):')
        self.stdout.write('-' * 60)
        
        for prog in sample_data:
            self.stdout.write(f"\n{prog['kuccps_code']}: {prog['programme_name']}")
            self.stdout.write(f"  Institution: {prog['institution_name']}")
            self.stdout.write(f"  Cutoff 2023: {prog.get('cutoff_2023', 'N/A')}")
            self.stdout.write(f"  Subjects: {len(prog.get('subjects', []))}")
