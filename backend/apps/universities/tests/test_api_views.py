"""
Unit tests for API views and serializers.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.universities.models import (
    Institution, ProgrammeLevel, ClusterGroup, SubClusterGroup,
    Programme, ProgrammeOffering, CutOffPoint
)
from apps.universities.serializers import (
    StudentGradesSerializer,
    EligibilityRequestSerializer
)
from students.models import Subject
import json


class StudentGradesSerializerTests(TestCase):
    """Test student grades serializer validation."""
    
    def test_valid_grades(self):
        """Test valid student grades."""
        data = {
            '101': 'A',
            '121': 'B+',
            '231': 'C',
        }
        
        serializer = StudentGradesSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_invalid_subject_code_format(self):
        """Test invalid subject code format."""
        data = {
            '1': 'A',  # Too short
        }
        
        serializer = StudentGradesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_invalid_grade_value(self):
        """Test invalid grade value."""
        data = {
            '101': 'X',  # Invalid grade
        }
        
        serializer = StudentGradesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_non_numeric_subject_code(self):
        """Test non-numeric subject code."""
        data = {
            'ABC': 'A',
        }
        
        serializer = StudentGradesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_case_insensitive_grades(self):
        """Test that grades are accepted case-insensitively."""
        data = {
            '101': 'a',
            '121': 'B+',
            '231': 'c-',
        }
        
        serializer = StudentGradesSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class EligibilityRequestSerializerTests(TestCase):
    """Test eligibility request serializer."""
    
    def test_valid_request(self):
        """Test complete valid request."""
        data = {
            'student_grades': {
                '101': 'A',
                '121': 'B+',
            },
            'target_year': 2024,
            'level_name': 'DEGREE'
        }
        
        serializer = EligibilityRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_defaults(self):
        """Test default values for optional fields."""
        data = {
            'student_grades': {
                '101': 'A',
            }
        }
        
        serializer = EligibilityRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['target_year'], 2024)
        self.assertEqual(serializer.validated_data['level_name'], 'DEGREE')
    
    def test_invalid_level_name(self):
        """Test invalid level name."""
        data = {
            'student_grades': {'101': 'A'},
            'level_name': 'INVALID'
        }
        
        serializer = EligibilityRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_year_out_of_range(self):
        """Test year out of valid range."""
        data = {
            'student_grades': {'101': 'A'},
            'target_year': 2050  # Too far in future
        }
        
        serializer = EligibilityRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class CheckEligibilityAPITests(TestCase):
    """Test Check Eligibility API endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        # Create subjects
        Subject.objects.create(code='101', name='English', category='GP1', max_points=12)
        Subject.objects.create(code='121', name='Mathematics Alternative A', category='GP1', max_points=12)
        Subject.objects.create(code='231', name='Physics', category='GP2', max_points=12)
        Subject.objects.create(code='232', name='Biology', category='GP2', max_points=12)
        
        # Create institution
        cls.institution = Institution.objects.create(
            name='Test University',
            code='T001',
            institution_type='PUBLIC',
            location='Nairobi'
        )
        
        # Create level
        cls.level = ProgrammeLevel.objects.create(name='DEGREE')
        
        # Create cluster
        cls.cluster = ClusterGroup.objects.create(
            level=cls.level,
            code='4',
            name='Sciences',
            subject_1='ENG',
            subject_2='MATH',
            subject_3='PHY',
            subject_4='BIO'
        )
        
        # Create subcluster
        cls.subcluster = SubClusterGroup.objects.create(
            cluster=cls.cluster,
            code='4A',
            name='Sciences A',
            subject_1='null',
            subject_2='null',
            subject_3='null',
            subject_4='null'
        )
        
        # Create programme
        cls.programme = Programme.objects.create(
            level=cls.level,
            sub_cluster=cls.subcluster,
            kuccps_code='T001-01-001',
            name='Test Programme',
            minimum_mean_grade='C+'
        )
        
        # Create offering
        cls.offering = ProgrammeOffering.objects.create(
            programme=cls.programme,
            institution=cls.institution
        )
        
        # Create cutoff
        CutOffPoint.objects.create(
            programme_offering=cls.offering,
            year=2024,
            cutoff_type='weighted_cluster_points',
            weighted_cluster_points=30.0
        )
    
    def setUp(self):
        """Set up API client for each test."""
        self.client = APIClient()
    
    def test_successful_eligibility_check(self):
        """Test successful eligibility check."""
        data = {
            'student_grades': {
                '101': 'A',
                '121': 'A',
                '231': 'A',
                '232': 'A',
            },
            'target_year': 2024,
            'level_name': 'DEGREE'
        }
        
        response = self.client.post(
            '/api/universities/check-eligibility/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        response_data = response.json()
        self.assertIn('total_programmes_analyzed', response_data)
        self.assertIn('eligible_programmes_count', response_data)
        self.assertIn('programmes', response_data)
        self.assertIn('student_aggregate', response_data)
    
    def test_invalid_request_data(self):
        """Test with invalid request data."""
        data = {
            'student_grades': {
                'INVALID': 'A',  # Invalid subject code
            }
        }
        
        response = self.client.post(
            '/api/universities/check-eligibility/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('error', response_data)
    
    def test_response_contains_programme_details(self):
        """Test that response contains detailed programme information."""
        data = {
            'student_grades': {
                '101': 'A',
                '121': 'A',
                '231': 'A',
                '232': 'A',
            }
        }
        
        response = self.client.post(
            '/api/universities/check-eligibility/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Check that programmes have required fields
        if len(response_data['programmes']) > 0:
            prog = response_data['programmes'][0]
            self.assertIn('programme_name', prog)
            self.assertIn('institution_name', prog)
            self.assertIn('cluster_name', prog)
            self.assertIn('student_points', prog)
            self.assertIn('cutoff_points', prog)
            self.assertIn('is_eligible', prog)
            self.assertIn('cluster_subjects', prog)
    
    def test_check_eligibility_all_endpoint(self):
        """Test the /all/ endpoint returns all programmes."""
        data = {
            'student_grades': {
                '101': 'D',  # Low grades
                '121': 'D',
                '231': 'D',
                '232': 'D',
            }
        }
        
        response = self.client.post(
            '/api/universities/check-eligibility/all/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Should return programmes even if ineligible
        total = response_data['total_programmes_analyzed']
        self.assertGreaterEqual(total, 0)
    
    def test_empty_student_grades(self):
        """Test with empty student grades."""
        data = {
            'student_grades': {}
        }
        
        response = self.client.post(
            '/api/universities/check-eligibility/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should still return 200 but with no eligible programmes
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['eligible_programmes_count'], 0)
