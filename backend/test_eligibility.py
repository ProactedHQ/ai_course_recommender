#!/usr/bin/env python
"""
Test KCSE Cluster Points Calculator

Tests the eligibility filter with sample student data.
"""
import os
import sys
import django

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

# Import after Django setup
from apps.universities.utils.eligibility_filter import get_eligible_programmes, filter_eligible_only
from apps.universities.utils.points_calculator import calculate_aggregate_points
from apps.universities.utils.requirement_parser import CODE_TO_NAME


# Sample student grades (using subject codes)
# This student has strong performance in sciences/math
sample_student_grades = {
    '101': 'B+',   # English
    '102': 'C+',   # Kiswahili
    '121': 'A-',   # Mathematics Alternative A
    '232': 'A',    # Biology
    '233': 'B+',   # Chemistry
    '231': 'B',    # Physics
    '311': 'C+',   # Geography
    '571': 'B-',   # Business Studies
}

print("="*70)
print("KCSE CLUSTER POINTS CALCULATOR - TEST")
print("="*70)

print("\n📝 Student Grades:")
print("-" * 70)
for code, grade in sample_student_grades.items():
    subject_name = CODE_TO_NAME.get(code, code)
    print(f"  {subject_name:40} {grade}")


# Calculate aggregate
aggregate = calculate_aggregate_points(sample_student_grades)
print(f"\n📊 Total Aggregate Points: {aggregate}/84")

print("\n🔍 Finding eligible programmes...")
print("-" * 70)

# Get all programmes (eligible and not eligible)
all_programmes = get_eligible_programmes(sample_student_grades, target_year=2024)

print(f"\n✅ Total programmes analyzed: {len(all_programmes)}")

# Filter to only eligible
eligible = filter_eligible_only(all_programmes)

print(f"✅ Eligible programmes (student meets cutoff): {len(eligible)}")
print(f"❌ Not eligible (below cutoff): {len(all_programmes) - len(eligible)}")

# Show top 10 eligible programmes
if eligible:
    print("\n" + "="*70)
    print("TOP 10 ELIGIBLE PROGRAMMES")
    print("="*70)
    
    for i, prog_dict in enumerate(eligible[:10], 1):
        prog = prog_dict['programme']
        inst = prog_dict['institution']
        cluster_subjects = prog_dict['cluster_subjects']
        
        print(f"\n{i}. {prog.name}")
        print(f"   Institution: {inst.name}")
        print(f"   Cluster: {prog_dict['cluster'].name}")
        print(f"   Subcluster: {prog_dict['subcluster'].code}")
        print(f"   Student Points: {prog_dict['student_points']}")
        print(f"   Cutoff Points: {prog_dict['cutoff_points']} ({prog_dict['cutoff_year']})")
        print(f"   Margin: +{prog_dict['points_margin']}")
        print(f"   Cluster Subjects Used:")
        for code, grade, points in cluster_subjects:
            subj_name = CODE_TO_NAME.get(code, code)
            print(f"      - {subj_name} ({grade}): {points} pts")
else:
    print("\n❌ No eligible programmes found for this student.")
    print("\nShowing why student was disqualified for first 5 clusters:")
    
    # Get unique clusters that were checked
    from apps.universities.models import ClusterGroup, ProgrammeLevel
    degree_level = ProgrammeLevel.objects.get(name='DEGREE')
    clusters = ClusterGroup.objects.filter(level=degree_level)[:5]
    
    for cluster in clusters:
        from apps.universities.utils.requirement_parser import parse_all_cluster_requirements
        from apps.universities.utils.subject_matcher import find_best_subject_combination
        
        reqs = parse_all_cluster_requirements(cluster)
        cluster_subjects = find_best_subject_combination(sample_student_grades, reqs)
        
        if cluster_subjects:
            from apps.universities.utils.points_calculator import calculate_cluster_points
            points = calculate_cluster_points(cluster_subjects, aggregate)
            print(f"\n  ✅ {cluster.name}: {points} points")
        else:
            print(f"\n  ❌ {cluster.name}: Requirements NOT met")
            print(f"     Required:")
            print(f"       1. {cluster.subject_1}")
            print(f"       2. {cluster.subject_2}")
            print(f"       3. {cluster.subject_3}")
            print(f"       4. {cluster.subject_4}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
