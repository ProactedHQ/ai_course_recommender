"""
Cluster Points Calculator

Implements KCSE cluster points formula: √((r/R) × (t/T)) × 48

Where:
- r = Sum of 4 cluster subject points (max 48)
- R = Maximum cluster points = 48
- t = Student's aggregate points (max 84)
- T = Maximum aggregate = 84
"""

import math
from typing import Dict, List, Tuple
from .subject_matcher import GRADE_TO_POINTS, normalize_grade


def calculate_aggregate_points(student_grades: Dict[str, str]) -> int:
    """
    Calculate total KCSE aggregate points based on the 7-subject rule:
    1. Mathematics (compulsory)
    2. Best of English or Kiswahili (compulsory)
    3. Five other best subjects
    
    Maximum: 84 points (7 subjects × 12 points each)
    """
    from .subject_matcher import GRADE_TO_POINTS, normalize_grade
    
    # Track used subject codes to avoid double counting
    used_subject_codes = set()
    selected_points = []

    # 1. Mathematics (121 or 122) - Compulsory
    # We pick the best math if both are present (unlikely in real KCSE but safe for data)
    math_codes = ['121', '122']
    math_options = []
    for code in math_codes:
        if code in student_grades:
            math_options.append((code, GRADE_TO_POINTS.get(normalize_grade(student_grades[code]), 0)))
    
    if math_options:
        best_math = max(math_options, key=lambda x: x[1])
        selected_points.append(best_math[1])
        used_subject_codes.add(best_math[0])
    # Note: If no math is provided, they get 0 for this compulsory slot

    # 2. Best Language (101 or 102) - Compulsory
    lang_codes = ['101', '102']
    lang_options = []
    for code in lang_codes:
        if code in student_grades:
            lang_options.append((code, GRADE_TO_POINTS.get(normalize_grade(student_grades[code]), 0)))
    
    if lang_options:
        best_lang = max(lang_options, key=lambda x: x[1])
        selected_points.append(best_lang[1])
        used_subject_codes.add(best_lang[0])
    
    # 3. Best 5 others
    other_options = []
    for code, grade in student_grades.items():
        if code not in used_subject_codes and code != 'MEAN': # Skip special tags
            pts = GRADE_TO_POINTS.get(normalize_grade(grade), 0)
            other_options.append(pts)
    
    # Sort others descending and take best 5
    other_options.sort(reverse=True)
    selected_points.extend(other_options[:5])
    
    aggregate = sum(selected_points)
    
    # Ensure we have at least 7 subjects conceptually (pad with 0 if necessary)
    # although sum handles this naturally.
    
    return min(aggregate, 84)


def calculate_overall_mean_grade(aggregate_points: int) -> str:
    """
    Determine the overall mean grade from aggregate points.
    Mean = Aggregate / 7.
    
    Grade boundaries (Scale of 12):
    12 (84) -> A
    11 (77) -> A-
    ...
    1 (7) -> E
    """
    from .subject_matcher import GRADE_HIERARCHY
    
    # Calculate average points
    avg_points = aggregate_points / 7.0
    rounded_avg = round(avg_points)
    
    # Map back to grade
    # 12 -> index 0 (A), 11 -> index 1 (A-), ..., 1 -> index 11 (E)
    # Formula: index = 12 - rounded_avg
    index = max(0, min(11, 12 - rounded_avg))
    
    return GRADE_HIERARCHY[index]


def calculate_cluster_points(
    cluster_subjects: List[Tuple[str, str, int]],
    total_aggregate: int
) -> float:
    """
    Calculate cluster points using KCSE formula.
    
    Formula: √((r/R) × (t/T)) × 48
    
    Args:
        cluster_subjects: List of 4 (subject_code, grade, points) tuples
        total_aggregate: Student's total KCSE aggregate (max 84)
    
    Returns:
        Cluster points (max 48.0)
    
    Example:
        cluster_subjects = [('101', 'A-', 11), ('121', 'B+', 10), ('231', 'A', 12), ('232', 'B', 9)]
        total_aggregate = 81
        cluster_points = √((42/48) × (81/84)) × 48
                       = √(0.875 × 0.964) × 48
                       = √0.844 × 48
                       = 0.919 × 48
                       = 44.09
    """
    R = 48  # Max cluster points (4 subjects × 12 points each)
    T = 84  # Max aggregate points (7 subjects × 12 points each)
    
    # r: Sum of 4 cluster subject points
    r = sum(points for _, _, points in cluster_subjects)
    
    # t: Total aggregate (capped at 84)
    t = min(total_aggregate, T)
    
    # Handle edge cases
    if r == 0 or t == 0:
        return 0.0
    
    # Apply formula: √((r/R) × (t/T)) × 48
    cluster_points = math.sqrt((r / R) * (t / T)) * 48
    
    # Round to 3 decimal places (matches KUCCPS format)
    return round(cluster_points, 3)


def format_cluster_calculation(
    cluster_subjects: List[Tuple[str, str, int]],
    total_aggregate: int,
    cluster_points: float
) -> str:
    """
    Format cluster calculation for debugging/display.
    
    Returns:
        Human-readable calculation breakdown
    """
    from .requirement_parser import CODE_TO_NAME
    
    r = sum(points for _, _, points in cluster_subjects)
    
    subjects_str = ', '.join([
        f"{CODE_TO_NAME.get(code, code)} ({grade}: {points} pts)"
        for code, grade, points in cluster_subjects
    ])
    
    calculation = f"""
Cluster Points Calculation:
- Subjects: {subjects_str}
- Cluster Points (r): {r}/48
- Aggregate (t): {total_aggregate}/84
- Formula: √(({r}/48) × ({total_aggregate}/84)) × 48
- Result: {cluster_points}
    """.strip()
    
    return calculation
