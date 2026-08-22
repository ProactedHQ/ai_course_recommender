from django.core.management.base import BaseCommand
from students.models import Subject
from universities.models import Institution, ClusterGroup, ProgrammeLevel, Programme, ProgrammeOffering, CutOffPoint
import json
import os
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds the database with KCSE Subjects, Institutions, Clusters, and Sample Programmes'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Starting Data Seeding...")

        # --- 1. SEED PROGRAMME LEVELS ---
        self.stdout.write("\n📈 Seeding Programme Levels...")
        levels = [
            ("DEGREE", "Degree"),
            ("DIPLOMA", "Diploma/Level 6"),
            ("CERTIFICATE", "Certificate/Level 5"),
            ("ARTISAN", "Artisan/Level 4"),
        ]
        
        level_objects = {}
        for code, name in levels:
            obj, created = ProgrammeLevel.objects.get_or_create(
                name=code,  # The 'name' field holds the choice key (DEGREE, etc.) in our model
                defaults={'name': code} 
            )
            level_objects[code] = obj
            
        self.stdout.write(f"   ✓ Levels seeded: {len(level_objects)}")


        # --- 2. SEED SUBJECTS ---
        self.stdout.write("\n📚 Seeding KCSE Subjects...")
        

        for code, name, cat in subjects:
            Subject.objects.get_or_create(code=code, defaults={'name': name, 'category': cat})
        
        self.stdout.write(f"   ✓ Subjects seeded: {Subject.objects.count()}")

        # --- 3. SEED INSTITUTIONS ---
        self.stdout.write("\n🏫 Seeding Institutions...")
        
        # Fallback list for essential testing if JSON missing
        institutions_payload = [
            {"code": "UON", "name": "University of Nairobi", "institution_type": "PUBLIC_UNIVERSITY", "location": "Nairobi"},
            {"code": "JKUAT", "name": "Jomo Kenyatta University of Agriculture and Technology", "institution_type": "PUBLIC_UNIVERSITY", "location": "Juja"},
            {"code": "KU", "name": "Kenyatta University", "institution_type": "PUBLIC_UNIVERSITY", "location": "Nairobi"},
            {"code": "STRATH", "name": "Strathmore University", "institution_type": "PRIVATE_UNIVERSITY", "location": "Nairobi"},
            {"code": "KABETE", "name": "Kabete National Polytechnic", "institution_type": "TVET", "location": "Nairobi"},
        ]

        # Try load JSON
        json_path = os.path.join(os.path.dirname(__file__), '../../../../scripts/institutions_data.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    scraped = json.load(f)
                    # Map types to new schema choices
                    type_map = {'PUBLIC': 'PUBLIC_UNIVERSITY', 'PRIVATE': 'PRIVATE_UNIVERSITY', 'TVET': 'TVET'}
                    for i in scraped:
                        i['institution_type'] = type_map.get(i.get('institution_type', 'PUBLIC'), 'PUBLIC_UNIVERSITY')
                        institutions_payload.append(i)
                self.stdout.write(f"   📄 Loaded {len(scraped)} from JSON")
            except Exception as e:
                self.stdout.write(f"   ⚠️ Error loading JSON: {e}")

        # Unique by code
        inst_objects = {}
        for inst in institutions_payload:
            obj, _ = Institution.objects.get_or_create(
                code=inst['code'],
                defaults={
                    'name': inst['name'],
                    'institution_type': inst['institution_type'],
                    'location': inst['location']
                }
            )
            inst_objects[inst['code']] = obj

        self.stdout.write(f"   ✓ Institutions seeded: {Institution.objects.count()}")

        # --- 4. SEED CLUSTER GROUPS ---
        self.stdout.write("\n📊 Seeding Clusters...")
        
        # DEGREE CLUSTERS (1-20)
        degree_clusters = [
            ("1", "Law"),
            ("2", "Business, Hospitality & Related"),
            ("3", "Social Sciences, Media Studies, Fine Arts, Film, Animation, Graphics & Related"),
            ("4", "Geosciences & Related"),
            ("5", "Engineering, Engineering Technology & Related"),
            ("6", "Architecture, Building Construction & Related"),
            ("7", "Computing, IT & Related"),
            ("8", "Agribusiness & Related"),
            ("9", "General Science, Biological Sciences, Physics, Chemistry & Related"),
            ("10", "Actuarial Science, Accountancy, Mathematics, Economics, Statistics & Related"),
            ("11", "Interior Design, Fashion Design, Textiles & Related"),
            ("12", "Sport Science & Related"),
            ("13", "Medicine, Health, Veterinary Medicine & Related"),
            ("14", "History, Archeology & Related"),
            ("15", "Agriculture, Animal Health, Food Science, Nutrition Dietetics, Environmental Sciences, Natural Resources & Related"),
            ("16", "Geography & Related"),
            ("17", "French & German"),
            ("18", "Music & Related"),
            ("19", "Education & Related"),
            ("20", "Religious Studies, Theology, Islamic Studies & Related"),
        ]

        degree_level = level_objects["DEGREE"]
        cluster_objects = {}
        
        for code, name in degree_clusters:
            obj, _ = ClusterGroup.objects.get_or_create(
                level=degree_level,
                code=code,
                defaults={'name': name}
            )
            cluster_objects[code] = obj

        self.stdout.write(f"   ✓ Degree Clusters seeded: {len(cluster_objects)}")

        # DIPLOMA CLUSTERS (Level 6)
        diploma_clusters = [
            ("LAW", "Law"),
            ("EDUCATION", "Education & Related"),
            ("BUSINESS", "Business & Related"),
            ("BUILDING", "Building, Construction & Related"),
            ("ENGINEERING", "Engineering, Technology & Related"),
            ("ENVIRONMENTAL", "Environmental Sciences"),
            ("APPLIED_SCI", "Applied Sciences, Health Sciences & Related"),
            ("FOOD_SCI", "Food Science & Related"),
            ("NUTRITION", "Nutrition & Dietetics"),
            ("SOCIAL_SCI", "Social Sciences"),
            ("COMPUTING", "Computing, IT & Related"),
            ("FASHION", "Clothing, Fashion & Textile"),
            ("AGRICULTURE", "Agricultural Sciences & Related"),
            ("NATURAL_SCI", "Natural Sciences & Related"),
            ("TAX", "Tax & Custom Administration"),
            ("MEDIA", "Graphics, Media Studies, Media Production & Related"),
            ("HOSPITALITY", "Hospitality, Hotel, Tourism, & Related"),
            ("TECHNICAL", "Technical Courses"),
            ("ANIMAL_HEALTH", "Animal Health and Related"),
            ("BEAUTY", "Hair Dressing & Beauty Therapy"),
            ("LIBRARY", "Library & Information Science"),
            ("TEACHER_ED", "Primary Teacher Education"),
            ("MUSIC", "Music and Related"),
        ]

        diploma_level = level_objects["DIPLOMA"]
        for code, name in diploma_clusters:
            obj, _ = ClusterGroup.objects.get_or_create(
                level=diploma_level,
                code=code,
                defaults={'name': name}
            )
            cluster_objects[f"DIP_{code}"] = obj

        self.stdout.write(f"   ✓ Diploma Clusters seeded: {len(diploma_clusters)}")

        # CERTIFICATE CLUSTERS (Level 5)
        certificate_clusters = [
            ("BUSINESS", "Business & Related"),
            ("BUILDING", "Building, Construction & Related"),
            ("ENGINEERING", "Engineering Technology & Related"),
            ("HEALTH_SCI", "Health Sciences & Related"),
            ("FOOD_SCI", "Food Science & Related"),
            ("NUTRITION", "Nutrition & Dietetics"),
            ("SOCIAL_SCI", "Social Sciences"),
            ("ENVIRONMENTAL", "Environmental Sciences"),
            ("APPLIED_SCI", "Applied Sciences"),
            ("IT", "IT & Related"),
            ("HOSPITALITY", "Hospitality, Hotel, Tourism, & Related"),
            ("FASHION", "Clothing, Fashion & Textile"),
            ("AGRICULTURE", "Agricultural Sciences & Related"),
            ("NATURAL_SCI", "Natural Sciences & Related"),
            ("MEDIA", "Graphics, Media Studies, Media Production & Related"),
            ("TECHNICAL", "Technical Courses"),
            ("TAX", "Tax & Custom Administration"),
            ("BEAUTY", "Hair Dressing & Beauty Therapy"),
            ("LIBRARY", "Library & Information Sciences"),
            ("LAW", "Law"),
            ("EDUCATION", "Education"),
            ("ANIMAL_HEALTH", "Animal Health"),
        ]

        certificate_level = level_objects["CERTIFICATE"]
        for code, name in certificate_clusters:
            obj, _ = ClusterGroup.objects.get_or_create(
                level=certificate_level,
                code=code,
                defaults={'name': name}
            )
            cluster_objects[f"CERT_{code}"] = obj

        self.stdout.write(f"   ✓ Certificate Clusters seeded: {len(certificate_clusters)}")

        # ARTISAN CLUSTERS (Level 4)
        artisan_clusters = [
            ("BUSINESS", "Business & Related"),
            ("BUILDING", "Building, Construction & Related"),
            ("ENGINEERING", "Engineering & Technology & Related"),
            ("FOOD_SCI", "Food Science & Related"),
            ("SOCIAL_SCI", "Social Sciences"),
            ("APPLIED_SCI", "Applied Sciences"),
            ("IT", "IT & Related"),
            ("HOSPITALITY", "Hospitality, Hotel, Tourism, & Related"),
            ("FASHION", "Clothing, Fashion & Textile"),
            ("AGRICULTURE", "Agricultural Sciences & Related"),
            ("NATURAL_SCI", "Natural Sciences & Related"),
            ("TECHNICAL", "Technical Courses"),
            ("BEAUTY", "Hair Dressing & Beauty Therapy"),
            ("LIBRARY", "Library & Information Sciences"),
        ]

        artisan_level = level_objects["ARTISAN"]
        for code, name in artisan_clusters:
            obj, _ = ClusterGroup.objects.get_or_create(
                level=artisan_level,
                code=code,
                defaults={'name': name}
            )
            cluster_objects[f"ART_{code}"] = obj

        self.stdout.write(f"   ✓ Artisan Clusters seeded: {len(artisan_clusters)}")

        # --- 5. SEED GENERIC PROGRAMMES & OFFERINGS ---
        self.stdout.write("\n🎓 Seeding Sample Programmes & Offerings...")
        
        # 5a. Computer Science (Cluster 7)
        cs_prog, _ = Programme.objects.get_or_create(
            kuccps_code="1266128", # Master/Generic Code
            defaults={
                'name': "Bachelor of Science in Computer Science",
                'level': degree_level,
                'cluster': cluster_objects.get("7"),  # Updated to use simple number
                'description': "Study of computers and computational systems.",
                'job_market_demand': "HIGH"
            }
        )
        
        # Offerings for CS
        if "UON" in inst_objects:
            offering, _ = ProgrammeOffering.objects.get_or_create(
                programme=cs_prog, institution=inst_objects["UON"]
            )
            # Add Cutoffs with new fields
            CutOffPoint.objects.get_or_create(
                offering=offering, 
                year=2023, 
                defaults={
                    'weighted_cluster_points': Decimal('42.155'),
                    'cutoff_type': 'WEIGHTED_POINTS',
                    'capacity': 120,
                    'placed_students': 118
                }
            )
            CutOffPoint.objects.get_or_create(
                offering=offering, 
                year=2022, 
                defaults={
                    'weighted_cluster_points': Decimal('41.882'),
                    'cutoff_type': 'WEIGHTED_POINTS',
                    'capacity': 115,
                    'placed_students': 115
                }
            )

        if "JKUAT" in inst_objects:
            offering, _ = ProgrammeOffering.objects.get_or_create(
                programme=cs_prog, institution=inst_objects["JKUAT"]
            )
            CutOffPoint.objects.get_or_create(
                offering=offering, 
                year=2023, 
                defaults={
                    'weighted_cluster_points': Decimal('41.332'),
                    'cutoff_type': 'WEIGHTED_POINTS',
                    'capacity': 100
                }
            )

        # 5b. Law (Cluster 1)
        law_prog, _ = Programme.objects.get_or_create(
            kuccps_code="1266101",
            defaults={
                'name': "Bachelor of Laws (LL.B)",
                'level': degree_level,
                'cluster': cluster_objects.get("1"),  # Updated to use simple number
                'description': "Study of law and legal systems.",
                'job_market_demand': "HIGH"
            }
        )
        
        if "UON" in inst_objects:
             ProgrammeOffering.objects.get_or_create(programme=law_prog, institution=inst_objects["UON"])
        if "STRATH" in inst_objects:
             ProgrammeOffering.objects.get_or_create(programme=law_prog, institution=inst_objects["STRATH"])

        self.stdout.write(f"   ✓ Generic Programmes seeded: {Programme.objects.count()}")
        self.stdout.write(f"   ✓ Specific Offerings seeded: {ProgrammeOffering.objects.count()}")
        self.stdout.write(f"   ✓ Cutoff Points seeded: {CutOffPoint.objects.count()}")

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully with NEW Schema!'))
        self.stdout.write("="*60)