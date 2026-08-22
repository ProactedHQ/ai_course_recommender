"""
Programme Eligibility Filter - OPTIMIZED VERSION

Main filtering logic to determine which programmes a student is eligible for based on:
1. Cluster requirements matching
2. Cluster points calculation
3. Subcluster requirements matching
4. Cutoff points comparison (with year fallback)

PERFORMANCE OPTIMIZATIONS:
- Aggressive prefetching to eliminate N+1 queries
- Subject cache built once and reused
- Early cluster filtering before programme queries
- In-memory cutoff lookup (no DB queries)
"""

from typing import Dict, List, Optional
from django.db.models import Prefetch, Q
from apps.students.models import Subject

from ..models import (
    ClusterGroup, SubClusterGroup, Programme,
    ProgrammeOffering, CutOffPoint, ProgrammeLevel
)
from .requirement_parser import (
    parse_all_cluster_requirements,
    parse_all_subcluster_requirements
)
from .subject_matcher import (
    find_best_subject_combination,
    check_subcluster_eligibility
)
from .points_calculator import (
    calculate_aggregate_points,
    calculate_cluster_points
)


GRADE_VALUES = {
    'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
}

def get_grade_value(grade: str) -> int:
    """Map grade to numeric value for comparison (A=12, E=1)."""
    return GRADE_VALUES.get(str(grade).strip(), 0)


def get_latest_cutoff_optimized(
    offering: ProgrammeOffering,
    target_year: int
) -> Optional[CutOffPoint]:
    """
    OPTIMIZED: Get cutoff using pre-fetched data (NO database queries).
    
    Expects cutoffs to be prefetched and ordered by -year.
    Falls back to previous years if current year is unavailable.
    
    Args:
        offering: ProgrammeOffering instance with prefetched cutoffs
        target_year: Preferred year (e.g., 2024)
    
    Returns:
        CutOffPoint instance with valid weighted_cluster_points, or None
    """
    # Iterate through pre-fetched cutoffs (already ordered by -year)
    # This is IN-MEMORY iteration - no database query!
    for cutoff in offering.cutoffs.all():
        # Only accept cutoffs with valid (non-NULL) points
        if cutoff.weighted_cluster_points is not None:
            return cutoff
    
    # No valid cutoff found
    return None


