
import os
import sys
import django
import json

# Add project root to sys.path
sys.path.append(os.getcwd())
# Add apps to sys.path
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.models import ClusterGroup
from apps.students.models import Subject
from apps.universities.utils.requirement_parser import parse_all_cluster_requirements
from apps.universities.utils.subject_matcher import match_requirement

def test_requirement_parsing():
    print("\n=== CLUSTER REQUIREMENT PARSING VERIFICATION ===")
    clusters = ClusterGroup.objects.filter(level__name='DEGREE').order_by('code')
    
    for cluster in clusters:
        print(f"\nCluster {cluster.code}: {cluster.name}")
        print(f" Raw: 1:[{cluster.subject_1}] 2:[{cluster.subject_2}] 3:[{cluster.subject_3}] 4:[{cluster.subject_4}]")
        
        parsed = parse_all_cluster_requirements(cluster)
        for i, p in enumerate(parsed, 1):
            if p['type'] == 'specific':
                details = f"Subjects: {p['subjects']}, Min Grade: {p.get('min_grade')}"
            elif p['type'] == 'group':
                details = f"Groups: {p['groups']}, Min Grade: {p.get('min_grade')}"
            else:
                details = f"Unknown Source: {p.get('raw_text')}"
            
            print(f"  - Req {i}: {p['type']} -> {details}")

def test_matching_logic():
    print("\n=== SUBJECT MATCHING LOGIC VERIFICATION ===")
    
    # Generic student profile
    student_grades = {
        '101': 'B+', # English
        '102': 'A-', # Kiswahili
        '121': 'A',  # Math A
        '231': 'B',  # Physics
        '233': 'A-', # Chemistry
        '311': 'B',  # Geography
        '440': 'A',  # Computer Studies
        '571': 'B+', # Business Studies
    }
    
    subject_cache = {s.code: s for s in Subject.objects.all()}
    
    # Test Cluster 5 (Engineering) - Requirements: MAT A, PHY, CHE, BIO/GP3/GP4/GP5
    cluster_5 = ClusterGroup.objects.get(code='5', level__name='DEGREE')
    reqs_5 = parse_all_cluster_requirements(cluster_5)
    
    print(f"\nTesting Match for Cluster 5: {cluster_5.name}")
    for i, req in enumerate(reqs_5, 1):
        matches = match_requirement(student_grades, req, subject_cache)
        match_str = ", ".join([f"{m[0]}({m[1]})" for m in matches])
        print(f" - Req {i} ({req['type']}): Found {len(matches)} matches: [{match_str}]")

def main():
    test_requirement_parsing()
    test_matching_logic()

if __name__ == "__main__":
    main()
