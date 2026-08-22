"""
Tests for universities app views and ViewSets.
Tests InstitutionViewSet, ProgrammeViewSet, ClusterGroupViewSet with caching.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from apps.universities.models import Institution, Programme, ProgrammeLevel, ClusterGroup

User = get_user_model()


class InstitutionViewSetTestCase(APITestCase):
    """Test InstitutionViewSet with caching"""
    
    def setUp(self):
        """Create test institutions"""
        self.user = User.objects.create_user(username='test', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.institution1 = Institution.objects.create(
            code="UON",
            name="University of Nairobi",
            location="Nairobi"
        )
        self.institution2 = Institution.objects.create(
            code="KU",
            name="Kenyatta University",
            location="Nairobi"
        )
        cache.clear()
    
    def test_list_institutions(self):
        """Test listing all institutions"""
        response = self.client.get('/api/institutions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_institution_caching(self):
        """Test that institutions are cached"""
        from utils.cache_utils import get_institution_cache_key
        
        # First request
        response1 = self.client.get('/api/institutions/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Check cache
        cache_key = get_institution_cache_key()
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        
        # Second request should use cache
        response2 = self.client.get('/api/institutions/')
        self.assertEqual(response1.data, response2.data)
    
    def test_institution_search(self):
        """Test searching institutions"""
        response = self.client.get('/api/institutions/?search=Nairobi')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return institutions in Nairobi
        self.assertGreater(len(response.data), 0)
    
    def test_search_results_cached_separately(self):
        """Test that search results are cached with different keys"""
        # Make two different searches
        response1 = self.client.get('/api/institutions/?search=Nairobi')
        response2 = self.client.get('/api/institutions/?search=Kenya')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


class ProgrammeViewSetTestCase(APITestCase):
    """Test ProgrammeViewSet with caching and query optimization"""
    
    def setUp(self):
        """Create test programmes"""
        self.user = User.objects.create_user(username='testprog', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.level = ProgrammeLevel.objects.create(
            name="DEGREE"
        )
        self.programme1 = Programme.objects.create(
            name="Computer Science",
            kuccps_code="CS001",
            level=self.level
        )
        self.programme2 = Programme.objects.create(
            name="Information Technology",
            kuccps_code="IT001",
            level=self.level
        )
        cache.clear()
    
    def test_list_programmes(self):
        """Test listing all programmes"""
        response = self.client.get('/api/programmes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_programme_caching(self):
        """Test that programmes are cached"""
        # First request
        response1 = self.client.get('/api/programmes/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Check cache exists
        cached_data = cache.get('programmes_list_all')
        self.assertIsNotNone(cached_data)
        
        # Second request
        response2 = self.client.get('/api/programmes/')
        self.assertEqual(response1.data, response2.data)
    
    def test_programme_search_caching(self):
        """Test that programme searches are cached"""
        response = self.client.get('/api/programmes/?search=Computer')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Search results should be cached with hash
        import hashlib
        query_hash = hashlib.md5('Computer'.encode()).hexdigest()
        cache_key = f'programmes_search_{query_hash}'
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
    
    def test_query_optimization(self):
        """Test that queries use select_related for performance"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Test that we're not hitting N+1 queries
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/programmes/')
            # Should be minimal queries, not one per programme
            # Exact count depends on setup, but should be < 10
            self.assertLess(len(queries), 10)


class ClusterGroupViewSetTestCase(APITestCase):
    """Test ClusterGroupViewSet with caching"""
    
    def setUp(self):
        """Create test cluster groups"""
        self.user = User.objects.create_user(username='testcluster', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.level = ProgrammeLevel.objects.create(
            name="DEGREE"
        )
        self.cluster1 = ClusterGroup.objects.create(
            code="CL1",
            name="Cluster 1",
            level=self.level
        )
        self.cluster2 = ClusterGroup.objects.create(
            code="CL2",
            name="Cluster 2",
            level=self.level
        )
        cache.clear()
    
    def test_list_clusters(self):
        """Test listing all cluster groups"""
        response = self.client.get('/api/clusters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_cluster_caching(self):
        """Test that cluster groups are cached"""
        from utils.cache_utils import get_cluster_cache_key
        
        # First request
        response1 = self.client.get('/api/clusters/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Check cache
        cache_key = get_cluster_cache_key()
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 2)
