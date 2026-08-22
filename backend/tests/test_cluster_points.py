
import os
import sys
import django
import math

# Add project root to sys.path
sys.path.append(os.getcwd())
# Add apps to sys.path
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.utils.points_calculator import calculate_aggregate_points, calculate_cluster_points
from apps.universities.utils.subject_matcher import find_best_subject_combination, GRADE_TO_POINTS
from apps.universities.models import ClusterGroup
from apps.students.models import Subject
from apps.universities.utils.requirement_parser import parse_all_cluster_requirements

def get_mean_grade(aggregate):
    points = aggregate / 7
    if points >= 11.5: return 'A'
    if points >= 10.5: return 'A-'
    if points >= 9.5: return 'B+'
    if points >= 8.5: return 'B'
    if points >= 7.5: return 'B-'
    if points >= 6.5: return 'C+'
    if points >= 5.5: return 'C'
    if points >= 4.5: return 'C-'
    if points >= 3.5: return 'D+'
    if points >= 2.5: return 'D'
    if points >= 1.5: return 'D-'
    return 'E'

def format_student(student_grades):
    return ", ".join([f"{code}:{grade}" for code, grade in student_grades.items()])

def run_test_case(name, student_grades):
    print(f"\n=== TEST CASE: {name} ===")
    print(f"Grades: {format_student(student_grades)}")
    
    # 1. Aggregate Points
    aggregate = calculate_aggregate_points(student_grades)
    mean_grade = get_mean_grade(aggregate)
    print(f"Aggregate: {aggregate}/84 (Mean Grade: {mean_grade})")
    
    # 2. Get all clusters and subjects cache
    clusters = ClusterGroup.objects.filter(level__name='DEGREE').order_by('code')
    subject_cache = {s.code: s for s in Subject.objects.all()}
    
    # 3. Test each cluster
    results = []
    for cluster in clusters:
        reqs = parse_all_cluster_requirements(cluster)
        best_combo = find_best_subject_combination(student_grades, reqs, subject_cache)
        
        if best_combo:
            points = calculate_cluster_points(best_combo, aggregate)
            results.append({
                'code': cluster.code,
                'name': cluster.name,
                'combo': best_combo,
                'points': points
            })
    
    # Sort and display results
    results.sort(key=lambda x: x['points'], reverse=True)
    print(f"Eligible for {len(results)}/{len(clusters)} clusters.")
    
    if results:
        print("\nTop 5 Cluster Results:")
        for r in results[:5]:
            combo_str = ", ".join([f"{c}({g}:{p})" for c, g, p in r['combo']])
            print(f" - Cluster {r['code']} ({r['name'][:40]}...): {r['points']} pts")
            print(f"   Combo: {combo_str}")
    else:
        print("Not eligible for any cluster.")

def main():
    # 1. A (81-84)
    profile_a = {'101': 'A', '102': 'A', '121': 'A', '231': 'A', '233': 'A', '311': 'A', '571': 'A'}
    # 2. A- (74-80)
    profile_a_minus = {'101': 'A-', '102': 'A-', '121': 'A-', '231': 'A-', '233': 'A-', '311': 'A-', '571': 'A-'}
    # 3. B+ (67-73)
    profile_b_plus = {'101': 'B+', '102': 'B+', '121': 'B+', '231': 'B+', '233': 'B+', '311': 'B+', '571': 'B+'}
    # 4. B (60-66)
    profile_b = {'101': 'B', '102': 'B', '121': 'B', '231': 'B', '233': 'B', '311': 'B', '571': 'B'}
    # 5. B- (53-59)
    profile_b_minus = {'101': 'B-', '102': 'B-', '121': 'B-', '231': 'B-', '233': 'B-', '311': 'B-', '571': 'B-'}
    # 6. C+ (46-52)
    profile_c_plus = {'101': 'C+', '102': 'C+', '121': 'C+', '231': 'C+', '233': 'C+', '311': 'C+', '571': 'C+'}
    # 7. C (39-45)
    profile_c = {'101': 'C', '102': 'C', '121': 'C', '231': 'C', '233': 'C', '311': 'C', '571': 'C'}
    # 8. C- (32-38)
    profile_c_minus = {'101': 'C-', '102': 'C-', '121': 'C-', '231': 'C-', '233': 'C-', '311': 'C-', '571': 'C-'}
    # 9. D+ (25-31)
    profile_d_plus = {'101': 'D+', '102': 'D+', '121': 'D+', '231': 'D+', '233': 'D+', '311': 'D+', '571': 'D+'}
    # 10. D (18-24)
    profile_d = {'101': 'D', '102': 'D', '121': 'D', '231': 'D', '233': 'D', '311': 'D', '571': 'D'}
    # 11. D- (11-17)
    profile_d_minus = {'101': 'D-', '102': 'D-', '121': 'D-', '231': 'D-', '233': 'D-', '311': 'D-', '571': 'D-'}
    # 12. E (7-10)
    profile_e = {'101': 'E', '102': 'E', '121': 'E', '231': 'E', '233': 'E', '311': 'E', '571': 'E'}

    profiles = [
        ("Mean Grade A", profile_a),
        ("Mean Grade A-", profile_a_minus),
        ("Mean Grade B+", profile_b_plus),
        ("Mean Grade B", profile_b),
        ("Mean Grade B-", profile_b_minus),
        ("Mean Grade C+", profile_c_plus),
        ("Mean Grade C", profile_c),
        ("Mean Grade C-", profile_c_minus),
        ("Mean Grade D+", profile_d_plus),
        ("Mean Grade D", profile_d),
        ("Mean Grade D-", profile_d_minus),
        ("Mean Grade E", profile_e)
    ]

    for name, profile in profiles:
        run_test_case(name, profile)

if __name__ == "__main__":
    main()
