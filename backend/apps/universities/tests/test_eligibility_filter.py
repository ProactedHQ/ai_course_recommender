"""
Integration tests for eligibility filter (end-to-end).
"""
from django.test import TestCase
from apps.universities.models import (
    Institution, ProgrammeLevel, ClusterGroup, SubClusterGroup,
    Programme, ProgrammeOffering, CutOffPoint
)
from apps.universities.utils.eligibility_filter import (
    get_eligible_programmes,
    filter_eligible_only
)
from students.models import Subject


class EligibilityFilterIntegrationTests(TestCase):
    """Integration tests for complete eligibility workflow."""
    
    @classmethod
    def setUpTestData(cls):
        """Create comprehensive test data once for all tests."""
        # Create subjects
        Subject.objects.create(code='101', name='English', category='GP1', max_points=12)
        Subject.objects.create(code='102', name='Kiswahili', category='GP1', max_points=12)
        Subject.objects.create(code='121', name='Mathematics Alternative A', category='GP1', max_points=12)
        Subject.objects.create(code='231', name='Physics', category='GP2', max_points=12)
        Subject.objects.create(code='232', name='Biology', category='GP2', max_points=12)
        Subject.objects.create(code='233', name='Chemistry', category='GP2', max_points=12)
        Subject.objects.create(code='311', name='Geography', category='GP3', max_points=12)
        Subject.objects.create(code='571', name='Business Studies', category='GP4', max_points=12)
        
        # Create institutions
        cls.institution1 = Institution.objects.create(
            name='University of Nairobi',
            code='C001',
            institution_type='PUBLIC',
            location='Nairobi'
        )
        
        cls.institution2 = Institution.objects.create(
            name='Kenyatta University',
            code='C002',
            institution_type='PUBLIC',
            location='Nairobi'
        )
        
        # Create programme level
        cls.level = ProgrammeLevel.objects.create(name='DEGREE')
        
        # Create cluster: Sciences (requires ENG, MATH, PHY/CHEM, BIO/GEO)
        cls.cluster_science = ClusterGroup.objects.create(
            level=cls.level,
            code='4',
            name='Biological & Physical Sciences',
            subject_1='ENG/KIS',
            subject_2='MATH',
            subject_3='PHY/CHEM',
            subject_4='BIO/GEO'
        )
        
        # Create subcluster 4A (no additional requirements)
        cls.subcluster_4a = SubClusterGroup.objects.create(
            cluster=cls.cluster_science,
            code='4A',
            name='Physical Sciences',
            subject_1='null',
            subject_2='null',
            subject_3='null',
            subject_4='null'
        )
        
        # Create subcluster 4B (requires PHYSICS at least B)
        cls.subcluster_4b = SubClusterGroup.objects.create(
            cluster=cls.cluster_science,
            code='4B',
            name='Geosciences',
            subject_1='PHY - B (PLAIN)',
            subject_2='null',
            subject_3='null',
            subject_4='null'
        )
        
        # Create programmes
        cls.programme_physics = Programme.objects.create(
            level=cls.level,
            sub_cluster=cls.subcluster_4a,
            kuccps_code='C001-01-001',
            name='Bachelor of Science (Physics)',
            minimum_mean_grade='C+'
        )
        
        cls.programme_astronomy = Programme.objects.create(
            level=cls.level,
            sub_cluster=cls.subcluster_4b,
            kuccps_code='C001-01-002',
            name='Bachelor of Science (Astronomy)',
            minimum_mean_grade='B-'
        )
        
        # Create programme offerings
        cls.offering_physics_uon = ProgrammeOffering.objects.create(
            programme=cls.programme_physics,
            institution=cls.institution1
        )
        
        cls.offering_astronomy_uon = ProgrammeOffering.objects.create(
            programme=cls.programme_astronomy,
            institution=cls.institution1
        )
        
        cls.offering_physics_ku = ProgrammeOffering.objects.create(
            programme=cls.programme_physics,
            institution=cls.institution2
        )
        
        # Create cutoff points
        CutOffPoint.objects.create(
            programme_offering=cls.offering_physics_uon,
            year=2024,
            cutoff_type='weighted_cluster_points',
            weighted_cluster_points=35.5
        )
        
        CutOffPoint.objects.create(
            programme_offering=cls.offering_astronomy_uon,
            year=2024,
            cutoff_type='weighted_cluster_points',
            weighted_cluster_points=38.0
        )
        
        CutOffPoint.objects.create(
            programme_offering=cls.offering_physics_ku,
            year=2024,
            cutoff_type='weighted_cluster_points',
            weighted_cluster_points=32.0
        )
    
    def test_student_meets_all_requirements(self):
        """Test student who meets all requirements."""
        student_grades = {
            '101': 'A',    # English
            '121': 'A-',   # Mathematics
            '231': 'A',    # Physics
            '232': 'A',    # Biology
            '233': 'B+',   # Chemistry
            '311': 'B',    # Geography
            '571': 'B-',   # Business
        }
        
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='DEGREE'
        )
        
        # Should have results
        self.assertGreater(len(results), 0)
        
        # Check that Physics programme is included
        physics_results = [r for r in results if r['programme'].id == self.programme_physics.id]
        self.assertGreater(len(physics_results), 0)
        
        # Check Astronomy (requires Physics B+)
        astronomy_results = [r for r in results if r['programme'].id == self.programme_astronomy.id]
        self.assertGreater(len(astronomy_results), 0)
    
    def test_student_fails_subcluster_requirement(self):
        """Test student who meets cluster but fails subcluster."""
        student_grades = {
            '101': 'A',
            '121': 'A',
            '231': 'C+',   # Physics C+ (Astronomy requires B)
            '232': 'A',
            '233': 'A',
            '311': 'A',
            '571': 'A',
        }
        
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='DEGREE'
        )
        
        # Should be eligible for Physics (no specific subcluster requirement)
        physics_results = [r for r in results if r['programme'].id == self.programme_physics.id]
        self.assertGreater(len(physics_results), 0)
        
        # Should NOT be eligible for Astronomy (requires Physics B)
        astronomy_results = [r for r in results if r['programme'].id == self.programme_astronomy.id]
        self.assertEqual(len(astronomy_results), 0)
    
    def test_filter_eligible_only(self):
        """Test filtering eligible programmes."""
        student_grades = {
            '101': 'B+',
            '121': 'A-',
            '231': 'B',
            '232': 'A',
            '233': 'B+',
            '311': 'C+',
            '571': 'B-',
        }
        
        all_results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='DEGREE'
        )
        
        eligible_only = filter_eligible_only(all_results)
        
        # Eligible programmes should have is_eligible = True
        for prog in eligible_only:
            self.assertTrue(prog['is_eligible'])
            self.assertGreaterEqual(prog['student_points'], prog['cutoff_points'])
    
    def test_cutoff_year_fallback(self):
        """Test cutoff year fallback when target year not available."""
        # Create older cutoff
        CutOffPoint.objects.create(
            programme_offering=self.offering_physics_uon,
            year=2020,
            cutoff_type='weighted_cluster_points',
            weighted_cluster_points=30.0
        )
        
        student_grades = {
            '101': 'A',
            '121': 'A',
            '231': 'A',
            '232': 'A',
            '233': 'A',
            '311': 'A',
            '571': 'A',
        }
        
        # Request year 2025 (doesn't exist, should fall back)
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2025,
            level_name='DEGREE'
        )
        
        # Should still return results using fallback cutoffs
        self.assertGreater(len(results), 0)
        
        # Check that cutoff year is not 2025
        for result in results:
            if result['cutoff_points'] is not None:
                self.assertLessEqual(result['cutoff_year'], 2024)
    
    def test_aggregate_calculation(self):
        """Test that aggregate is correctly calculated."""
        student_grades = {
            '101': 'A',    # 12
            '121': 'A',    # 12
            '231': 'A',    # 12
            '232': 'A',    # 12
            '233': 'A',    # 12
            '311': 'A',    # 12
            '571': 'A',    # 12
        }
        
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='DEGREE'
        )
        
        # Check aggregate in results
        for result in results:
            self.assertEqual(result['aggregate'], 84)  # 7 × 12 = 84
    
    def test_cluster_points_calculation(self):
        """Test that cluster points are calculated correctly."""
        student_grades = {
            '101': 'A',    # 12
            '121': 'A',    # 12
            '231': 'A',    # 12
            '232': 'A',    # 12
            '233': 'B',    # 9
            '311': 'B',    # 9
            '571': 'B',    # 9
        }
        
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='DEGREE'
        )
        
        # Check that cluster points are reasonable (should be > 0 and <= 48)
        for result in results:
            self.assertGreater(result['student_points'], 0)
            self.assertLessEqual(result['student_points'], 48)


class EligibilityFilterEdgeCasesTests(TestCase):
    """Test edge cases in eligibility filtering."""
    
    def test_empty_student_grades(self):
        """Test with no student grades."""
        results = get_eligible_programmes(
            student_grades={},
            target_year=2024,
            level_name='DEGREE'
        )
        
        # Should return empty or all ineligible
        eligible = filter_eligible_only(results)
        self.assertEqual(len(eligible), 0)
    
    def test_invalid_level_name(self):
        """Test with invalid level name."""
        student_grades = {'101': 'A', '121': 'A', '231': 'A', '232': 'A'}
        
        results = get_eligible_programmes(
            student_grades=student_grades,
            target_year=2024,
            level_name='INVALID'
        )
        
        # Should return empty (no programmes at that level)
        self.assertEqual(len(results), 0)
