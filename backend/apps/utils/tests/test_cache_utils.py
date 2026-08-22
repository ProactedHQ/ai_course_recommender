"""
Tests for cache utilities.
Tests cache key generation, invalidation, and helper functions.
"""
from django.test import TestCase
from django.core.cache import cache
from utils.cache_utils import (
    get_subject_cache_key,
    get_institution_cache_key,
    get_cluster_cache_key,
    get_programme_cache_key,
    invalidate_subject_cache,
    invalidate_institution_cache,
    invalidate_cluster_cache,
    invalidate_cache_pattern,
    invalidate_all_caches
)


class CacheUtilsTestCase(TestCase):
    """Test cache utility functions"""
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
    
    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()
    
    def test_get_subject_cache_key(self):
        """Test subject cache key generation"""
        key = get_subject_cache_key()
        self.assertEqual(key, 'subjects_list_all')
    
    def test_get_institution_cache_key_no_search(self):
        """Test institution cache key without search"""
        key = get_institution_cache_key()
        self.assertEqual(key, 'institutions_list_all')
    
    def test_get_institution_cache_key_with_search(self):
        """Test institution cache key with search query"""
        key = get_institution_cache_key('Nairobi')
        self.assertTrue(key.startswith('institutions_search_'))
        
        # Same search should produce same key
        key2 = get_institution_cache_key('Nairobi')
        self.assertEqual(key, key2)
        
        # Different search should produce different key
        key3 = get_institution_cache_key('Mombasa')
        self.assertNotEqual(key, key3)
    
    def test_get_cluster_cache_key(self):
        """Test cluster cache key generation"""
        key = get_cluster_cache_key()
        self.assertEqual(key, 'clusters_list_all')
    
    def test_get_programme_cache_key_variations(self):
        """Test programme cache key with different parameters"""
        # No parameters
        key1 = get_programme_cache_key()
        self.assertEqual(key1, 'programmes_list_all')
        
        # With search only
        key2 = get_programme_cache_key(search_query='Computer')
        self.assertTrue('search_' in key2)
        
        # With cluster only
        key3 = get_programme_cache_key(cluster_id=1)
        self.assertTrue('cluster_1' in key3)
        
        # With both
        key4 = get_programme_cache_key(search_query='Computer', cluster_id=1)
        self.assertTrue('search_' in key4)
        self.assertTrue('cluster_1' in key4)
    
    def test_invalidate_subject_cache(self):
        """Test subject cache invalidation"""
        # Set cache
        cache_key = get_subject_cache_key()
        cache.set(cache_key, {'test': 'data'})
        self.assertIsNotNone(cache.get(cache_key))
        
        # Invalidate
        invalidate_subject_cache()
        self.assertIsNone(cache.get(cache_key))
    
    def test_invalidate_cluster_cache(self):
        """Test cluster cache invalidation"""
        # Set cache
        cache_key = get_cluster_cache_key()
        cache.set(cache_key, {'test': 'data'})
        self.assertIsNotNone(cache.get(cache_key))
        
        # Invalidate
        invalidate_cluster_cache()
        self.assertIsNone(cache.get(cache_key))
    
    def test_invalidate_all_caches(self):
        """Test clearing all caches"""
        # Set multiple cache entries
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        
        # Invalidate all
        result = invalidate_all_caches()
        self.assertTrue(result)
        
        # All should be gone
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))
        self.assertIsNone(cache.get('key3'))
