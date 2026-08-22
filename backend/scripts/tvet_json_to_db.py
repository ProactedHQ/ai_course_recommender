import os
import sys
import django
import json
import logging
from decimal import Decimal
from django.db import transaction
from datetime import datetime

# Add project root and apps to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.models import Institution, Programme, ProgrammeLevel, ProgrammeOffering, ProgrammeRequirement, ClusterGroup

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("tvet_json_load.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@transaction.atomic
def load_json(json_path="tvet_data_extracted.json"):
    start_time = datetime.now()
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return

    logger.info("====================================================")
    logger.info(f"STARTING OPTIMIZED BULK LOAD: {json_path}")
    logger.info("====================================================")

    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    logger.info(f"Total items in clean JSON: {len(items)}")
    
    # 1. Levels
    levels = {
        'ARTISAN': ProgrammeLevel.objects.get_or_create(name='ARTISAN')[0],
        'CRAFT': ProgrammeLevel.objects.get_or_create(name='CRAFT')[0],
        'CERTIFICATE': ProgrammeLevel.objects.get_or_create(name='CERTIFICATE')[0]
    }
    
    # 2. Institutions - Bulk + Full Refresh
    all_inst_names = list(set(item['institution'] for item in items))
    existing_insts = {inst.name: inst for inst in Institution.objects.filter(name__in=all_inst_names)}
    
    new_insts = [
        Institution(
            name=name,
            code=f"TVET-{abs(hash(name)) % 1000000}",
            institution_type='TVET'
        )
        for name in all_inst_names if name not in existing_insts
    ]
    
    if new_insts:
        logger.info(f"Creating {len(new_insts)} new TVET Institutions...")
        Institution.objects.bulk_create(new_insts, ignore_conflicts=True)
    
    # Full re-fetch (safest)
    existing_insts = {inst.name: inst for inst in Institution.objects.filter(name__in=all_inst_names)}
    
    # 3. ClusterGroups - Fixed caching
    unique_groups = set(
        (item.get('trade') or item.get('cluster') or "Uncategorized", item['level'])
        for item in items
    )
    
    existing_groups = {(g.name, g.level.name): g for g in ClusterGroup.objects.filter(
        level__name__in=levels.keys()
    )}
    
    new_groups = [
        ClusterGroup(name=name, level=levels[level_name])
        for name, level_name in unique_groups
        if (name, level_name) not in existing_groups
    ]
    
    if new_groups:
        logger.info(f"Creating {len(new_groups)} new ClusterGroups...")
        ClusterGroup.objects.bulk_create(new_groups, ignore_conflicts=True)
    
    # Full re-fetch for clusters (this fixes the bug)
    existing_groups = {(g.name, g.level.name): g for g in ClusterGroup.objects.filter(
        level__name__in=levels.keys()
    )}

    # 4. Programmes - Bulk Create + Bulk Update
    all_codes = [item['code'] for item in items]
    existing_programmes = {p.kuccps_code: p for p in Programme.objects.filter(kuccps_code__in=all_codes)}
    
    to_create = []
    to_update = []
    
    seen_in_batch = set()
    for item in items:
        code = item['code']
        if code in seen_in_batch:
            continue
        seen_in_batch.add(code)
        
        level = levels[item['level']]
        trade_name = item.get('trade') or item.get('cluster') or "Uncategorized"
        cluster = existing_groups.get((trade_name, item['level']))
        
        props = {
            'name': item['programme'],
            'level': level,
            'cluster': cluster,
            'minimum_mean_grade': item.get('min_grade')
        }
        
        if item['code'] in existing_programmes:
            prog = existing_programmes[item['code']]
            prog.name = props['name']
            prog.level = props['level']
            prog.cluster = props['cluster']
            prog.minimum_mean_grade = props['minimum_mean_grade']
            to_update.append(prog)
        else:
            to_create.append(Programme(kuccps_code=item['code'], **props))

    if to_create:
        logger.info(f"Creating {len(to_create)} new Programmes...")
        Programme.objects.bulk_create(to_create, batch_size=500)
    
    if to_update:
        logger.info(f"Updating {len(to_update)} existing Programmes...")
        Programme.objects.bulk_update(to_update, ['name', 'level', 'cluster', 'minimum_mean_grade'], batch_size=500)

    # 5. Re-fetch programmes for FKs
    all_programmes = {p.kuccps_code: p for p in Programme.objects.filter(kuccps_code__in=all_codes)}
    
    # 6. Offerings & Requirements (delete old + bulk create)
    to_create_offerings = []
    to_create_requirements = []
    
    seen_offerings = set()
    seen_requirements = set()
    for item in items:
        prog = all_programmes.get(item['code'])
        inst = existing_insts.get(item['institution'])
        if not prog or not inst:
            continue
            
        # Deduplicate offerings
        offering_key = (prog.id, inst.id)
        if offering_key in seen_offerings:
            continue
        seen_offerings.add(offering_key)

        cost = None
        if item.get('cost'):
            try:
                cost = Decimal(str(item['cost']).replace(',', ''))
            except:
                cost = None
                
        to_create_offerings.append(ProgrammeOffering(
            programme=prog,
            institution=inst,
            cost=cost
        ))
        
        # Deduplicate requirements
        if item.get('requirements'):
            req_key = (prog.id, item['requirements'])
            if req_key in seen_requirements:
                continue
            seen_requirements.add(req_key)
            
            to_create_requirements.append(ProgrammeRequirement(
                programme=prog,
                description=item['requirements']
            ))

    if to_create_offerings:
        logger.info(f"Creating {len(to_create_offerings)} ProgrammeOfferings...")
        ProgrammeOffering.objects.filter(programme__kuccps_code__in=all_codes).delete()
        ProgrammeOffering.objects.bulk_create(to_create_offerings, batch_size=500)
    
    if to_create_requirements:
        logger.info(f"Creating {len(to_create_requirements)} ProgrammeRequirements...")
        ProgrammeRequirement.objects.filter(programme__kuccps_code__in=all_codes).delete()
        ProgrammeRequirement.objects.bulk_create(to_create_requirements, batch_size=500)

    duration = datetime.now() - start_time
    logger.info("====================================================")
    logger.info(f"BULK LOAD COMPLETE! Duration: {duration}")
    logger.info(f"   Institutions: {len(existing_insts)} | ClusterGroups: {len(existing_groups)}")
    logger.info(f"   Programmes: {len(all_programmes)} | Offerings: {len(to_create_offerings)}")
    logger.info("====================================================")

if __name__ == "__main__":
    load_json()  