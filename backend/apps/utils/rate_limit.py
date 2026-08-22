"""
Rate limiting decorators for API views.
Prevents abuse and ensures fair resource usage.
"""
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import time


def rate_limit(key_prefix='api', rate='10/m', methods=None):
    """
    Rate limiting decorator for DRF ViewSets.
    
    Args:
        key_prefix (str): Prefix for cache key
        rate (str): Rate limit (e.g., '10/m' = 10 per minute, '100/h' = 100 per hour)
        methods (list): HTTP methods to rate limit (default: ['POST', 'PUT', 'PATCH', 'DELETE'])
    
    Example:
        @rate_limit(key_prefix='recommendation', rate='5/m', methods=['POST'])
        def create(self, request):
            ...
    """
    if methods is None:
        methods = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Parse rate limit
    count, period = rate.split('/')
    count = int(count)
    
    period_seconds = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }.get(period, 60)
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Skip rate limiting if not enabled or Redis unavailable
            if not getattr(settings, 'REDIS_AVAILABLE', False):
                return func(self, request, *args, **kwargs)
            
            # Check if method should be rate limited
            if request.method not in methods:
                return func(self, request, *args, **kwargs)
            
            # Get user identifier
            if request.user and request.user.is_authenticated:
                user_id = str(request.user.id)
            else:
                # Use IP address for anonymous users
                user_id = get_client_ip(request)
            
            # Create cache key
            cache_key = f'ratelimit_{key_prefix}_{user_id}_{request.method}'
            
            # Get current request count
            request_data = cache.get(cache_key, {'count': 0, 'reset': time.time() + period_seconds})
            
            # Check if we need to reset the counter
            if time.time() > request_data['reset']:
                request_data = {'count': 0, 'reset': time.time() + period_seconds}
            
            # Check rate limit
            if request_data['count'] >= count:
                return Response({
                    'error': 'Rate limit exceeded',
                    'detail': f'Maximum {count} requests per {period} allowed',
                    'retry_after': int(request_data['reset'] - time.time())
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment counter
            request_data['count'] += 1
            cache.set(cache_key, request_data, period_seconds)
            
            # Call the actual function
            response = func(self, request, *args, **kwargs)
            
            # Add rate limit headers to response
            try:
                if hasattr(response, 'headers') or isinstance(response, Response):
                    response['X-RateLimit-Limit'] = str(count)
                    response['X-RateLimit-Remaining'] = str(max(0, count - request_data['count']))
                    response['X-RateLimit-Reset'] = str(int(request_data['reset']))
            except Exception:
                pass # Fail silently if headers can't be set
                
            return response
        
        return wrapper
    return decorator


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
