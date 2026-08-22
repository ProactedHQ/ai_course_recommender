
import os
import pdfplumber
import re
import json
import logging
import sys
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("tvet_pdf_extraction.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def is_valid_trade_heading(line):
    """Only real trade headings (no footers, page numbers, etc.)"""
    clean = line.strip()
    if len(clean) < 15 or not clean.isupper():
        return False
    if any(x in clean for x in ['KUCCPS', 'PAGE', 'PORTAL', 'PLACEMENT', 'OF ', '2020', '2021']):
        return False
    return bool(re.search(r'^(ARTISAN|CRAFT|CERTIFICATE|GRADE III|LEVEL [0-9])', clean))

def extract_from_pdf(pdf_path, level_name, columns_count, grade_idx=None, cost_idx=None, req_idx=None):
    logger.info(f"====================================================")
    logger.info(f"🔍 STARTING EXTRACTION: {level_name} Level")
    logger.info(f"📄 Source: {pdf_path}")
    logger.info(f"====================================================")
    
    data = []
    current_trade = "Uncategorized"
    
    if not os.path.exists(pdf_path):
        logger.warning(f"File not found: {pdf_path}. Skipping.")
        return []

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        
        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            if page_num % 5 == 0 or page_num == 1:
                logger.info(f"Processing Page {page_num} of {num_pages}...")
            
            text = page.extract_text() or ""
            # Improved heading detection
            for line in text.split('\n'):
                if is_valid_trade_heading(line):
                    current_trade = line.strip()
                    logger.debug(f"New Trade Group → {current_trade}")
            
            tables = page.extract_tables()
            page_extracted = 0
            for table in tables:
                if not table or len(table) < 2 or len(table[0]) < columns_count:
                    continue
                
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    
                    code = clean_text(row[1])
                    inst = clean_text(row[2])
                    prog = clean_text(row[3])
                    
                    if not code or len(code) < 5 or not inst or not prog:
                        continue
                    if re.match(r'^PROG|CODE|NO\.', code.upper()):
                        continue  # skip header rows
                    
                    # Parse cost to integer
                    cost = None
                    if cost_idx is not None:
                        cost_str = clean_text(row[cost_idx])
                        cost_str = cost_str.replace(',', '').strip()
                        if cost_str.isdigit():
                            cost = int(cost_str)
                    
                    item = {
                        'level': level_name,
                        'trade': current_trade,           # clean version
                        'cluster': current_trade,         # kept for your compatibility
                        'code': code,
                        'institution': inst,
                        'programme': prog,
                        'min_grade': clean_text(row[grade_idx]) if grade_idx is not None else None,
                        'cost': cost,
                        'requirements': clean_text(row[req_idx]) if req_idx is not None else None
                    }
                    data.append(item)
                    page_extracted += 1
            
            if page_extracted > 0:
                logger.info(f"   - Page {page_num}: Extracted {page_extracted} valid offerings.")
                    
    logger.info(f"FINISHED {level_name}: Total {len(data)} clean items extracted.")
    return data

def main():
    start_time = datetime.now()
    logger.info("🚀 TVET PDF TO JSON START (FIXED VERSION)")
    
    base_path = "KUCCPS PROGRAMMES PDF"
    configs = [
        {"file": "Artisan Programmes 20-21.pdf",      "level": "ARTISAN",    "cols": 5, "grade": 4, "cost": None, "req": None},
        {"file": "Craft Certificate Programmes 20-21.pdf", "level": "CRAFT", "cols": 6, "grade": 4, "cost": None, "req": 5},
        {"file": "CERTIFICATE_PROGRAMMES.pdf",        "level": "CERTIFICATE","cols": 5, "grade": None, "cost": 4, "req": None}
    ]
    
    all_extracted_data = []
    for cfg in configs:
        path = os.path.join(base_path, cfg["file"])
        all_extracted_data.extend(extract_from_pdf(
            path, 
            cfg["level"], 
            cfg["cols"], 
            grade_idx=cfg.get("grade"), 
            cost_idx=cfg.get("cost"), 
            req_idx=cfg.get("req")
        ))
    
    output_file = "tvet_data_extracted.json"
    logger.info(f"Saving {len(all_extracted_data)} total clean items to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, indent=2)
        
    duration = datetime.now() - start_time
    logger.info(f"MISSION COMPLETE: {len(all_extracted_data)} clean items saved in {duration}")

if __name__ == "__main__":
    main()