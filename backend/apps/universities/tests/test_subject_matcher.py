"""
Unit tests for subject matcher utility.
"""
from django.test import TestCase
from apps.universities.utils.subject_matcher import (
    match_requirement,
    find_best_subject_combination,
    check_subcluster_eligibility,
    compare_grades
)
from students.models import Subject


class CompareGradesTests(TestCase):
    """Test grade comparison logic."""
    
    def test_grade_hierarchy(self):
        """Test that grades are compared correctly."""
        # A > A-
        self.assertTrue(compare_grades('A', 'A-'))
        self.assertFalse(compare_grades('A-', 'A'))
        
        # A- > B+
        self.assertTrue(compare_grades('A-', 'B+'))
        
        # B+ > B > B-
        self.assertTrue(compare_grades('B+', 'B'))
        self.assertTrue(compare_grades('B', 'B-'))
        
        # Equal grades
        self.assertTrue(compare_grades('B+', 'B+'))
    
    def test_grade_edge_cases(self):
        """Test edge cases in grade comparison."""
        # Highest and lowest
        self.assertTrue(compare_grades('A', 'E'))
        self.assertFalse(compare_grades('E', 'A'))
        
        # Same grade should return True (meets requirement)
        self.assertTrue(compare_grades('B', 'B'))


class MatchRequirementTests(TestCase):
    """Test requirement matching logic."""
    
    def setUp(self):
        """Create test subjects."""
        Subject.objects.create(code='101', name='English', category='GP1', max_points=12)
        Subject.objects.create(code='102', name='Kiswahili', category='GP1', max_points=12)
        Subject.objects.create(code='121', name='Mathematics Alternative A', category='GP1', max_points=12)
        Subject.objects.create(code='231', name='Physics', category='GP2', max_points=12)
        Subject.objects.create(code='232', name='Biology', category='GP2', max_points=12)
        Subject.objects.create(code='233', name='Chemistry', category='GP2', max_points=12)
        Subject.objects.create(code='311', name='Geography', category='GP3', max_points=12)
        
        self.subject_cache = {s.code: s for s in Subject.objects.all()}
    
    def test_match_specific_subject(self):
        """Test matching specific subject requirement."""
        student_grades = {'101': 'A', '121': 'B+'}
        requirement = {'type': 'specific', 'subjects': ['101'], 'min_grade': None}
        
        matches = match_requirement(student_grades, requirement, self.subject_cache)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], '101')  # Subject code
        self.assertEqual(matches[0][1], 'A')    # Grade
        self.assertEqual(matches[0][2], 12)     # Points
    
    def test_match_subject_with_alternatives(self):
        """Test matching requirement with multiple alternatives."""
        student_grades = {'101': 'B+', '102': 'A'}
        requirement = {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': None}
        
        matches = match_requirement(student_grades, requirement, self.subject_cache)
        
        # Should return both
        self.assertEqual(len(matches), 2)
    
    def test_match_with_minimum_grade(self):
        """Test matching with minimum grade requirement."""
        student_grades = {'101': 'C+', '102': 'A'}
        requirement = {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': 'B'}
        
        matches = match_requirement(student_grades, requirement, self.subject_cache)
        
        # Only Kiswahili (A) meets minimum grade B
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], '102')
    
    def test_match_group_requirement(self):
        """Test matching group-based requirements."""
        student_grades = {'231': 'A', '232': 'B+', '233': 'B'}
        requirement = {'type': 'group', 'groups': ['GP2'], 'min_grade': None}
        
        matches = match_requirement(student_grades, requirement, self.subject_cache)
        
        # All three sciences are in GP2
        self.assertEqual(len(matches), 3)
    
    def test_match_no_matches(self):
        """Test when student doesn't have required subjects."""
        student_grades = {'311': 'A'}  # Only Geography
        requirement = {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': None}
        
        matches = match_requirement(student_grades, requirement, self.subject_cache)
        
        self.assertEqual(len(matches), 0)


class FindBestSubjectCombinationTests(TestCase):
    """Test finding best 4 subjects for cluster."""
    
    def setUp(self):
        """Create test subjects."""
        Subject.objects.create(code='101', name='English', category='GP1', max_points=12)
        Subject.objects.create(code='121', name='Mathematics Alternative A', category='GP1', max_points=12)
        Subject.objects.create(code='231', name='Physics', category='GP2', max_points=12)
        Subject.objects.create(code='232', name='Biology', category='GP2', max_points=12)
        Subject.objects.create(code='233', name='Chemistry', category='GP2', max_points=12)
        Subject.objects.create(code='311', name='Geography', category='GP3', max_points=12)
        
        self.subject_cache = {s.code: s for s in Subject.objects.all()}
    
    def test_meets_all_requirements(self):
        """Test finding combination when all requirements are met."""
        student_grades = {
            '101': 'B+',   # 10 points
            '121': 'A-',   # 11 points
            '231': 'B',    # 9 points
            '232': 'A',    # 12 points
            '233': 'B+',   # 10 points
        }
        
        requirements = [
            {'type': 'specific', 'subjects': ['101'], 'min_grade': None},
            {'type': 'specific', 'subjects': ['121'], 'min_grade': None},
            {'type': 'specific', 'subjects': ['231', '233'], 'min_grade': None},  # Physics or Chemistry
            {'type': 'group', 'groups': ['GP2'], 'min_grade': None},
        ]
        
        result = find_best_subject_combination(student_grades, requirements, self.subject_cache)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        
        # Should select best subjects
        codes = [subj[0] for subj in result]
        self.assertIn('101', codes)  # English (required)
        self.assertIn('121', codes)  # Math (required)
        self.assertIn('232', codes)  # Biology (best GP2, 12 points)
    
    def test_fails_when_missing_requirement(self):
        """Test that function returns None when ANY requirement is not met."""
        student_grades = {
            '121': 'A',
            '231': 'A',
            '232': 'A',
            '233': 'A',
            # Missing English (101)
        }
        
        requirements = [
            {'type': 'specific', 'subjects': ['101'], 'min_grade': None},  # REQUIRED
            {'type': 'specific', 'subjects': ['121'], 'min_grade': None},
            {'type': 'group', 'groups': ['GP2'], 'min_grade': None},
            {'type': 'group', 'groups': ['GP2'], 'min_grade': None},
        ]
        
        result = find_best_subject_combination(student_grades, requirements, self.subject_cache)
        
        # Should return None because English is missing
        self.assertIsNone(result)
    
    def test_selects_best_from_alternatives(self):
        """Test that best subject is selected from alternatives."""
        student_grades = {
            '101': 'B',    # English: 9 points
            '102': 'A',    # Kiswahili: 12 points
            '121': 'A-',
            '231': 'A',
            '232': 'A',
        }
        
        requirements = [
            {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': None},  # ENG or KIS
            {'type': 'specific', 'subjects': ['121'], 'min_grade': None},
            {'type': 'group', 'groups': ['GP2'], 'min_grade': None},
            {'type': 'group', 'groups': ['GP2'], 'min_grade': None},
        ]
        
        result = find_best_subject_combination(student_grades, requirements, self.subject_cache)
        
        codes = [subj[0] for subj in result]
        # Should select Kiswahili (A, 12 points) over English (B, 9 points)
        self.assertIn('102', codes)
        self.assertNotIn('101', codes)


class CheckSubclusterEligibilityTests(TestCase):
    """Test subcluster eligibility checking."""
    
    def setUp(self):
        """Create test subjects."""
        Subject.objects.create(code='101', name='English', category='GP1', max_points=12)
        Subject.objects.create(code='121', name='Mathematics Alternative A', category='GP1', max_points=12)
        Subject.objects.create(code='231', name='Physics', category='GP2', max_points=12)
        Subject.objects.create(code='232', name='Biology', category='GP2', max_points=12)
        
        self.subject_cache = {s.code: s for s in Subject.objects.all()}
    
    def test_meets_subcluster_requirements(self):
        """Test student meeting subcluster requirements."""
        student_grades = {
            '101': 'A',
            '121': 'A-',
            '231': 'B+',
            '232': 'A',
        }
        
        cluster_subjects = [
            ('101', 'A', 12),
            ('121', 'A-', 11),
            ('231', 'B+', 10),
            ('232', 'A', 12),
        ]
        
        subcluster_reqs = [
            {'type': 'specific', 'subjects': ['121'], 'min_grade': 'B'},  # Math at least B
            {'type': 'none'},
            {'type': 'none'},
            {'type': 'none'},
        ]
        
        result = check_subcluster_eligibility(
            student_grades, subcluster_reqs, cluster_subjects, self.subject_cache
        )
        
        self.assertTrue(result)
    
    def test_fails_minimum_grade(self):
        """Test failing subcluster due to minimum grade."""
        student_grades = {
            '101': 'A',
            '121': 'C+',   # Below minimum
            '231': 'A',
            '232': 'A',
        }
        
        cluster_subjects = [
            ('101', 'A', 12),
            ('121', 'C+', 7),
            ('231', 'A', 12),
            ('232', 'A', 12),
        ]
        
        subcluster_reqs = [
            {'type': 'specific', 'subjects': ['121'], 'min_grade': 'B'},  # Requires B, student has C+
            {'type': 'none'},
            {'type': 'none'},
            {'type': 'none'},
        ]
        
        result = check_subcluster_eligibility(
            student_grades, subcluster_reqs, cluster_subjects, self.subject_cache
        )
        
        self.assertFalse(result)
