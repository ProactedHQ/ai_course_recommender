"""
Unit tests for points calculator utility.
"""
from django.test import TestCase
from apps.universities.utils.points_calculator import (
    calculate_aggregate_points,
    calculate_cluster_points
)

# Grade points mapping for testing
GRADE_POINTS = {
    'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
}


class CalculateAggregatePointsTests(TestCase):
    """Test aggregate points calculation (best 7 subjects)."""
    
    def test_aggregate_with_7_subjects(self):
        """Test aggregate with exactly 7 subjects."""
        student_grades = {
            '101': 'A',    # 12
            '102': 'B+',   # 10
            '121': 'A-',   # 11
            '231': 'A',    # 12
            '232': 'A',    # 12
            '233': 'B+',   # 10
            '311': 'B',    # 9
        }
        
        result = calculate_aggregate_points(student_grades)
        expected = 12 + 12 + 12 + 11 + 10 + 10 + 9  # 76
        self.assertEqual(result, expected)
    
    def test_aggregate_with_more_than_7(self):
        """Test aggregate selects best 7 from more subjects."""
        student_grades = {
            '101': 'A',    # 12
            '102': 'C',    # 6 (should be excluded)
            '121': 'A-',   # 11
            '231': 'A',    # 12
            '232': 'A',    # 12
            '233': 'B+',   # 10
            '311': 'B',    # 9
            '312': 'B+',   # 10
        }
        
        result = calculate_aggregate_points(student_grades)
        # Best 7: A(12) + A(12) + A(12) + A-(11) + B+(10) + B+(10) + B(9) = 76
        self.assertEqual(result, 76)
    
    def test_aggregate_with_fewer_than_7(self):
        """Test aggregate with less than 7 subjects."""
        student_grades = {
            '101': 'A',    # 12
            '121': 'A-',   # 11
            '231': 'B+',   # 10
        }
        
        result = calculate_aggregate_points(student_grades)
        expected = 12 + 11 + 10  # 33
        self.assertEqual(result, expected)
    
    def test_maximum_aggregate(self):
        """Test maximum possible aggregate (84 points)."""
        student_grades = {
            '101': 'A',  # 12
            '102': 'A',  # 12
            '121': 'A',  # 12
            '231': 'A',  # 12
            '232': 'A',  # 12
            '233': 'A',  # 12
            '311': 'A',  # 12
        }
        
        result = calculate_aggregate_points(student_grades)
        self.assertEqual(result, 84)  # 7 × 12 = 84
    
    def test_empty_grades(self):
        """Test with no grades."""
        result = calculate_aggregate_points({})
        self.assertEqual(result, 0)


class CalculateClusterPointsTests(TestCase):
    """Test cluster points calculation formula."""
    
    def test_cluster_points_formula(self):
        """Test cluster points formula: √((r/R) × (t/T)) × 48."""
        cluster_subjects = [
            ('101', 'A', 12),
            ('121', 'A-', 11),
            ('231', 'B+', 10),
            ('232', 'B', 9),
        ]
        total_aggregate = 70
        
        result = calculate_cluster_points(cluster_subjects, total_aggregate)
        
        # r = 12 + 11 + 10 + 9 = 42
        # R = 48 (max for 4 subjects)
        # t = 70
        # T = 84 (max aggregate)
        # Formula: √((42/48) × (70/84)) × 48
        # = √(0.875 × 0.833) × 48
        # = √0.729 × 48
        # = 0.854 × 48
        # ≈ 40.99
        
        self.assertAlmostEqual(result, 40.99, places=1)
    
    def test_perfect_cluster_points(self):
        """Test maximum cluster points (48)."""
        cluster_subjects = [
            ('101', 'A', 12),
            ('121', 'A', 12),
            ('231', 'A', 12),
            ('232', 'A', 12),
        ]
        total_aggregate = 84  # Max aggregate
        
        result = calculate_cluster_points(cluster_subjects, total_aggregate)
        
        # r = 48, R = 48, t = 84, T = 84
        # √((48/48) × (84/84)) × 48 = √1 × 48 = 48
        self.assertEqual(result, 48.0)
    
    def test_cluster_points_with_lower_aggregate(self):
        """Test cluster points with lower aggregate."""
        cluster_subjects = [
            ('101', 'B', 9),
            ('121', 'B', 9),
            ('231', 'B', 9),
            ('232', 'B', 9),
        ]
        total_aggregate = 60
        
        result = calculate_cluster_points(cluster_subjects, total_aggregate)
        
        # r = 36, R = 48, t = 60, T = 84
        # √((36/48) × (60/84)) × 48
        # = √(0.75 × 0.714) × 48
        # = √0.536 × 48
        # = 0.732 × 48
        # ≈ 35.14
        
        self.assertAlmostEqual(result, 35.14, places=1)
    
    def test_cluster_points_returns_float(self):
        """Test that cluster points returns float with 3 decimal places."""
        cluster_subjects = [
            ('101', 'A-', 11),
            ('121', 'A-', 11),
            ('231', 'A-', 11),
            ('232', 'A-', 11),
        ]
        total_aggregate = 75
        
        result = calculate_cluster_points(cluster_subjects, total_aggregate)
        
        self.assertIsInstance(result, float)
        # Check it has at most 3 decimal places
        self.assertEqual(result, round(result, 3))