def get_eligible_programmes(
    student_grades: Dict[str, str],
    target_year: int = 2024,
    level_name: str = 'DEGREE'
) -> List[Dict]:
    """
    OPTIMIZED: Get all programmes student is eligible for.
    
    PERFORMANCE IMPROVEMENTS:
    1. Subject cache built ONCE at start
    2. Aggressive prefetching - single mega-query for all data
    3. Early cluster filtering - skip ineligible clusters before programme queries
    4. In-memory cutoff lookup - no N+1 queries
    
    Args:
        student_grades: Dict of {subject_code: grade}
                       e.g., {'101': 'B+', '121': 'A-', '231': 'A', '232': 'B+'}
        target_year: Year to check cutoffs (defaults to 2024)
        level_name: Programme level (defaults to 'DEGREE')
    
    Returns:
        List of dicts with programme info and eligibility details
    """
    # OPTIMIZATION 1: Calculate aggregate once
    total_aggregate = calculate_aggregate_points(student_grades)
    
    # OPTIMIZATION 2: Build subject cache ONCE (eliminates ~20 queries)
    subject_cache = {s.code: s for s in Subject.objects.all()}
    
    eligible_programmes = []
    
    # Get programme level
    # KUCCPS HIERARCHY RULES
    level_defaults = {
        'DEGREE': 'C+',
        'DIPLOMA': 'C-',
        'CERTIFICATE': 'C-',
        'CRAFT': 'D',
        'ARTISAN': 'E'
    }
    kuccps_min = level_defaults.get(level_name, 'E')
    
    student_mean = student_grades.get('MEAN', 'E')
    
    if get_grade_value(student_mean) < get_grade_value(kuccps_min):
        return []

    try:
        level = ProgrammeLevel.objects.get(name=level_name)
    except ProgrammeLevel.DoesNotExist:
        return []
    
    # OPTIMIZATION 3: Aggressive prefetching - single mega-query
    # This eliminates thousands of N+1 queries by fetching everything upfront
    clusters = ClusterGroup.objects.filter(level=level).prefetch_related(
        Prefetch(
            'programme_set',
            queryset=Programme.objects.select_related('level').prefetch_related(
                Prefetch(
                    'offerings',
                    queryset=ProgrammeOffering.objects.select_related('institution')
                )
            )
        ),
        Prefetch(
            'subclusters',
            queryset=SubClusterGroup.objects.prefetch_related(
                Prefetch(
                    'programmes',
                    queryset=Programme.objects.select_related('level').prefetch_related(
                        Prefetch(
                            'offerings',
                            queryset=ProgrammeOffering.objects.select_related('institution').prefetch_related(
                                Prefetch(
                                    'cutoffs',
                                    queryset=CutOffPoint.objects.filter(
                                        year__gte=target_year - 6,  # Last 7 years
                                        weighted_cluster_points__isnull=False  # Skip NULLs
                                    ).order_by('-year')  # Newest first
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    
    # ====================================================================
    # BRANCHING LOGIC: DEGREE vs TVET
    # DEGREE: Cluster points calculation + cutoff comparison
    # TVET:   Grade-only check — if mean grade meets minimum, they're in
    # ====================================================================
    
    is_degree = (level_name == 'DEGREE')
    
    if is_degree:
        # ── DEGREE PATH: Full cluster matching + cutoff comparison ──
        # OPTIMIZATION 4: Early cluster filtering
        eligible_clusters = []
        
        for cluster in clusters:
            cluster_reqs = parse_all_cluster_requirements(cluster)
            cluster_subjects = find_best_subject_combination(
                student_grades, cluster_reqs, subject_cache
            )
            
            if not cluster_subjects:
                continue
            
            cluster_points = calculate_cluster_points(cluster_subjects, total_aggregate)
            eligible_clusters.append((cluster, cluster_subjects, cluster_points))
        
        for cluster, cluster_subjects, cluster_points in eligible_clusters:
            for subcluster in cluster.subclusters.all():
                subcluster_reqs = parse_all_subcluster_requirements(subcluster)
                
                if not check_subcluster_eligibility(
                    student_grades, subcluster_reqs, cluster_subjects, subject_cache
                ):
                    continue
                
                for programme in subcluster.programmes.all():
                    for offering in programme.offerings.all():
                        all_cutoffs = list(offering.cutoffs.all())
                        latest_cutoff = all_cutoffs[0] if all_cutoffs else None
                        previous_cutoff = all_cutoffs[1] if len(all_cutoffs) > 1 else None
                        
                        if not latest_cutoff:
                            continue
                        
                        latest_value = float(latest_cutoff.weighted_cluster_points)
                        prev_value = float(previous_cutoff.weighted_cluster_points) if previous_cutoff else None
                        
                        is_eligible = cluster_points >= latest_value
                        points_margin = cluster_points - latest_value
                        
                        eligible_programmes.append({
                            'programme': programme,
                            'offering': offering,
                            'institution': offering.institution,
                            'cluster': cluster,
                            'subcluster': subcluster,
                            'student_points': cluster_points,
                            'cutoff_points': latest_value,
                            'cutoff_year': latest_cutoff.year,
                            'prev_cutoff_points': prev_value,
                            'prev_cutoff_year': previous_cutoff.year if previous_cutoff else None,
                            'cluster_subjects': cluster_subjects,
                            'is_eligible': is_eligible,
                            'aggregate': total_aggregate,
                            'points_margin': round(points_margin, 3)
                        })
    
    else:
        # ---- TVET PATH: Grade-only check (no cluster points required) ----
        # For Diploma, Certificate, Craft, Artisan - eligibility is purely
        # based on whether the student's Mean Grade meets the programme's minimum.
        # No cluster subject matching or cutoff points are used.
        
        student_mean_val = get_grade_value(student_mean)
        
        for cluster in clusters:
            # Check both SubCluster programmes AND direct Cluster programmes
            # (TVET data often maps directly to ClusterGroup)
            
            # A. Process SubClusters (if any)
            for subcluster in cluster.subclusters.all():
                for programme in subcluster.programmes.all():
                    prog_min = programme.minimum_mean_grade or kuccps_min
                    prog_min_val = get_grade_value(prog_min)
                    
                    is_eligible = student_mean_val >= prog_min_val
                    
                    for offering in programme.offerings.all():
                        eligible_programmes.append({
                            'programme': programme,
                            'offering': offering,
                            'institution': offering.institution,
                            'cluster': cluster,
                            'subcluster': subcluster,
                            'student_points': student_mean_val,
                            'cutoff_points': prog_min_val,
                            'cutoff_year': None,
                            'prev_cutoff_points': None,
                            'prev_cutoff_year': None,
                            'cluster_subjects': {}, # Not required for TVET
                            'is_eligible': is_eligible,
                            'aggregate': total_aggregate,
                            'points_margin': 0
                        })
            
            # B. Process direct Cluster programmes (TVET fix)
            # We use programme_set as the default related name since none is defined.
            for programme in cluster.programme_set.all():
                prog_min = programme.minimum_mean_grade or kuccps_min
                prog_min_val = get_grade_value(prog_min)
                is_eligible = student_mean_val >= prog_min_val
                
                for offering in programme.offerings.all():
                    eligible_programmes.append({
                        'programme': programme,
                        'offering': offering,
                        'institution': offering.institution,
                        'cluster': cluster,
                        'subcluster': None,
                        'student_points': student_mean_val,
                        'cutoff_points': prog_min_val,
                        'cutoff_year': None,
                        'prev_cutoff_points': None,
                        'prev_cutoff_year': None,
                        'cluster_subjects': {},
                        'is_eligible': is_eligible,
                        'aggregate': total_aggregate,
                        'points_margin': 0
                    })
    
    # Sort by points margin (best matches first)
    eligible_programmes.sort(key=lambda x: x['points_margin'], reverse=True)
    
    return eligible_programmes


def filter_eligible_only(programmes_list: List[Dict]) -> List[Dict]:
    """
    Filter to only programmes where student meets cutoff.
    
    Args:
        programmes_list: Output from get_eligible_programmes()
    
    Returns:
        Filtered list with only is_eligible=True
    """
    return [p for p in programmes_list if p['is_eligible']]


def get_programme_summary(programme_dict: Dict) -> str:
    """
    Format programme eligibility info for display.
    
    Args:
        programme_dict: Single programme dict from get_eligible_programmes()
    
    Returns:
        Human-readable summary string
    """
    status = "[OK] ELIGIBLE" if programme_dict['is_eligible'] else "[X] Not Eligible"
    margin = f"+{programme_dict['points_margin']}" if programme_dict['points_margin'] > 0 else str(programme_dict['points_margin'])
    
    return f"""
{status}
Programme: {programme_dict['programme'].name}
Institution: {programme_dict['institution'].name}
Cluster: {programme_dict['cluster'].name}
Subcluster: {programme_dict['subcluster'].code}
Student Points: {programme_dict['student_points']}
Cutoff Points: {programme_dict['cutoff_points']} ({programme_dict['cutoff_year']})
Margin: {margin}
    """.strip()
