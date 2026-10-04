"""
WSGI config for course_recomeder_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
os.environ.setdefault("APP_ENV", "production")  # web server entry point: production unless told otherwise

application = get_wsgi_application()
