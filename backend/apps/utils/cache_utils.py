"""
Cache utility functions for AI Course Recommender backend.
Provides cache invalidation and key generation utilities.
"""
from django.core.cache import cache
import hashlib
import logging

logger = logging.getLogger(__name__)


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern.
    
    Args:
        pattern (str): Pattern to match (e.g., 'subjects_*')
    
    Note: This requires django-redis backend with pattern deletion support
    """
    try:
        cache.delete_pattern(pattern)
        logger.info(f"Invalidated cache for pattern: {pattern}")
        return True
    except AttributeError:
        # If using LocMemCache, it doesn't support delete_pattern
        logger.warning(f"Cache backend doesn't support pattern deletion: {pattern}")
        return False
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
        return False


def invalidate_all_caches():
    """Clear all caches - use sparingly!"""
    try:
        cache.clear()
        logger.warning("ALL CACHES CLEARED")
        return True
    except Exception as e:
        logger.error(f"Failed to clear all caches: {e}")
        return False


# Cache key generators
def get_subject_cache_key():
    """Generate cache key for subjects list"""
    return 'subjects_list_all'


def get_institution_cache_key(search_query=''):
    """
    Generate cache key for institutions list.
    
    Args:
        search_query (str): Optional search query to include in cache key
    """
    if search_query:
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        return f'institutions_search_{query_hash}'
    return 'institutions_list_all'


def get_cluster_cache_key():
    """Generate cache key for cluster groups list"""
    return 'clusters_list_all'


def get_programme_cache_key(search_query='', cluster_id=None):
    """
    Generate cache key for programmes list.
    
    Args:
        search_query (str): Optional search query
        cluster_id (int): Optional cluster filter
    """
    if search_query or cluster_id:
        cache_key_parts = ['programmes']
        if search_query:
            query_hash = hashlib.md5(search_query.encode()).hexdigest()
            cache_key_parts.append(f'search_{query_hash}')
        if cluster_id:
            cache_key_parts.append(f'cluster_{cluster_id}')
        return '_'.join(cache_key_parts)
    return 'programmes_list_all'


def invalidate_subject_cache():
    """Invalidate subject-related caches"""
    cache.delete(get_subject_cache_key())
    logger.info("Invalidated subject cache")


def invalidate_institution_cache():
    """Invalidate institution-related caches"""
    invalidate_cache_pattern('institutions_*')


def invalidate_programme_cache():
    """Invalidate programme-related caches"""
    invalidate_cache_pattern('programmes_*')


def invalidate_cluster_cache():
    """Invalidate cluster-related caches"""
    cache.delete(get_cluster_cache_key())
    logger.info("Invalidated cluster cache")
