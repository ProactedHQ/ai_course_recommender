from django.core.management.base import BaseCommand
from django.db import transaction
from students.models import Subject
from universities.models import (
    Institution, ClusterGroup, ProgrammeLevel, Programme, 
    ProgrammeOffering, CutOffPoint, SubClusterGroup
)
import json
import os
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path


class Command(BaseCommand):
    help = 'Comprehensive database seeding from all extracted JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview seeding without saving to database',
        )

    def __init__(self):
        super().__init__()
        self.dry_run = False
        self.stats = {
            'subjects': 0,
            'levels': 0,
            'institutions': 0,
            'degree_clusters': 0,
            'degree_subclusters': 0,
            'tvet_clusters': 0,
            'programmes': 0,
            'offerings': 0,
            'cutoffs': 0,
            'errors': []
        }

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved"))
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("COMPREHENSIVE DATABASE SEEDING"))
        self.stdout.write("Using separate transactions per phase for reliability")
        self.stdout.write("=" * 70)

        try:
            # Phase 1: Foundation - separate transaction
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("PHASE 1: FOUNDATION DATA"))
            self.stdout.write("=" * 70)
            with transaction.atomic():
                self.seed_subjects()
                self.seed_programme_levels()
                self.seed_institutions()
                if self.dry_run:
                    raise Exception("Dry run phase 1")
            self.stdout.write(self.style.SUCCESS("   Phase 1 committed successfully!"))

            # Phase 2: Degree Clusters - separate transaction
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("PHASE 2: DEGREE CLUSTERS"))
            self.stdout.write("=" * 70)
            with transaction.atomic():
                self.seed_degree_clusters()
                self.seed_degree_subclusters()
                if self.dry_run:
                    raise Exception("Dry run phase 2")
            self.stdout.write(self.style.SUCCESS("   Phase 2 committed successfully!"))

            # Phase 3: TVET Clusters - separate transaction
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("PHASE 3: TVET CLUSTERS"))
            self.stdout.write("=" * 70)
            with transaction.atomic():
                self.seed_tvet_clusters()
                if self.dry_run:
                    raise Exception("Dry run phase 3")
            self.stdout.write(self.style.SUCCESS("   Phase 3 committed successfully!"))

            # Phase 4: Programmes & Offerings - separate transaction
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("PHASE 4: PROGRAMMES & OFFERINGS"))
            self.stdout.write("=" * 70)
            with transaction.atomic():
                self.seed_programmes()
                if self.dry_run:
                    raise Exception("Dry run phase 4")
            self.stdout.write(self.style.SUCCESS("   Phase 4 committed successfully!"))

            # Phase 5: Cutoffs - separate transaction
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("PHASE 5: CUTOFF POINTS"))
            self.stdout.write("=" * 70)
            with transaction.atomic():
                self.seed_cutoffs()
                if self.dry_run:
                    raise Exception("Dry run phase 5")
            self.stdout.write(self.style.SUCCESS("   Phase 5 committed successfully!"))

        except Exception as e:
            if "Dry run" not in str(e):
                self.stdout.write(self.style.ERROR(f"\nERROR: {e}"))
                self.stdout.write(self.style.WARNING("\nPartial seeding may have occurred. Check database state."))

        # Print summary
        self.print_summary()

    def seed_subjects(self):
        """Seed KCSE subjects using bulk_create for performance"""
        self.stdout.write("\n[1/5] Seeding Subjects...")
        
        # KCSE Subjects (31 subjects from seed_data.py structure)
        subjects_data = [
            # Group 1 - Compulsory
            ('101', 'English', 'GP1'),
            ('102', 'Kiswahili', 'GP1'),
            ('121', 'Mathematics Alternative A', 'GP1'),
            ('122', 'Mathematics Alternative B', 'GP1'),
            
            # Group 2 - Sciences
            ('231', 'Physics', 'GP2'),
            ('232', 'Biology', 'GP2'),
            ('233', 'Chemistry', 'GP2'),
            ('236', 'Home Science', 'GP2'),
            ('245', 'Agriculture', 'GP2'),
            ('246', 'Biological Sciences', 'GP2'),
            ('247', 'Physical Sciences', 'GP2'),
            
            # Group 3 - Humanities
            ('311', 'Geography', 'GP3'),
            ('312', 'History and Government', 'GP3'),
            ('313', 'Christian Religious Education', 'GP3'),
            ('314', 'Islamic Religious Education', 'GP3'),
            ('315', 'Hindu Religious Education', 'GP3'),
            
            # Group 4 - Technical & Applied
            ('433', 'Aviation Technology', 'GP4'),
            ('440', 'Computer Studies', 'GP4'),
            ('442', 'Electricity', 'GP4'),
            ('443', 'Power Mechanics', 'GP4'),
            ('444', 'Metalwork', 'GP4'),
            ('445', 'Building Construction', 'GP4'),
            ('446', 'Woodwork', 'GP4'),
            ('447', 'Drawing and Design', 'GP4'),
            ('448', 'Art and Design', 'GP4'),
            
            # Group 5 - Business & Languages
            ('565', 'French', 'GP5'),
            ('566', 'German', 'GP5'),
            ('571', 'Business Studies', 'GP5'),
            ('574', 'Music', 'GP5'),
            ('579', 'Arabic', 'GP5'),
            ('511', 'Accounting', 'GP5'),
        ]

        if not self.dry_run:
            # Use bulk_create for much faster insertion
            subjects_to_create = [
                Subject(code=code, name=name, category=category)
                for code, name, category in subjects_data
            ]
            Subject.objects.bulk_create(subjects_to_create, ignore_conflicts=True)
        
        self.stats['subjects'] = len(subjects_data)
        self.stdout.write(self.style.SUCCESS(f"   [OK] Subjects seeded: {self.stats['subjects']}"))

    def seed_programme_levels(self):
        """Seed programme levels"""
        self.stdout.write("\n[2/5] Seeding Programme Levels...")
        
        levels = [
            ("DEGREE", "Degree"),
            ("DIPLOMA", "Diploma/Level 6"),
            ("CERTIFICATE", "Certificate/Level 5"),
            ("ARTISAN", "Artisan/Level 4"),
        ]

        for code, name in levels:
            if not self.dry_run:
                ProgrammeLevel.objects.get_or_create(name=code)
            self.stats['levels'] += 1

        self.stdout.write(self.style.SUCCESS(f"   [OK] Programme levels seeded: {self.stats['levels']}"))

    def seed_institutions(self):
        """Seed institutions from institutions_data.json using bulk_create"""
        self.stdout.write("\n[3/5] Seeding Institutions...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'scripts' / 'institutions_data.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"   [ERROR] institutions_data.json not found at {json_path}"))
            self.stats['errors'].append(f"institutions_data.json not found")
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                institutions = json.load(f)
            
            # Map old types to new schema
            type_map = {
                'PUBLIC': 'PUBLIC_UNIVERSITY',
                'PRIVATE': 'PRIVATE_UNIVERSITY',
                'TVET': 'TVET'
            }

            if not self.dry_run:
                # Use bulk_create for faster insertion
                institutions_to_create = []
                for inst in institutions:
                    inst_type = type_map.get(inst.get('institution_type', 'PUBLIC'), 'PUBLIC_UNIVERSITY')
                    institutions_to_create.append(
                        Institution(
                            code=inst['code'],
                            name=inst['name'],
                            institution_type=inst_type,
                            location=inst.get('location', 'Kenya')
                        )
                    )
                
                # Batch create in chunks to avoid memory issues
                batch_size = 100
                for i in range(0, len(institutions_to_create), batch_size):
                    batch = institutions_to_create[i:i+batch_size]
                    Institution.objects.bulk_create(batch, ignore_conflicts=True)
                    if (i + batch_size) % 250 == 0:
                        self.stdout.write(f"      ... {min(i + batch_size, len(institutions_to_create))}/{len(institutions_to_create)} processed")
            
            self.stats['institutions'] = len(institutions)
            self.stdout.write(self.style.SUCCESS(f"   [OK] Institutions seeded: {self.stats['institutions']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error loading institutions: {e}"))
            self.stats['errors'].append(f"Institution seeding error: {e}")

    def seed_degree_clusters(self):
        """Seed degree clusters from degree_clusters_MANUAL.json"""
        self.stdout.write("\n[4/5] Seeding Degree Clusters...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'degree_clusters_MANUAL.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"   [ERROR] degree_clusters_MANUAL.json not found"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            degree_level = ProgrammeLevel.objects.get(name='DEGREE') if not self.dry_run else None

            for cluster in data.get('clusters', []):
                code = cluster.get('code')
                name = cluster.get('name')
                
                if not self.dry_run:
                    ClusterGroup.objects.get_or_create(
                        level=degree_level,
                        code=code,
                        defaults={
                            'name': name,
                            'subject_1': cluster.get('subject_1'),
                            'subject_2': cluster.get('subject_2'),
                            'subject_3': cluster.get('subject_3'),
                            'subject_4': cluster.get('subject_4'),
                        }
                    )
                self.stats['degree_clusters'] += 1

            self.stdout.write(self.style.SUCCESS(f"   [OK] Degree clusters seeded: {self.stats['degree_clusters']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error: {e}"))
            self.stats['errors'].append(f"Degree cluster error: {e}")

    def seed_degree_subclusters(self):
        """Seed degree subclusters from degree_clusters_MANUAL.json"""
        self.stdout.write("\n[5/5] Seeding Degree Subclusters...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'degree_clusters_MANUAL.json'
        
        if not json_path.exists():
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for cluster_data in data.get('clusters', []):
                cluster_code = cluster_data.get('code')
                
                if not self.dry_run:
                    degree_level = ProgrammeLevel.objects.get(name='DEGREE')
                    cluster = ClusterGroup.objects.get(level=degree_level, code=cluster_code)
                else:
                    cluster = None

                for subcluster in cluster_data.get('subclusters', []):
                    sub_code = subcluster.get('code')
                    
                    if not self.dry_run:
                        SubClusterGroup.objects.get_or_create(
                            code=sub_code,
                            defaults={
                                'cluster': cluster,
                                'subject_1': subcluster.get('subject_1'),
                                'subject_2': subcluster.get('subject_2'),
                                'subject_3': subcluster.get('subject_3'),
                                'subject_4': subcluster.get('subject_4'),
                            }
                        )
                    self.stats['degree_subclusters'] += 1

            self.stdout.write(self.style.SUCCESS(f"   [OK] Degree subclusters seeded: {self.stats['degree_subclusters']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error: {e}"))
            self.stats['errors'].append(f"Subcluster error: {e}")

    def seed_tvet_clusters(self):
        """Seed TVET clusters from tvet_clusters_MANUAL.json"""
        self.stdout.write("\n[6/6] Seeding TVET Clusters...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'tvet_clusters_MANUAL.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"   [ERROR] tvet_clusters_MANUAL.json not found"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get programme levels
            if not self.dry_run:
                diploma_level = ProgrammeLevel.objects.get(name='DIPLOMA')
                certificate_level = ProgrammeLevel.objects.get(name='CERTIFICATE')
                artisan_level = ProgrammeLevel.objects.get(name='ARTISAN')

            for cluster in data.get('clusters', []):
                section = cluster.get('section', 'STANDARD')
                cluster_num = cluster.get('cluster_number')
                category = cluster.get('category')
                
                # Determine prefix based on section
                if section == 'KNEC EXAMINATION':
                    prefix = 'KNEC'
                elif section == 'INTERNAL EXAMINERS':
                    prefix = 'INTERNAL'
                else:
                    prefix = 'TVET'
                
                # Handle subcategories vs levels
                if 'subcategories' in cluster:
                    # Has subcategories (e.g., Architecture)
                    for subcat in cluster['subcategories']:
                        subcat_name = subcat['subcategory_name']
                        self._seed_tvet_cluster_levels(
                            f"{prefix}-{cluster_num}-{subcat_name[:3].upper()}",
                            f"{category} ({subcat_name})",
                            subcat['levels'],
                            diploma_level if not self.dry_run else None,
                            certificate_level if not self.dry_run else None,
                            artisan_level if not self.dry_run else None
                        )
                elif 'levels' in cluster:
                    # Check for variants within levels
                    has_variants = any('variants' in level for level in cluster['levels'])
                    
                    if has_variants:
                        # Create separate cluster for each variant
                        for level in cluster['levels']:
                            if 'variants' in level:
                                for variant in level['variants']:
                                    variant_name = variant['variant_name']
                                    clean_variant = variant_name.replace(' ', '-')
                                    self._seed_single_tvet_cluster(
                                        f"{prefix}-{cluster_num}-{clean_variant[:10].upper()}",
                                        f"{category} ({level['level']}: {variant_name})",
                                        level['level'],
                                        level['mean_grade'],
                                        variant['subject_requirements'],
                                        diploma_level if not self.dry_run else None,
                                        certificate_level if not self.dry_run else None,
                                        artisan_level if not self.dry_run else None
                                    )
                            else:
                                # No variants, create normally
                                self._seed_single_tvet_cluster(
                                    f"{prefix}-{cluster_num}",
                                    f"{category} ({level['level']})",
                                    level['level'],
                                    level['mean_grade'],
                                    level.get('subject_requirements', []),
                                    diploma_level if not self.dry_run else None,
                                    certificate_level if not self.dry_run else None,
                                    artisan_level if not self.dry_run else None
                                )
                    else:
                        # No variants, create normally
                        self._seed_tvet_cluster_levels(
                            f"{prefix}-{cluster_num}",
                            category,
                            cluster['levels'],
                            diploma_level if not self.dry_run else None,
                            certificate_level if not self.dry_run else None,
                            artisan_level if not self.dry_run else None
                        )

            self.stdout.write(self.style.SUCCESS(f"   [OK] TVET clusters seeded: {self.stats['tvet_clusters']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error: {e}"))
            self.stats['errors'].append(f"TVET cluster error: {e}")

    def _seed_tvet_cluster_levels(self, base_code, category, levels, diploma_level, certificate_level, artisan_level):
        """Helper to seed TVET clusters for each level"""
        for level in levels:
            level_name = level['level']
            mean_grade = level.get('mean_grade')
            requirements = level.get('subject_requirements', [])
            
            self._seed_single_tvet_cluster(
                f"{base_code}-{level_name[:4].upper()}",
                f"{category} ({level_name})",
                level_name,
                mean_grade,
                requirements,
                diploma_level,
                certificate_level,
                artisan_level
            )

    def _seed_single_tvet_cluster(self, code, name, level_name, mean_grade, requirements, diploma_level, certificate_level, artisan_level):
        """Helper to seed a single TVET cluster"""
        # Determine the programme level
        if 'Diploma' in level_name:
            prog_level = diploma_level
        elif 'Certificate' in level_name:
            prog_level = certificate_level
        elif 'Artisan' in level_name:
            prog_level = artisan_level
        else:
            prog_level = diploma_level  # Default

        # Extract first 4 subject requirements
        subjects = [None, None, None, None]
        for i, req in enumerate(requirements[:4]):
            if i < 4:
                subject = req.get('subject', '')
                grade = req.get('minimum_grade', '')
                if subject:
                    subjects[i] = f"{subject} - {grade}" if grade else subject

        if not self.dry_run and prog_level:
            ClusterGroup.objects.get_or_create(
                level=prog_level,
                code=code,
                defaults={
                    'name': name,
                    'subject_1': subjects[0],
                    'subject_2': subjects[1],
                    'subject_3': subjects[2],
                    'subject_4': subjects[3],
                }
            )
        self.stats['tvet_clusters'] += 1

    def seed_programmes(self):
        """Seed programmes and offerings using bulk_create for performance"""
        self.stdout.write("\n[7/7] Seeding Programmes & Offerings...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'degree_programmes_full.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"   [ERROR] degree_programmes_full.json not found"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load programme-to-cluster mapping
            programme_cluster_map = self._build_programme_cluster_map()

            if not self.dry_run:
                degree_level = ProgrammeLevel.objects.get(name='DEGREE')
                
                total_records = len(data.get('data', []))
                self.stdout.write(f"   Processing {total_records} programme records...")
                
                # Build institution cache
                institution_cache = {}
                for inst in Institution.objects.all():
                    institution_cache[inst.code] = inst
                    institution_cache[inst.name] = inst
                
                # Collect unique programmes and offerings
                programmes_to_create = {}
                offerings_to_create = []
                
                for idx, record in enumerate(data.get('data', []), 1):
                    kuccps_code = record.get('kuccps_code')
                    programme_name = record.get('programme_name')
                    institution_name = record.get('institution_name')
                    inst_code = kuccps_code[:4]
                    
                    if idx % 500 == 0:
                        self.stdout.write(f"      ... {idx}/{total_records} processed")
                    
                    # Get institution (prefer by name, fallback to code)
                    institution = institution_cache.get(institution_name) or institution_cache.get(inst_code)
                    if not institution:
                        continue  # Skip if institution not found
                    
                    # Find cluster/subcluster
                    cluster, subcluster = self._find_matching_cluster(programme_name, programme_cluster_map)
                    
                    # Collect programme data
                    if kuccps_code not in programmes_to_create:
                        programmes_to_create[kuccps_code] = {
                            'kuccps_code': kuccps_code,
                            'name': programme_name,
                            'level': degree_level,
                            'cluster': cluster,
                            'sub_cluster': subcluster,
                        }
                    
                    # Collect offering data (programme + institution pair)
                    offerings_to_create.append((kuccps_code, institution.code))
                
                # Bulk create programmes
                self.stdout.write(f"   Creating {len(programmes_to_create)} unique programmes...")
                programmes_objs = [Programme(**prog_data) for prog_data in programmes_to_create.values()]
                Programme.objects.bulk_create(programmes_objs, batch_size=200, ignore_conflicts=True)
                self.stats['programmes'] = len(programmes_to_create)
                
                # Get programme objects for offerings
                programme_obj_cache = {p.kuccps_code: p for p in Programme.objects.all()}
                
                # Bulk create offerings
                self.stdout.write(f"   Creating {len(offerings_to_create)} programme offerings...")
                offerings_objs = []
                for kuccps_code, inst_code in offerings_to_create:
                    programme = programme_obj_cache.get(kuccps_code)
                    institution = institution_cache.get(inst_code)
                    if programme and institution:
                        offerings_objs.append(ProgrammeOffering(
                            programme=programme,
                            institution=institution
                        ))
                
                ProgrammeOffering.objects.bulk_create(offerings_objs, batch_size=200, ignore_conflicts=True)
                self.stats['offerings'] = len(offerings_objs)
            else:
                # Dry run
                self.stats['programmes'] = len(set(r.get('kuccps_code') for r in data.get('data', [])))
                self.stats['offerings'] = len(data.get('data', []))

            self.stdout.write(self.style.SUCCESS(f"   [OK] Programmes seeded: {self.stats['programmes']}"))
            self.stdout.write(self.style.SUCCESS(f"   [OK] Offerings seeded: {self.stats['offerings']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error: {e}"))
            self.stats['errors'].append(f"Programme seeding error: {e}")

    def _build_programme_cluster_map(self):
        """Build a map of programme names to clusters/subclusters"""
        mapping = {}
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'degree_clusters_MANUAL.json'
        
        if not json_path.exists():
            return mapping

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for cluster in data.get('clusters', []):
                cluster_code = cluster.get('code')
                
                for subcluster in cluster.get('subclusters', []):
                    subcluster_code = subcluster.get('code')
                    
                    for programme_name in subcluster.get('programmes', []):
                        mapping[programme_name.lower().strip()] = {
                            'cluster_code': cluster_code,
                            'subcluster_code': subcluster_code
                        }

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ! Could not build programme map: {e}"))

        return mapping

    def _find_matching_cluster(self, programme_name, programme_map):
        """Find matching cluster using fuzzy name matching"""
        if not programme_map:
            return None, None

        # Try exact match first
        programme_lower = programme_name.lower().strip()
        if programme_lower in programme_map:
            match = programme_map[programme_lower]
            if not self.dry_run:
                degree_level = ProgrammeLevel.objects.get(name='DEGREE')
                cluster = ClusterGroup.objects.filter(level=degree_level, code=match['cluster_code']).first()
                subcluster = SubClusterGroup.objects.filter(code=match['subcluster_code']).first()
                return cluster, subcluster
            return None, None

        # Try fuzzy matching
        best_match = None
        best_ratio = 0.85  # Threshold for fuzzy matching

        for mapped_name, info in programme_map.items():
            ratio = SequenceMatcher(None, programme_lower, mapped_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = info

        if best_match and not self.dry_run:
            degree_level = ProgrammeLevel.objects.get(name='DEGREE')
            cluster = ClusterGroup.objects.filter(level=degree_level, code=best_match['cluster_code']).first()
            subcluster = SubClusterGroup.objects.filter(code=best_match['subcluster_code']).first()
            return cluster, subcluster

        return None, None

    def seed_cutoffs(self):
        """Seed cutoff points from degree_cutoffs_extracted.json"""
        self.stdout.write("\n[8/8] Seeding Cutoff Points...")
        
        json_path = Path(__file__).parent.parent.parent.parent.parent / 'extraction_output' / 'degree_cutoffs_extracted.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"   [ERROR] degree_cutoffs_extracted.json not found"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for record in data.get('data', []):
                kuccps_code = record.get('kuccps_code')
                inst_code = kuccps_code[:4]
                cutoffs = record.get('cutoffs', {})

                if not self.dry_run:
                    # Get programme and institution
                    try:
                        programme = Programme.objects.get(kuccps_code=kuccps_code)
                        institution = Institution.objects.get(code=inst_code)
                        offering = ProgrammeOffering.objects.get(programme=programme, institution=institution)
                    except (Programme.DoesNotExist, Institution.DoesNotExist, ProgrammeOffering.DoesNotExist):
                        continue

                # Create cutoffs for each year
                for year, points in cutoffs.items():
                    try:
                        year_int = int(year)
                        points_decimal = Decimal(str(points))
                        
                        if not self.dry_run:
                            CutOffPoint.objects.get_or_create(
                                offering=offering,
                                year=year_int,
                                defaults={
                                    'weighted_cluster_points': points_decimal,
                                    'cutoff_type': 'WEIGHTED_POINTS'
                                }
                            )
                        self.stats['cutoffs'] += 1
                    except (ValueError, TypeError) as e:
                        continue

            self.stdout.write(self.style.SUCCESS(f"   [OK] Cutoff points seeded: {self.stats['cutoffs']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [ERROR] Error: {e}"))
            self.stats['errors'].append(f"Cutoff seeding error: {e}")

    def print_summary(self):
        """Print seeding summary"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("SEEDING SUMMARY"))
        self.stdout.write("=" * 70)
        
        self.stdout.write(f"\nSubjects:              {self.stats['subjects']}")
        self.stdout.write(f"Programme Levels:      {self.stats['levels']}")
        self.stdout.write(f"Institutions:          {self.stats['institutions']}")
        self.stdout.write(f"Degree Clusters:       {self.stats['degree_clusters']}")
        self.stdout.write(f"Degree Subclusters:    {self.stats['degree_subclusters']}")
        self.stdout.write(f"TVET Clusters:         {self.stats['tvet_clusters']}")
        self.stdout.write(f"Programmes:            {self.stats['programmes']}")
        self.stdout.write(f"Programme Offerings:   {self.stats['offerings']}")
        self.stdout.write(f"Cutoff Points:         {self.stats['cutoffs']}")
        
        if self.stats['errors']:
            self.stdout.write(self.style.ERROR(f"\nErrors: {len(self.stats['errors'])}"))
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        self.stdout.write("\n" + "=" * 70)
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN COMPLETE - No data was saved"))
        else:
            self.stdout.write(self.style.SUCCESS("DATABASE SEEDING COMPLETE!"))
        self.stdout.write("=" * 70 + "\n")
