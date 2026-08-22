
from typing import List, Dict, Optional
from decimal import Decimal
from django.db.models import Prefetch
from apps.universities.models import (
    ProgrammeOffering, Programme, ProgrammeLevel, 
    ClusterGroup, CutOffPoint, ProgrammeRequirement
)
from apps.students.models import Subject
from .points_calculator import calculate_aggregate_points, calculate_cluster_points
from .requirement_parser import parse_all_cluster_requirements, parse_all_subcluster_requirements
from .subject_matcher import find_best_subject_combination, check_subcluster_eligibility

class RecommendationEngine:
    """
    4-Stage Recommendation Pipeline:
    1. Retrieval: Fetch all possible offerings for the student's level.
    2. Filtering: Apply hard eligibility rules (Grades, Prerequisites).
    3. Scoring: Calculate merit scores (Cluster Points or Grade-based).
    4. Reasoning: Generate technical explanations for eligibility.
    """

    def __init__(self, student_profile, level_name: str = 'DEGREE', target_year: int = 2024, offerings=None):
        self.student = student_profile
        self.level_name = level_name
        self.target_year = target_year
        self.student_grades = self._get_student_grades() if student_profile else {}
        self.aggregate_points = calculate_aggregate_points(self.student_grades) if self.student_grades else 0
        self.subject_cache = {s.code: s for s in Subject.objects.all()}
        self.prefetched_offerings = offerings
        self.results = []

    def _get_student_grades(self) -> Dict[str, str]:
        """Convert student academic results to {subject_code: grade} dict."""
        return {res.subject.code: res.grade for res in self.student.academic_results.all()}

    @staticmethod
    def get_grade_value(grade: str) -> int:
        """Map grade to numeric value for comparison (A=12, E=1)."""
        grade_map = {
            'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
            'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
        }
        return grade_map.get(grade, 0)

    def run(self) -> List[Dict]:
        """Orchestrate the 4-stage pipeline."""
        # Stage 1: Retrieval (Prefetch + Filter by Level)
        offerings = self.prefetched_offerings if self.prefetched_offerings is not None else self.retrieve()
        
        # Stage 2: Filtering & Stage 3: Scoring
        for offering in offerings:
            eligibility = self.filter(offering)
            if eligibility['is_eligible']:
                score = self.score(offering, eligibility)
                
                # Stage 4: Reasoning
                reasoning = self.reason(offering, eligibility, score)
                
                self.results.append({
                    'offering': offering,
                    'eligibility': eligibility,
                    'score': score,
                    'reasoning': reasoning
                })
        
        # Sort by score descending (Higher cluster points or better merit)
        self.results.sort(key=lambda x: x['score'], reverse=True)
        return self.results

    def retrieve(self) -> List[ProgrammeOffering]:
        """STAGE 1: Fetch offerings with optimized prefetching."""
        try:
            level = ProgrammeLevel.objects.get(name=self.level_name)
        except ProgrammeLevel.DoesNotExist:
            return []
        
        return ProgrammeOffering.objects.filter(
            programme__level=level
        ).select_related(
            'programme', 'institution', 'programme__cluster'
        ).prefetch_related(
            'programme__requirements',
            Prefetch(
                'cutoffs',
                queryset=CutOffPoint.objects.filter(
                    year__gte=self.target_year - 5
                ).order_by('-year')
            )
        )

    def filter(self, offering: ProgrammeOffering) -> Dict:
        """STAGE 2: Check hard eligibility (Grades & Subjects)."""
        programme = offering.programme
        is_eligible = True
        reason = ""
        
        # A. Mean Grade Check
        level_defaults = {
            'DEGREE': 'C+',
            'DIPLOMA': 'C-',
            'CERTIFICATE': 'C-',
            'CRAFT': 'D',
            'ARTISAN': 'E'
        }
        # Ensure we use the KUCCPS level-wide minimum floor
        kuccps_min = level_defaults.get(self.level_name, 'E')
        db_min = programme.minimum_mean_grade
        
        # Logic: Use DB's specific grade if it is MORE restrictive than KUCCPS floor
        if db_min and self.get_grade_value(db_min) > self.get_grade_value(kuccps_min):
            min_mean = db_min
        else:
            min_mean = kuccps_min
        
        if self.get_grade_value(self.student.mean_grade) < self.get_grade_value(min_mean):
            return {'is_eligible': False, 'reason': f"Requires Mean Grade {min_mean}"}
            
        # B. Degree-Specific Cluster Requirements
        cluster_subjects = None
        if self.level_name == 'DEGREE' and programme.cluster:
            cluster_reqs = parse_all_cluster_requirements(programme.cluster)
            cluster_subjects = find_best_subject_combination(self.student_grades, cluster_reqs, self.subject_cache)
            
            if not cluster_subjects:
                return {'is_eligible': False, 'reason': "Does not meet cluster subject requirements"}
        
        # C. Generic Subject Requirements
        for req in programme.requirements.all():
            # (Simplified check: assuming requirements are mandatory)
            # This will be expanded as needed.
            pass
            
        return {
            'is_eligible': True,
            'cluster_subjects': cluster_subjects,
            'reason': "Meets all requirements"
        }

    def score(self, offering: ProgrammeOffering, eligibility: Dict) -> float:
        """STAGE 3: Calculate merit score (Cluster Points or TVET Grade Score)."""
        if self.level_name == 'DEGREE':
            # Weighted Cluster Points
            if eligibility['cluster_subjects']:
                return float(calculate_cluster_points(eligibility['cluster_subjects'], self.aggregate_points))
            return 0.0
        else:
            # Merit score for TVET: Just use Mean Grade points for now
            return float(self.get_grade_value(self.student.mean_grade))

    def reason(self, offering: ProgrammeOffering, eligibility: Dict, score: float) -> str:
        """STAGE 4: Generate technical explanation."""
        programme = offering.programme
        cost_info = f" | Annual Cost: KES {offering.cost:,.0f}" if offering.cost else ""
        
        if self.level_name == 'DEGREE':
            return f"Eligible for {programme.name}. Your Cluster Points: {score:.3f}. Mean Grade: {self.student.mean_grade}.{cost_info}"
        else:
            return f"Eligible for {programme.name}. Minimum Grade: {programme.minimum_mean_grade}. Your Grade: {self.student.mean_grade}.{cost_info}"
