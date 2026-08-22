
import os
import sys
import django
import time
from decimal import Decimal
from django.db.models import Prefetch

# Add project root and apps to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.students.models import StudentProfile, Subject, AcademicResult
from apps.universities.models import ProgrammeLevel, ProgrammeOffering, CutOffPoint
from apps.universities.utils.recommender_pipeline import RecommendationEngine

def create_mock_student(name, mean_grade):
    # Mock profile
    from unittest.mock import MagicMock
    student = MagicMock(spec=StudentProfile)
    student.name = name
    student.mean_grade = mean_grade
    
    # Mock academic results
    results = []
    subjects = ["MAT", "ENG", "KIS", "BIO", "PHY", "CHE", "HAG"]
    for code in subjects:
        res = MagicMock(spec=AcademicResult)
        res.subject.code = code
        res.grade = mean_grade
        results.append(res)
    
    student.academic_results.all.return_value = results
    return student

def run_grade_spectrum_test():
    grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']
    levels = ['DEGREE', 'DIPLOMA', 'CERTIFICATE', 'CRAFT', 'ARTISAN']
    
    print("=" * 60)
    print("🚀 OPTIMIZED KUCCPS GRADE SPECTRUM VERIFICATION (< 60s)")
    print("=" * 60)
    
    # STAGE 0: Pre-fetch ALL offerings globally for speed
    print("[1/2] Pre-fetching all offerings from database...")
    level_data = {}
    for level_name in levels:
        try:
            level = ProgrammeLevel.objects.get(name=level_name)
            level_data[level_name] = list(ProgrammeOffering.objects.filter(
                programme__level=level
            ).select_related(
                'programme', 'institution', 'programme__cluster'
            ).prefetch_related(
                'programme__requirements'
            ))
            print(f"      Cached {len(level_data[level_name])} programs for {level_name}")
        except:
            level_data[level_name] = []
            print(f"      No data for {level_name}")

    print("\n[2/2] Running in-memory recommendation analysis...")
    start_time = time.time()
    
    for grade in grades:
        student = create_mock_student(f"Student_{grade}", grade)
        counts = {}
        for level_name in levels:
            engine = RecommendationEngine(student, level_name=level_name, offerings=level_data[level_name])
            results = engine.run()
            counts[level_name] = len(results)
            
        print(f"🎓 Grade {grade: <3} | Results: {counts}")

    duration = time.time() - start_time
    print("-" * 60)
    print(f"✅ VERIFICATION COMPLETE in {duration:.2f} seconds.")
    print("=" * 60)

if __name__ == "__main__":
    run_grade_spectrum_test()
