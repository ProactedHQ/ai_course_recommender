"""
Subject Matcher for KCSE Requirements

Matches student subjects/grades to cluster/subcluster requirements.
Implements strict matching: Student MUST meet ALL 4 requirements or is disqualified.
"""

from typing import Dict, List, Optional, Tuple
from apps.students.models import Subject


# Grade to points mapping (KCSE grading system)
GRADE_TO_POINTS = {
    'A': 12, 'A-': 11,
    'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5,
    'D+': 4, 'D': 3, 'D-': 2,
    'E': 1
}

# Grade hierarchy for comparison (lower index = better grade)
GRADE_HIERARCHY = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']


def normalize_grade(grade: str) -> str:
    """Normalize grade format (e.g., "B plain" → "B")"""
    grade = str(grade).strip().upper()
    # Remove "PLAIN" or other text
    grade = grade.replace('PLAIN', '').replace('(', '').replace(')', '').strip()
    return grade


def grade_meets_minimum(student_grade: str, min_grade: str) -> bool:
    """
    Check if student's grade meets minimum requirement.
    
    Args:
        student_grade: Student's actual grade (e.g., "B+")
        min_grade: Minimum required grade (e.g., "C+")
    
    Returns:
        True if student grade >= minimum grade
    """
    if not min_grade:
        return True  # No minimum specified
    
    student_grade = normalize_grade(student_grade)
    min_grade = normalize_grade(min_grade)
    
    try:
        student_idx = GRADE_HIERARCHY.index(student_grade)
        min_idx = GRADE_HIERARCHY.index(min_grade)
        return student_idx <= min_idx  # Lower index = better grade
    except ValueError:
        # Grade not in hierarchy
        return False


def match_requirement(
    student_grades: Dict[str, str],
    requirement: Dict,
    subject_cache: Dict[str, Subject]
) -> List[Tuple[str, str, int]]:
    """
    Match student subjects to a single requirement.
    
    Args:
        student_grades: Dict of {subject_code: grade}, e.g., {'101': 'B+', '121': 'A-'}
        requirement: Parsed requirement dict from requirement_parser
        subject_cache: Optional cache of Subject objects
    
    Returns:
        List of (subject_code, grade, points) tuples that match the requirement
    """
    if requirement['type'] == 'none':
        return []
    
    matches = []
    
    if requirement['type'] == 'specific':
        # Check if student has any of the specified subjects
        for subj_code in requirement['subjects']:
            if subj_code in student_grades:
                grade = student_grades[subj_code]
                
                # Check minimum grade if specified
                if requirement.get('min_grade'):
                    if not grade_meets_minimum(grade, requirement['min_grade']):
                        continue  # Grade too low
                
                points = GRADE_TO_POINTS.get(normalize_grade(grade), 0)
                matches.append((subj_code, grade, points))
    
    elif requirement['type'] == 'group':
        # Find all student subjects in the specified groups
        # subject_cache is now required parameter
        for subj_code, grade in student_grades.items():
            subject = subject_cache.get(subj_code)
            if subject and subject.category in requirement['groups']:
                # Check minimum grade if specified
                if requirement.get('min_grade'):
                    if not grade_meets_minimum(grade, requirement['min_grade']):
                        continue
                
                points = GRADE_TO_POINTS.get(normalize_grade(grade), 0)
                matches.append((subj_code, grade, points))
    
    elif requirement['type'] == 'unknown':
        # Could not parse requirement - skip for safety
        return []
    
    return matches


def find_best_subject_combination(
    student_grades: Dict[str, str],
    requirements: List[Dict],
    subject_cache: Dict[str, Subject]
) -> Optional[List[Tuple[str, str, int]]]:
    """
    Find the best 4 UNIQUE subjects that match ALL cluster requirements.
    
    STRICT RULE: Student MUST meet ALL 4 requirements or return None.
    If a requirement needs Physics and student didn't take it, they're disqualified.
    
    Selects the BEST performing subjects (highest points) from available matches.
    
    Args:
        student_grades: Dict of {subject_code: grade}
        requirements: List of 4 parsed requirement dicts
        subject_cache: Pre-built cache of Subject objects {code: Subject}
    
    Returns:
        List of 4 (subject_code, grade, points) tuples that maximize points,
        or None if ANY requirement is not met
    """
    # subject_cache now passed as parameter - no DB query!
    
    # Match each requirement and track which subjects can satisfy each
    requirement_matches = []
    
    for req in requirements:
        if req['type'] == 'none':
            # Empty requirement - can be filled by any subject later
            requirement_matches.append((req, []))
            continue
        
        matches = match_requirement(student_grades, req, subject_cache)
        
        if not matches:
            # CRITICAL: Student does NOT meet this requirement
            # Example: Cluster needs Physics ('231'), student didn't take it
            # Result: Student is DISQUALIFIED from this cluster
            return None
        
        requirement_matches.append((req, matches))
    
    # At this point, student meets ALL non-empty requirements
    # Now assign best subjects to each requirement without reuse
    
    selected = []
    used_subjects = set()
    
    # First pass: Assign subjects to requirements with fewest options (most constrained first)
    # This ensures we don't waste a rare subject on a flexible requirement
    requirement_matches_sorted = sorted(
        requirement_matches,
        key=lambda x: len(x[1]) if x[1] else 999  # Empty reqs last
    )
    
    for req, matches in requirement_matches_sorted:
        if req['type'] == 'none' or not matches:
            continue
        
        # Filter out already used subjects
        available = [m for m in matches if m[0] not in used_subjects]
        
        if not available:
            # This shouldn't happen if we sorted correctly, but safety check
            # Try to find ANY unused subject that could work
            continue
        
        # Pick the highest points from available
        best = max(available, key=lambda x: x[2])
        selected.append(best)
        used_subjects.add(best[0])
    
    # Fill remaining slots (if any) with best unused subjects
    # This handles 'none' type requirements
    while len(selected) < 4:
        # Get all unused subjects
        unused = [
            (code, grade, GRADE_TO_POINTS.get(normalize_grade(grade), 0))
            for code, grade in student_grades.items()
            if code not in used_subjects
        ]
        
        if not unused:
            # Not enough subjects to fill 4 slots
            return None
        
        # Pick best unused
        best = max(unused, key=lambda x: x[2])
        selected.append(best)
        used_subjects.add(best[0])
    
    # Ensure exactly 4 unique subjects
    if len(selected) != 4:
        return None
    
    # Final validation: all subjects are unique
    if len(set(s[0] for s in selected)) != 4:
        return None
    
    return selected


def check_subcluster_eligibility(
    student_grades: Dict[str, str],
    subcluster_requirements: List[Dict],
    cluster_subjects: List[Tuple[str, str, int]],
    subject_cache: Dict[str, Subject]
) -> bool:
    """
    Check if student meets subcluster requirements.
    
    Subcluster requirements are ADDITIONAL constraints on top of cluster requirements.
    They typically specify minimum grades for specific subjects already in the cluster.
    
    Args:
        student_grades: Dict of {subject_code: grade}
        subcluster_requirements: List of 4 parsed subcluster requirement dicts
        cluster_subjects: The 4 subjects selected for cluster points
        subject_cache: Pre-built cache of Subject objects {code: Subject}
    
    Returns:
        True if student meets all subcluster requirements
    """
    # subject_cache now passed as parameter - no DB query!
    
    for req in subcluster_requirements:
        if req['type'] == 'none':
            continue  # No additional requirement
        
        matches = match_requirement(student_grades, req, subject_cache)
        
        if not matches:
            # Student doesn't meet this subcluster requirement
            return False
    
    return True
