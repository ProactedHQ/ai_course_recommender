"""
Guards that keep development and test environments away from production infrastructure.
Imported by settings.py, so this module must not import Django models.

Rules (applied in settings.py):
  - APP_ENV must be set explicitly by every entry point. Only the production web server entry
    points (passenger_wsgi.py / wsgi.py / asgi.py) default it to "production". So a local
    `manage.py`, script or shell with an old .env refuses to start instead of silently
    running against production.
  - development: DATABASE_URL must be SQLite or a database on this machine.
  - development/test: Redis must be local, otherwise it is ignored (no cache sharing).
  - development/test/staging: the production database is refused.
  - development/test: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must not belong to the production
    Supabase project (local login uses the separate development project).
"""
import base64
import json
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

# Public identifier of the PROACTED/KeDira production Supabase project (it is also in the
# public frontend bundle). Used only to refuse it outside production; not a credential.
PRODUCTION_SUPABASE_PROJECT_REF = "zuoujlipkmoqxrwcrdij"

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "host.docker.internal", "db", "postgres", "redis"}


def _host(url):
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def is_local_url(url):
    """True for sqlite URLs and URLs whose host is this machine / a local container name."""
    if not url:
        return True
    if url.startswith("sqlite"):
        return True
    return _host(url) in LOCAL_HOSTS


def points_at_production_supabase(value):
    return PRODUCTION_SUPABASE_PROJECT_REF in (value or "")


def require_app_env(raw_value):
    """Return the APP_ENV value, or explain how to set it."""
    value = (raw_value or "").strip().lower()
    if not value:
        raise ImproperlyConfigured(
            "APP_ENV is not set. Local work: put APP_ENV=development in backend/.env "
            "(copy backend/.env.example). Tests: APP_ENV=test. The production web server sets "
            "it automatically; production management commands need APP_ENV=production."
        )
    return value


def check_database_url(app_env, database_url):
    """Refuse databases that development/staging must never use."""
    if app_env == "development" and not is_local_url(database_url):
        raise ImproperlyConfigured(
            "APP_ENV=development only allows SQLite or a database on this machine "
            "(localhost/127.0.0.1). Remove the remote DATABASE_URL from backend/.env."
        )
    if app_env in ("development", "test", "staging") and points_at_production_supabase(database_url):
        raise ImproperlyConfigured(f"APP_ENV={app_env} must not use the production database.")


def safe_redis_url(app_env, redis_url):
    """The Redis URL this environment may use; remote Redis is dropped outside staging/production."""
    if app_env in ("development", "test") and not is_local_url(redis_url):
        return ""
    return redis_url


def supabase_key_project_ref(key):
    """Project ref inside a legacy JWT-style Supabase key (anon/service_role), else ''."""
    parts = (key or "").split(".")
    if len(parts) != 3:
        return ""  # new-style sb_publishable_/sb_secret_ keys carry no ref
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        return str(json.loads(base64.urlsafe_b64decode(payload)).get("ref", ""))
    except (ValueError, TypeError):
        return ""


def check_supabase_settings(app_env, supabase_url, service_role_key):
    """development/test must authenticate against a non-production Supabase project."""
    if app_env not in ("development", "test"):
        return
    if points_at_production_supabase(supabase_url):
        raise ImproperlyConfigured(
            f"APP_ENV={app_env} must not use the production Supabase project. Set SUPABASE_URL to the "
            "development project (see docs/PAYMENTS.md, 'Development login')."
        )
    if supabase_key_project_ref(service_role_key) == PRODUCTION_SUPABASE_PROJECT_REF:
        raise ImproperlyConfigured(f"APP_ENV={app_env} must not hold the production Supabase service-role key.")
