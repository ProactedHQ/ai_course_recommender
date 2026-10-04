"""
Development/test must never reach production infrastructure. These tests boot settings in clean
subprocesses with fake, production-looking values (no real credentials anywhere).
"""
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from utils.env_safety import (
    PRODUCTION_SUPABASE_PROJECT_REF, check_database_url, is_local_url, require_app_env, safe_redis_url,
)

BACKEND_DIR = Path(settings.BASE_DIR)
FAKE_PROD_DB = f"postgresql://postgres.{PRODUCTION_SUPABASE_PROJECT_REF}:fake@aws-0-eu.pooler.supabase.com:6543/postgres"
FAKE_REMOTE_REDIS = "rediss://default:fake@example-redis.upstash.io:6379"

PROBE = (
    "import django; django.setup(); from django.conf import settings as s; "
    "print('OK', s.APP_ENV, s.DATABASES['default']['ENGINE'].split('.')[-1], s.PAYMENT_PROVIDER, "
    "bool(s.PAYHERO_API_PASSWORD or s.PAYHERO_CALLBACK_SECRET), s.REDIS_AVAILABLE)"
)


def boot(**env):
    """Import settings in a subprocess; cwd is outside backend/ so no .env file is picked up."""
    base = {'PATH': os.environ.get('PATH', ''), 'PYTHONPATH': str(BACKEND_DIR),
            'DJANGO_SETTINGS_MODULE': 'course_recomeder_backend.settings', 'REDIS_HOST': '127.0.0.255'}
    base.update(env)
    return subprocess.run([sys.executable, '-c', PROBE], cwd='/', env=base,
                          capture_output=True, text=True, timeout=120)


class EnvSafetyRulesTests(SimpleTestCase):

    def test_app_env_is_mandatory(self):
        with self.assertRaises(ImproperlyConfigured):
            require_app_env(None)
        self.assertEqual(require_app_env(' Development '), 'development')

    def test_local_urls(self):
        for url in ('', 'sqlite:///db.sqlite3', 'postgres://u:p@localhost:5432/x', 'redis://127.0.0.1:6379/0'):
            self.assertTrue(is_local_url(url), url)
        for url in (FAKE_PROD_DB, FAKE_REMOTE_REDIS, 'postgres://u:p@10.0.0.5/x'):
            self.assertFalse(is_local_url(url), url)

    def test_database_rules(self):
        check_database_url('development', 'postgres://u:p@localhost/x')
        check_database_url('staging', 'postgres://u:p@staging-db.example/x')
        check_database_url('production', FAKE_PROD_DB)
        for env, url in [('development', FAKE_PROD_DB), ('development', 'postgres://u:p@10.0.0.5/x'),
                         ('staging', FAKE_PROD_DB), ('test', FAKE_PROD_DB)]:
            with self.assertRaises(ImproperlyConfigured, msg=(env, url)):
                check_database_url(env, url)

    def test_remote_redis_dropped_outside_deployed_envs(self):
        self.assertEqual(safe_redis_url('development', FAKE_REMOTE_REDIS), '')
        self.assertEqual(safe_redis_url('test', FAKE_REMOTE_REDIS), '')
        self.assertEqual(safe_redis_url('production', FAKE_REMOTE_REDIS), FAKE_REMOTE_REDIS)


