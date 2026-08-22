
import os
import sys
import django
import pdfplumber
import re
import logging
from decimal import Decimal
from django.db import transaction

# Add project root and apps to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.models import Institution, Programme, ProgrammeLevel, ProgrammeOffering, ProgrammeRequirement, ClusterGroup
from apps.students.models import Subject

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("tvet_extraction.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# In-memory caches to reduce DB hits
INSTITUTION_CACHE = {}
PROGRAMME_CACHE = {}
CLUSTER_CACHE = {}

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def get_or_create_institution_cached(name):
    name = clean_text(name)
    if not name: return None
    
    if name in INSTITUTION_CACHE:
        return INSTITUTION_CACHE[name]
        
    inst, created = Institution.objects.get_or_create(
        name=name,
        defaults={'code': f"TVET-{abs(hash(name)) % 1000000}", 'institution_type': 'TVET', 'location': 'Kenya'}
    )
    if created:
        logger.debug(f"New Institution created: {name}")
    INSTITUTION_CACHE[name] = inst
    return inst

def get_or_create_cluster_cached(name, level):
    name = clean_text(name)
    if not name: return None
    
    cache_key = f"{level.name}:{name}"
    if cache_key in CLUSTER_CACHE:
        return CLUSTER_CACHE[cache_key]
    
    cluster, created = ClusterGroup.objects.get_or_create(
        name=name,
        level=level,
        defaults={'code': ''}
    )
    if created:
        logger.info(f"New Trade Group (Cluster): {name} for {level.name}")
    CLUSTER_CACHE[cache_key] = cluster
    return cluster

@transaction.atomic
def process_table_rows_optimized(rows, level, cluster, cost_col=None, grade_col=None, req_col=None):
    count = 0
    for row in rows:
        if not row or len(row) < 4: continue
        
        # Skip header rows
        if any(h in str(row[1]).upper() for h in ['PROG CODE', 'CODE', 'PROG #']):
            continue
            
        code = clean_text(row[1])
        inst_name = clean_text(row[2])
        prog_name = clean_text(row[3])
        
        if not code or not inst_name or not prog_name: continue
        
        try:
            # 1. Institution
            institution = get_or_create_institution_cached(inst_name)
            
            # 2. Programme
            min_grade = "E"
            if grade_col is not None and len(row) > grade_col:
                min_grade = clean_text(row[grade_col]) or min_grade
                
            programme, p_created = Programme.objects.update_or_create(
                kuccps_code=code,
                defaults={
                    'name': prog_name,
                    'level': level,
                    'cluster': cluster,
                    'minimum_mean_grade': min_grade
                }
            )
            
            # 3. Offering
            cost = None
            if cost_col is not None and len(row) > cost_col:
                cost_str = clean_text(row[cost_col]).replace(',', '')
                try:
                    cost = Decimal(cost_str)
                except:
                    cost = None
                    
            offering, o_created = ProgrammeOffering.objects.update_or_create(
                programme=programme,
                institution=institution,
                defaults={'cost': cost}
            )
            
            # 4. Requirements (for Craft)
            if req_col is not None and len(row) > req_col:
                req_text = clean_text(row[req_col])
                if req_text and req_text.upper() != 'BLANK':
                    ProgrammeRequirement.objects.update_or_create(
                        programme=programme,
                        description=req_text,
                        defaults={'minimum_grade': 'D'}
                    )
            
            count += 1
            if count % 20 == 0:
                logger.debug(f"  Processed {count} rows in current table...")
                
        except Exception as e:
            logger.error(f"Error processing row {code} for {inst_name}: {str(e)}")
            
    return count

def extract_from_pdf_optimized(pdf_path, level_name, columns_count, grade_idx=None, cost_idx=None, req_idx=None):
    logger.info(f"Starting extraction for {level_name} Level...")
    logger.info(f"Source PDF: {pdf_path}")
    
    level, _ = ProgrammeLevel.objects.get_or_create(name=level_name)
    total_extracted = 0
    
    if not os.path.exists(pdf_path):
        logger.warning(f"File not found: {pdf_path}. Skipping.")
        return 0

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        logger.info(f"PDF opened successfully. Total pages: {num_pages}")
        
        current_cluster = None
        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            if page_num % 5 == 0 or page_num == 1:
                logger.info(f"==> Processing Page {page_num} of {num_pages}...")
            
            # Find headings (Trade Groups)
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    # Bold headings are usually UPPERCASE and descriptive
                    if clean_line.isupper() and len(clean_line) > 10 and not any(k in clean_line for k in ['KUCCPS', 'PAGE', 'PORTAL', 'PLACEMEMT']):
                        current_cluster = get_or_create_cluster_cached(clean_line, level)
            
            # Extract and process tables
            tables = page.extract_tables()
            if not tables:
                logger.debug(f"No tables found on page {page_num}")
                continue
                
            page_count = 0
            for table in tables:
                if not table: continue
                if len(table[0]) >= columns_count:
                    page_count += process_table_rows_optimized(table, level, current_cluster, cost_idx, grade_idx, req_idx)
            
            total_extracted += page_count
            if page_count > 0:
                logger.info(f"    Page {page_num} finished: Extracted {page_count} offerings (Total so far: {total_extracted})")
                    
    logger.info(f"SUCCESS: Finished {level_name} Level. Total extracted: {total_extracted}")
    return total_extracted

def main():
    logger.info("====================================================")
    logger.info("🚀 KUCCPS TVET PROGRAMME EXTRACTION STARTED")
    logger.info("====================================================")
    
    base_path = "KUCCPS PROGRAMMES PDF"
    artisan_pdf = os.path.join(base_path, "Artisan Programmes 20-21.pdf")
    craft_pdf = os.path.join(base_path, "Craft Certificate Programmes 20-21.pdf")
    cert_pdf = os.path.join(base_path, "CERTIFICATE_PROGRAMMES.pdf")
    
    total = 0
    
    # 1. Artisan
    total += extract_from_pdf_optimized(artisan_pdf, 'ARTISAN', 5, grade_idx=4)
    
    # 2. Craft Certificate (Level 5)
    total += extract_from_pdf_optimized(craft_pdf, 'CERTIFICATE', 6, grade_idx=4, req_idx=5)
        
    # 3. Certificate (General/Placement list)
    total += extract_from_pdf_optimized(cert_pdf, 'CERTIFICATE', 5, cost_idx=4)
        
    logger.info("====================================================")
    logger.info(f"🏆 MISSION COMPLETE!")
    logger.info(f"Total TVET Offerings Processed: {total}")
    logger.info(f"Full log available at: tvet_extraction.log")
    logger.info("====================================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nExtraction interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"FATAL ERROR: {str(e)}", exc_info=True)
        sys.exit(1)
