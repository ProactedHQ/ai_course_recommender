"""
Redis availability detection and configuration.
Provides graceful fallback for development environments without Redis.

Used by settings.py at startup. REDIS_URL (Upstash in production) or REDIS_HOST/PORT.
When Redis is reachable: django-redis cache, Channels layer, rate limiting on.
When it is not: LocMem cache (per process), no WebSocket progress, no rate limiting.
"""
import os
import sys


def is_redis_available():
    """
    Check if Redis is available and running.
    
    Returns:
        bool: True if Redis is available, False otherwise
    """
    try:
        import redis
        if os.environ.get('REDIS_URL'):
            client = redis.from_url(
                os.environ.get('REDIS_URL'),
                socket_connect_timeout=2,
                socket_timeout=2
            )
        else:
            client = redis.Redis(
                host=os.environ.get('REDIS_HOST', '127.0.0.1'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                db=0,
                socket_connect_timeout=2,
                socket_timeout=2
            )
        client.ping()
        return True
    except (ImportError, redis.ConnectionError, redis.TimeoutError, Exception) as e:
        print(f"⚠️  Redis not available: {e}", file=sys.stderr)
        print("   Running without Redis caching and WebSocket support.", file=sys.stderr)
        print("   (This is normal for Windows development environments)", file=sys.stderr)
        return False


def get_cache_backend():
    """
    Get appropriate cache backend based on Redis availability.
    
    Returns:
        dict: Cache configuration for Django settings
    """
    if is_redis_available():
        return {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    'RETRY_ON_TIMEOUT': True,
                    'MAX_CONNECTIONS': 50,
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                },
                'KEY_PREFIX': 'ai_course_recommender',
                'TIMEOUT': 60 * 15,  # 15 minutes default
            }
        }
    else:
        # Fallback to in-memory cache (no persistence, but works without Redis)
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
                'TIMEOUT': 60 * 15,
            }
        }


def get_channel_layers():
    """
    Get Channel Layers configuration based on Redis availability.
    
    Returns:
        dict: Channel Layers configuration or None
    """
    if is_redis_available():
        return {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')],
                    'capacity': 1500,
                    'expiry': 10,
                },
            },
        }
    else:
        # Use in-memory channel layer (development only, doesn't work across multiple workers)
        return {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer'
            },
        }
