"""
Django production settings for course_recomeder_backend (cPanel Passenger / WSGI).

Assumptions:
- API is served at: https://api.proactedai.co.ke
- Frontend is served at: https://proactedai.co.ke
- Database is Supabase Postgres via DATABASE_URL (required)
- Redis caching is Upstash via REDIS_URL (optional; falls back to LocMem)
- Authentication uses Supabase JWT via SUPABASE_JWT_SECRET

Important:
- Do NOT hardcode secrets in this file.
- Set environment variables in cPanel "Setup Python App".
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import timedelta

import dj_database_url

# -----------------------------------------------------------------------------
# Base paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "apps"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from utils.redis_config import is_redis_available, get_cache_backend, get_channel_layers
REDIS_AVAILABLE = is_redis_available()

# -----------------------------------------------------------------------------
# Environment helpers
# -----------------------------------------------------------------------------
def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [v.strip() for v in raw.split(",") if v.strip()]

def require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

# -----------------------------------------------------------------------------
# Core security / debug
# -----------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = require_env("SECRET_KEY")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "api.proactedai.co.ke")

# If you're behind a proxy/CDN and see HTTPS redirect loops, uncomment and set properly.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -----------------------------------------------------------------------------
# Installed apps
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    *(['daphne'] if REDIS_AVAILABLE else []),

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "csp",  # required because CSP middleware is enabled below

    # Local apps
    "apps.users.apps.UsersConfig",
    "apps.students.apps.StudentsConfig",
    "apps.universities.apps.UniversitiesConfig",
    "proacted_recommender_engine.apps.ProactedRecommenderEngineConfig",
    'apps.blog.apps.BlogConfig',
    'subscriptions',

    *(['channels'] if REDIS_AVAILABLE else []),
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    # CSP (Content Security Policy)
    "csp.middleware.CSPMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------------------------------------------------------
# URL / Templates / WSGI
# -----------------------------------------------------------------------------
ROOT_URLCONF = "course_recomeder_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# ASGI / WSGI Application
if REDIS_AVAILABLE:
    ASGI_APPLICATION = "course_recomeder_backend.asgi.application"
else:
    # cPanel Passenger runs WSGI
    WSGI_APPLICATION = "course_recomeder_backend.wsgi.application"

# -----------------------------------------------------------------------------
# Database (required)
# -----------------------------------------------------------------------------
DATABASE_URL = require_env("DATABASE_URL")

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL.split(' ')[0] if ' ' in DATABASE_URL else DATABASE_URL,
        conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600")),
    )
}
# Supabase: enforce SSL
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"].update({"sslmode": "require"})

# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "users.CustomUser"

# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.users.auth.supabase.SupabaseJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# -----------------------------------------------------------------------------
# drf-spectacular (Swagger/OpenAPI)
# -----------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "AIACADEMIA - PROACTED API Docs",
    "DESCRIPTION": (
        "Detailed API documentation for the AI Course Recommender system. "
        "All protected endpoints require a Supabase JWT Bearer Token."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_PATCH": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"bearerAuth": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your Supabase Access Token (JWT) to authorize requests.",
            }
        }
    },
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "/static/drf_spectacular/logo.png",
    "ENUM_NAME_OVERRIDES": {
        "CategoryEnum": "students.models.Subject.CATEGORY_CHOICES",
    },
}

# -----------------------------------------------------------------------------
# JWT / Supabase signing secret
# -----------------------------------------------------------------------------
SUPABASE_JWT_SECRET = require_env("SUPABASE_JWT_SECRET")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SUPABASE_JWT_SECRET,
}

# -----------------------------------------------------------------------------
# CORS (Frontend origins)
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "https://proactedai.co.ke",
    "https://www.proactedai.co.ke",
]

# Optional local dev override (keep disabled on cPanel unless needed)
if env_bool("ALLOW_LOCALHOST_CORS", False):
    CORS_ALLOWED_ORIGINS += ["http://localhost:5173"]

# If you ever use cookies/sessions across origins, you would also need:
# CORS_ALLOW_CREDENTIALS = True

# -----------------------------------------------------------------------------
# Static files
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# -----------------------------------------------------------------------------
# Security headers (Production)
# -----------------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Cookies (Admin site uses session/csrf cookies)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Admin typically needs CSRF cookie accessible by browser
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# -----------------------------------------------------------------------------
# Content Security Policy (CSP)
# -----------------------------------------------------------------------------
# django-csp >= 4.0 format
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'style-src': ("'self'", "'unsafe-inline'"),
        'script-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", "data:"),
        'font-src': ("'self'", "data:"),
        'frame-ancestors': ("'self'",),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
}

# -----------------------------------------------------------------------------
# Cache & Channels (Redis if available; otherwise fallback)
# -----------------------------------------------------------------------------

CACHES = get_cache_backend()

if REDIS_AVAILABLE:
    CHANNEL_LAYERS = get_channel_layers()

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
from utils.logging_config import setup_logging

LOGGING = setup_logging()

# -----------------------------------------------------------------------------
# PayHero (env only; the live payment provider used by apps/subscriptions)
# -----------------------------------------------------------------------------
# PAYHERO_CALLBACK_URL must point at /api/subscriptions/confirmation/.
# PAYHERO_CALLBACK_SECRET authenticates the callback: it is appended to the callback
# URL as ?secret=... when an STK push is started, and checked again when PayHero
# calls back. If PAYHERO_CALLBACK_SECRET is empty, every callback is rejected.
PAYHERO_CHANNEL_ID = os.environ.get("PAYHERO_CHANNEL_ID", "").strip()
PAYHERO_API_USERNAME = os.environ.get("PAYHERO_API_USERNAME", "").strip()
PAYHERO_API_PASSWORD = os.environ.get("PAYHERO_API_PASSWORD", "").strip()
PAYHERO_CALLBACK_URL = os.environ.get("PAYHERO_CALLBACK_URL", "").strip()
PAYHERO_CALLBACK_SECRET = os.environ.get("PAYHERO_CALLBACK_SECRET", "").strip()

CACHE_TTL = {
    'SUBJECTS': 60 * 60 * 24,      # 24 hours
    'INSTITUTIONS': 60 * 60 * 12,   # 12 hours
    'CLUSTERS': 60 * 60 * 24,       # 24 hours
    'PROGRAMMES': 60 * 60 * 2,      # 2 hours
    'SEARCH_RESULTS': 60 * 5,       # 5 minutes
}