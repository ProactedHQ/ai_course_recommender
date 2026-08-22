"""
Tests for students app views and ViewSets.
Tests SubjectViewSet, StudentProfileViewSet, AcademicResultViewSet, PromptSubmissionViewSet.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from apps.students.models import Subject, StudentProfile, AcademicResult, PromptSubmission
import json

User = get_user_model()


class SubjectViewSetTestCase(APITestCase):
    """Test SubjectViewSet including caching functionality"""
    
    def setUp(self):
        """Create test subjects"""
        self.user = User.objects.create_user(username='testsubject', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.subject1 = Subject.objects.create(
            code="101",
            name="English",
            category="1"
        )
        self.subject2 = Subject.objects.create(
            code="121",
            name="Mathematics",
            category="2"
        )
        cache.clear()  # Clear cache before each test
    
    def test_list_subjects(self):
        """Test listing all subjects"""
        response = self.client.get('/api/subjects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'English')
    
    def test_subject_caching(self):
        """Test that subjects are cached after first request"""
        from utils.cache_utils import get_subject_cache_key
        
        # First request - cache miss
        response1 = self.client.get('/api/subjects/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Check cache was populated
        cache_key = get_subject_cache_key()
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 2)
        
        # Second request - cache hit
        response2 = self.client.get('/api/subjects/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)


class StudentProfileViewSetTestCase(APITestCase):
    """Test StudentProfileViewSet with authentication"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_profile(self):
        """Test creating a student profile"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'year_of_study': 2024
        }
        response = self.client.post('/api/profiles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudentProfile.objects.count(), 1)
        self.assertEqual(StudentProfile.objects.first().user, self.user)
    
    def test_profile_requires_authentication(self):
        """Test that profile creation requires authentication"""
        self.client.force_authenticate(user=None)
        data = {'first_name': 'John', 'last_name': 'Doe'}
        response = self.client.post('/api/profiles/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_can_only_see_own_profile(self):
        """Test that users can only see their own profile"""
        # Create profile for user1
        profile1 = StudentProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe'
        )
        
        # Create another user with profile
        user2 = User.objects.create_user(username='user2', password='pass123')
        profile2 = StudentProfile.objects.create(
            user=user2,
            first_name='Jane',
            last_name='Smith'
        )
        
        # User1 should only see their profile
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'John')


class PromptSubmissionViewSetTestCase(APITestCase):
    """Test PromptSubmissionViewSet with rate limiting and WebSocket integration"""
    
    def setUp(self):
        """Create test user and clear cache"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cache.clear()
    
    def test_create_submission(self):
        """Test creating a prompt submission"""
        data = {
            'prompt_text': 'I want to study Computer Science',
            'user_preferences': {'field': 'technology'}
        }
        response = self.client.post('/api/prompts/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('received', response.data)
        self.assertIn('submission_id', response.data)
        self.assertIn('recommendations', response.data)
        self.assertEqual(PromptSubmission.objects.count(), 1)
    
    def test_rate_limiting(self):
        """Test that rate limiting works (5 requests per minute)"""
        data = {
            'prompt_text': 'Test prompt',
            'user_preferences': {}
        }
        
        # Make 5 requests (should all succeed)
        for i in range(5):
            response = self.client.post('/api/prompts/', data)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        
        # 6th request should be rate limited
        response = self.client.post('/api/prompts/', data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)
        self.assertIn('Rate limit exceeded', response.data['error'])
    
    def test_submission_requires_authentication(self):
        """Test that submissions require authentication"""
        self.client.force_authenticate(user=None)
        data = {'prompt_text': 'Test', 'user_preferences': {}}
        response = self.client.post('/api/prompts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_user_submissions(self):
        """Test listing user's own submissions"""
        # Create submissions for user
        PromptSubmission.objects.create(
            user=self.user,
            prompt_text='Test 1',
            result={'test': 'data'}
        )
        PromptSubmission.objects.create(
            user=self.user,
            prompt_text='Test 2',
            result={'test': 'data2'}
        )
        
        # Create submission for another user
        user2 = User.objects.create_user(username='user2', password='pass')
        PromptSubmission.objects.create(
            user=user2,
            prompt_text='Other user',
            result={}
        )
        
        # User should only see their own submissions
        response = self.client.get('/api/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class AcademicResultViewSetTestCase(APITestCase):
    """Test AcademicResultViewSet"""
    
    def setUp(self):
        """Create test user and student profile"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe'
        )
        self.subject = Subject.objects.create(
            code="101",
            name="English"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_academic_result(self):
        """Test creating an academic result"""
        data = {
            'student': self.student_profile.id,
            'subject': self.subject.id,
            'grade': 'A'
        }
        response = self.client.post('/api/grades/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AcademicResult.objects.count(), 1)
