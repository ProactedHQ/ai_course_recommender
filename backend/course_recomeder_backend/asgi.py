"""
ASGI config for course_recomeder_backend project.
Enables WebSocket support via Django Channels (if Redis is available).
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import settings after Django setup
from django.conf import settings

# Conditionally add WebSocket routing if Redis is available
if getattr(settings, 'REDIS_AVAILABLE', False):
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from apps.students import routing as student_routing
    
    application = ProtocolTypeRouter({
        'http': django_asgi_app,
        'websocket': AuthMiddlewareStack(
            URLRouter(
                student_routing.websocket_urlpatterns
            )
        ),
    })
else:
    # Fallback to HTTP only (no WebSocket support)
    application = django_asgi_app

