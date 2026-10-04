"""
Django settings for course_recomeder_backend - one file for every environment.

APP_ENV selects the environment. It must be set explicitly, except by the production web
server entry points (passenger_wsgi.py / wsgi.py / asgi.py), which default it to production:
  development  local machine: SQLite unless DATABASE_URL is set, mock payments, DEBUG on
  test         test runner: in-memory SQLite, mock payments, no Redis, no secrets needed
  staging      deployed test server: its own DATABASE_URL and secrets, mock payments by default
  production   api.proactedai.co.ke on cPanel Passenger: all secrets required, PayHero only

Important:
- Do NOT hardcode secrets in this file. Every secret comes from the environment.
- Production values are set by the project owner on the hosting server, never in git.
- See docs/PAYMENTS.md and backend/.env.example.
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

# -----------------------------------------------------------------------------
# Environment helpers
# -----------------------------------------------------------------------------
# An empty variable (e.g. "NAME=" copied from .env.example) counts as unset and gets the default.
def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default

def env_int(name: str, default: int) -> int:
    return int(env_str(name, str(default)))

def env_bool(name: str, default: bool = False) -> bool:
    return env_str(name, str(default)).lower() in ("1", "true", "yes", "on")

def env_list(name: str, default: str = "") -> list[str]:
    raw = env_str(name, default)
    return [v.strip() for v in raw.split(",") if v.strip()]

def require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
from utils.env_safety import (
    check_database_url, check_supabase_settings, is_local_url, require_app_env, safe_redis_url,
)

# No default here: manage.py, scripts and shells must say which environment they are in, so an
# old .env full of production values cannot be used by accident.
APP_ENV = require_app_env(os.environ.get("APP_ENV"))
IS_PRODUCTION = APP_ENV == "production"
IS_DEPLOYED = APP_ENV in ("staging", "production")  # real servers: secrets required

RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"
if RUNNING_TESTS and APP_ENV != "test":
    raise RuntimeError(
        f"Refusing to run tests with APP_ENV={APP_ENV}: they could touch a real database. "
        "Run them with APP_ENV=test (see docs/PAYMENTS.md)."
    )

# development/test only ever talk to a Redis on this machine; a remote REDIS_URL is ignored.
_redis_url = os.environ.get("REDIS_URL", "")
if safe_redis_url(APP_ENV, _redis_url) != _redis_url:
    print(f"Ignoring non-local REDIS_URL in APP_ENV={APP_ENV}.", file=sys.stderr)
    os.environ["REDIS_URL"] = ""
if APP_ENV in ("development", "test") and not is_local_url("redis://" + os.environ.get("REDIS_HOST", "127.0.0.1")):
    os.environ["REDIS_HOST"] = "127.0.0.1"

from utils.redis_config import is_redis_available, get_cache_backend, get_channel_layers
REDIS_AVAILABLE = False if APP_ENV == "test" else is_redis_available()

# -----------------------------------------------------------------------------
# Core security / debug
# -----------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", APP_ENV == "development")

if IS_DEPLOYED:
    SECRET_KEY = require_env("SECRET_KEY")
else:
    SECRET_KEY = os.environ.get("SECRET_KEY", "").strip() or "django-insecure-local-development-only"

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "api.proactedai.co.ke" if IS_DEPLOYED else "localhost,127.0.0.1,testserver",
)

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
# Database (PostgreSQL in staging/production; SQLite allowed locally)
# -----------------------------------------------------------------------------
if APP_ENV == "test":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
else:
    DATABASE_URL = require_env("DATABASE_URL") if IS_DEPLOYED else os.environ.get("DATABASE_URL", "").strip()
    check_database_url(APP_ENV, DATABASE_URL)  # development: local only; never production outside it
    if DATABASE_URL:
        DATABASES = {
            "default": dj_database_url.parse(
                DATABASE_URL.split(' ')[0] if ' ' in DATABASE_URL else DATABASE_URL,
                conn_max_age=env_int("DB_CONN_MAX_AGE", 600),
            )
        }
        if "postgresql" in DATABASES["default"]["ENGINE"]:
            # Hosted Postgres (Supabase) requires SSL; a local Postgres usually doesn't have it.
            DATABASES["default"].setdefault("OPTIONS", {})
            DATABASES["default"]["OPTIONS"]["sslmode"] = env_str(
                "DB_SSLMODE", "require" if IS_DEPLOYED else "prefer"
            )
    else:
        # development without DATABASE_URL: a local file, never a shared database
        DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

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
SUPABASE_JWT_SECRET = require_env("SUPABASE_JWT_SECRET") if IS_DEPLOYED else os.environ.get("SUPABASE_JWT_SECRET", "").strip()
# development/test: refuse production auth/admin credentials (local login uses the dev project)
check_supabase_settings(APP_ENV, os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))

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

# Local frontend (Vite) - on by default only in development
if env_bool("ALLOW_LOCALHOST_CORS", APP_ENV == "development"):
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

if IS_DEPLOYED and not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
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

CACHES = (
    {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    if APP_ENV == "test" else get_cache_backend()
)

if REDIS_AVAILABLE:
    CHANNEL_LAYERS = get_channel_layers()

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
from utils.logging_config import setup_logging

LOGGING = setup_logging()

# -----------------------------------------------------------------------------
# Payments (apps/subscriptions) - PayHero is the only real provider
# -----------------------------------------------------------------------------
# Flow: frontend -> Django initiate -> PayHero -> M-Pesa prompt -> PayHero callback
#       -> Django verifies -> PostgreSQL. The frontend never sees any of these values.
from apps.subscriptions.config import (
    default_payment_provider, subscription_prices_for, validate_payment_settings,
)

PAYMENT_PROVIDER = env_str("PAYMENT_PROVIDER", default_payment_provider(APP_ENV)).lower()
if APP_ENV == "test":
    PAYMENT_PROVIDER = "mock"
PAYHERO_ALLOW_NON_PRODUCTION = env_bool("PAYHERO_ALLOW_NON_PRODUCTION", False)
validate_payment_settings(APP_ENV, PAYMENT_PROVIDER, PAYHERO_ALLOW_NON_PRODUCTION)

# Secrets - owner-controlled, supplied by the hosting environment. Empty = payments unavailable.
PAYHERO_CHANNEL_ID = os.environ.get("PAYHERO_CHANNEL_ID", "").strip()
PAYHERO_API_USERNAME = os.environ.get("PAYHERO_API_USERNAME", "").strip()
PAYHERO_API_PASSWORD = os.environ.get("PAYHERO_API_PASSWORD", "").strip()
# Must point at https://<api-domain>/api/subscriptions/confirmation/
PAYHERO_CALLBACK_URL = os.environ.get("PAYHERO_CALLBACK_URL", "").strip()
# Appended to the callback URL as ?secret=... and checked on every callback.
PAYHERO_CALLBACK_SECRET = os.environ.get("PAYHERO_CALLBACK_SECRET", "").strip()

if not IS_DEPLOYED:
    # development/test never hold PayHero credentials, whatever a local .env contains.
    for _name in ("PAYHERO_CHANNEL_ID", "PAYHERO_API_USERNAME", "PAYHERO_API_PASSWORD", "PAYHERO_CALLBACK_SECRET"):
        globals()[_name] = ""

# After a valid callback, also confirm with PayHero's GET transaction-status before activating
# a plan. Off until the owner has confirmed the response format with one staging payment.
PAYHERO_VERIFY_WITH_STATUS_API = env_bool("PAYHERO_VERIFY_WITH_STATUS_API", False)

# Seconds before giving up on PayHero HTTP calls (connect, read)
PAYHERO_TIMEOUT_SECONDS = (5, env_int("PAYHERO_READ_TIMEOUT", 30))

SUBSCRIPTION_PRICES_KES = subscription_prices_for(APP_ENV)
PAYMENT_PENDING_TIMEOUT_MINUTES = env_int("PAYMENT_PENDING_TIMEOUT_MINUTES", 15)
PAYMENT_MAX_ATTEMPTS_PER_WINDOW = 3          # initiate/ calls per user ...
PAYMENT_ATTEMPT_WINDOW_MINUTES = 5           # ... within this many minutes

CACHE_TTL = {
    'SUBJECTS': 60 * 60 * 24,      # 24 hours
    'INSTITUTIONS': 60 * 60 * 12,   # 12 hours
    'CLUSTERS': 60 * 60 * 24,       # 24 hours
    'PROGRAMMES': 60 * 60 * 2,      # 2 hours
    'SEARCH_RESULTS': 60 * 5,       # 5 minutes
}