class EnvSafetyBootTests(SimpleTestCase):
    """Whole-settings behaviour with a production-looking environment (all values fake)."""

    PROD_LOOKING = dict(DATABASE_URL=FAKE_PROD_DB, REDIS_URL=FAKE_REMOTE_REDIS, SECRET_KEY='fake',
                        SUPABASE_JWT_SECRET='fake', PAYHERO_CHANNEL_ID='1', PAYHERO_API_USERNAME='fake',
                        PAYHERO_API_PASSWORD='fake', PAYHERO_CALLBACK_SECRET='fake')

    def test_missing_app_env_refuses_to_start(self):
        result = boot(**self.PROD_LOOKING)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('APP_ENV is not set', result.stderr)

    def test_development_refuses_production_database(self):
        result = boot(APP_ENV='development', **self.PROD_LOOKING)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('only allows SQLite or a database on this machine', result.stderr)

    def test_development_with_prod_values_but_local_db_is_isolated(self):
        env = {**self.PROD_LOOKING, 'APP_ENV': 'development', 'DATABASE_URL': ''}
        result = boot(**env)
        self.assertEqual(result.returncode, 0, result.stderr[-400:])
        # sqlite, mock payments, PayHero credentials discarded, remote Redis ignored
        _, app_env, engine, provider, has_creds, redis = result.stdout.split()[-6:]
        self.assertEqual((app_env, engine, provider, has_creds, redis),
                         ('development', 'sqlite3', 'mock', 'False', 'False'))
        self.assertIn('Ignoring non-local REDIS_URL', result.stderr)

    def test_development_cannot_select_payhero(self):
        result = boot(APP_ENV='development', DATABASE_URL='', PAYMENT_PROVIDER='payhero',
                      PAYHERO_ALLOW_NON_PRODUCTION='true')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('always uses PAYMENT_PROVIDER=mock', result.stderr)

    def test_staging_refuses_production_database(self):
        result = boot(APP_ENV='staging', **self.PROD_LOOKING)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must not use the production database', result.stderr)

    def test_web_server_entry_points_default_to_production(self):
        for module in ('passenger_wsgi.py', 'course_recomeder_backend/wsgi.py', 'course_recomeder_backend/asgi.py'):
            self.assertIn('os.environ.setdefault("APP_ENV", "production")', (BACKEND_DIR / module).read_text(), module)


def fake_legacy_key(ref, role):
    """A JWT-shaped string carrying only a project ref and role - not a real key (unsigned)."""
    import base64, json
    seg = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')
    return f"{seg({'alg': 'HS256'})}.{seg({'ref': ref, 'role': role})}.fake-signature"


class SupabaseIsolationTests(SimpleTestCase):

    def test_key_ref_detection(self):
        from utils.env_safety import supabase_key_project_ref
        self.assertEqual(supabase_key_project_ref(fake_legacy_key('devref123', 'service_role')), 'devref123')
        self.assertEqual(supabase_key_project_ref('sb_secret_fakefakefake'), '')
        self.assertEqual(supabase_key_project_ref(''), '')

    def test_development_refuses_production_supabase(self):
        from utils.env_safety import check_supabase_settings
        prod_url = f"https://{PRODUCTION_SUPABASE_PROJECT_REF}.supabase.co"
        for env in ('development', 'test'):
            with self.assertRaises(ImproperlyConfigured):
                check_supabase_settings(env, prod_url, '')
            with self.assertRaises(ImproperlyConfigured):
                check_supabase_settings(env, 'https://devproject.supabase.co',
                                        fake_legacy_key(PRODUCTION_SUPABASE_PROJECT_REF, 'service_role'))
            check_supabase_settings(env, 'https://devproject.supabase.co',
                                    fake_legacy_key('devproject', 'service_role'))
        check_supabase_settings('production', prod_url, fake_legacy_key(PRODUCTION_SUPABASE_PROJECT_REF, 'service_role'))

    def test_boot_refuses_production_supabase_in_development(self):
        result = boot(APP_ENV='development', DATABASE_URL='',
                      SUPABASE_URL=f"https://{PRODUCTION_SUPABASE_PROJECT_REF}.supabase.co")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must not use the production Supabase project', result.stderr)

    def test_boot_accepts_development_supabase(self):
        result = boot(APP_ENV='development', DATABASE_URL='', SUPABASE_URL='https://devproject.supabase.co')
        self.assertEqual(result.returncode, 0, result.stderr[-400:])


class SupabaseAuthFallbackTests(SimpleTestCase):
    """The production-project fallback in apps/users/auth/supabase.py is production-only."""

    def test_no_fallback_outside_production(self):
        from unittest.mock import patch
        from rest_framework.exceptions import AuthenticationFailed
        from apps.users.auth import supabase as sb
        with patch.dict(os.environ, {'SUPABASE_URL': ''}):
            with self.assertRaises(AuthenticationFailed):
                sb._get_supabase_url()          # APP_ENV=test
            with self.settings(APP_ENV='production'):
                self.assertEqual(sb._get_supabase_url(), sb.PRODUCTION_SUPABASE_URL)
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://devproject.supabase.co/'}):
            self.assertEqual(sb._get_supabase_url(), 'https://devproject.supabase.co')
