"""
Base PDF Extractor for KUCCPS Data

Provides shared utilities for extracting data from KUCCPS PDFs:
- PDF reading with pdfplumber
- Data cleaning and normalization
- JSON export for validation
- Error logging
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

import pdfplumber
import pandas as pd
from django.core.management.base import BaseCommand


class BasePDFExtractor(BaseCommand):
    """Base class for KUCCPS PDF extraction commands"""
    
    # Valid KCSE grades
    VALID_GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = self.setup_logger()
        self.errors = []
        self.extracted_data = []
        
        # Lazy-load institution mapping (will be loaded on first access)
        self._institution_mapping = None
    
    @property
    def institution_mapping(self) -> Dict[str, str]:
        """Lazy-load institution mapping from database"""
        if self._institution_mapping is None:
            self._institution_mapping = self._load_institution_mapping()
        return self._institution_mapping
        
    def _load_institution_mapping(self) -> Dict[str, str]:
        """
        Load institution code <-> name mapping from database
        Returns a dict where both code->name and name->code mappings exist
        """
        from universities.models import Institution
        
        mapping = {}
        institutions = Institution.objects.all()
        
        self.logger.info(f"Loaded {institutions.count()} institutions from database")
        
        for inst in institutions:
            # Code -> Name mapping
            if inst.code:
                code_key = inst.code.upper().strip()
                mapping[code_key] = inst.name
            
            # Name -> Name mapping (for exact matches)
            if inst.name:
                name_key = inst.name.upper().strip()
                mapping[name_key] = inst.name
                
                # Also add normalized version (single whitespace)
                name_normalized = " ".join(name_key.split())
                if name_normalized != name_key:
                    mapping[name_normalized] = inst.name

        return mapping
        
    def setup_logger(self) -> logging.Logger:
        """Setup logging for extraction process"""
        log_dir = Path('extraction_logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'{self.__class__.__name__}_{timestamp}.log'
        
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def extract_tables_from_pdf(self, pdf_path: str, pages: str = 'all') -> List[pd.DataFrame]:
        """
        Extract tables from PDF using pdfplumber
        
        Args:
            pdf_path: Path to PDF file
            pages: Page specification ('all', '1-5', '1,3,5')
        
        Returns:
            List of DataFrames, one per table found
        """
        self.logger.info(f"Opening PDF: {pdf_path}")
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Determine which pages to process
                if pages == 'all':
                    page_list = pdf.pages
                else:
                    # Parse page specification
                    page_list = self._parse_page_spec(pages, len(pdf.pages))
                    page_list = [pdf.pages[i] for i in page_list]
                
                for page_num, page in enumerate(page_list, 1):
                    self.logger.info(f"Processing page {page_num}...")
                    
                    # Extract tables from page
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables, 1):
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])  # First row as header
                            tables.append(df)
                            self.logger.info(f"  Found table {table_num} with {len(df)} rows")
                
                self.logger.info(f"Extracted {len(tables)} tables total")
                
        except Exception as e:
            self.logger.error(f"Error reading PDF: {str(e)}")
            raise
        
        return tables
    
    def _parse_page_spec(self, spec: str, total_pages: int) -> List[int]:
        """Parse page specification like '1-5' or '1,3,5'"""
        pages = []
        for part in spec.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start - 1, min(end, total_pages)))
            else:
                pages.append(int(part) - 1)
        return pages
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean extracted DataFrame
        - Remove empty rows/columns
        - Replace '-' with None
        - Forward fill merged cells
        - Strip whitespace
        """
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Replace common null indicators
        df = df.replace(['-', '—', 'N/A', 'n/a', ''], None)
        
        # Strip whitespace from string columns
        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].str.replace('\n', ' ', regex=False).str.strip()
        
        # Forward fill merged cells (common in PDFs)
        df = df.ffill()
        
        return df
    
    def normalize_institution_name(self, name: str) -> Optional[str]:
        """
        Normalize institution name using database mapping
        Handles both codes (e.g., 'UON') and full names
        
        Args:
            name: Institution code or name from PDF
            
        Returns:
            Normalized institution name from database, or None if not found
        """
        if not name:
            return None
        
        # Try exact match (case-insensitive)
        name_upper = name.strip().upper()
        if name_upper in self.institution_mapping:
            return self.institution_mapping[name_upper]
            
        # Try normalized whitespace
        name_normalized = " ".join(name_upper.split())
        if name_normalized in self.institution_mapping:
            return self.institution_mapping[name_normalized]
        
        # Try fuzzy match on partial name (optional enhancement)
        # For now, log warning if not found
        self.logger.warning(f"Institution not found in database: '{name}'")
        return name.strip()  # Return original if not found
    
    def parse_cutoff_value(self, value: str) -> Optional[Decimal]:
        """Parse cut-off value, handling None/'-' gracefully"""
        if not value or value == '-':
            return None
        
        try:
            return Decimal(str(value).strip())
        except:
            self.logger.warning(f"Invalid cutoff value: {value}")
            return None
    
    def parse_grade(self, grade_str: str) -> Optional[str]:
        """Parse and validate grade"""
        if not grade_str:
            return None
        
        grade = grade_str.strip().upper()
        if grade in self.VALID_GRADES:
            return grade
        
        self.logger.warning(f"Invalid grade: {grade_str}")
        return None
    
    def export_to_json(self, data: List[Dict], output_file: str, metadata: Dict[str, Any] = None):
        """
        Export extracted data to JSON for validation
        
        Args:
            data: List of dictionaries to export
            output_file: Output JSON filename
            metadata: Optional metadata to include
        """
        output_path = Path('extraction_output') / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        export_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_records': len(data),
                'total_errors': len(self.errors),
                **(metadata or {})
            },
            'data': data,
            'errors': self.errors
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Exported {len(data)} records to {output_path}")
        self.stdout.write(self.style.SUCCESS(f'Data exported to {output_path}'))
    
    def log_error(self, row_num: int, field: str, message: str, data: Dict = None):
        """Log an extraction error"""
        error = {
            'row': row_num,
            'field': field,
            'message': message,
            'data': data
        }
        self.errors.append(error)
        self.logger.error(f"Row {row_num}, {field}: {message}")
    
    def add_arguments(self, parser):
        """Common arguments for extraction commands"""
        parser.add_argument(
            '--pdf',
            type=str,
            help='Path to PDF file (if not default)',
        )
        parser.add_argument(
            '--pages',
            type=str,
            default='all',
            help='Pages to extract (e.g., "all", "1-5", "1,3,5")',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON filename',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Extract and validate but don\'t save to database',
        )
        parser.add_argument(
            '--seed',
            action='store_true',
            help='Seed extracted data to database',
        )
