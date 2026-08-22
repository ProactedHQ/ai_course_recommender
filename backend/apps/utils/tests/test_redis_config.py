"""
Tests for Redis configuration utilities.
Tests Redis detection and fallback functionality.
"""
from django.test import TestCase
from django.core.cache import cache
from utils.redis_config import is_redis_available, get_cache_backend, get_channel_layers


class RedisConfigTestCase(TestCase):
    """Test Redis configuration and fallback"""
    
    def test_is_redis_available(self):
        """Test Redis availability detection"""
        result = is_redis_available()
        # Result should be boolean
        self.assertIsInstance(result, bool)
        # If Redis is available, it should return True
        # If not available, should return False without crashing
    
    def test_get_cache_backend(self):
        """Test cache backend configuration"""
        backend_config = get_cache_backend()
        
        # Should return a dict
        self.assertIsInstance(backend_config, dict)
        
        # Should have 'default' key
        self.assertIn('default', backend_config)
        
        # Default should have BACKEND key
        self.assertIn('BACKEND', backend_config['default'])
        
        # Backend should be either Redis or LocMem
        backend = backend_config['default']['BACKEND']
        valid_backends = [
            'django_redis.cache.RedisCache',
            'django.core.cache.backends.locmem.LocMemCache'
        ]
        self.assertIn(backend, valid_backends)
    
    def test_get_channel_layers(self):
        """Test channel layers configuration"""
        channels_config = get_channel_layers()
        
        # Should return a dict
        self.assertIsInstance(channels_config, dict)
        
        # Should have 'default' key
        self.assertIn('default', channels_config)
        
        # Should have BACKEND key
        self.assertIn('BACKEND', channels_config['default'])
        
        # Backend should be either Redis or InMemory
        backend = channels_config['default']['BACKEND']
        valid_backends = [
            'channels_redis.core.RedisChannelLayer',
            'channels.layers.InMemoryChannelLayer'
        ]
        self.assertIn(backend, valid_backends)
    
    def test_cache_operations(self):
        """Test basic cache operations work regardless of backend"""
        # Set a cache value
        cache.set('test_key', 'test_value', 60)
        
        # Retrieve it
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # Delete it
        cache.delete('test_key')
        value = cache.get('test_key')
        self.assertIsNone(value)
