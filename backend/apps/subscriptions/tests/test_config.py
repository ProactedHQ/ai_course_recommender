"""
Environment-separation and secret-hygiene checks for payments.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from apps.subscriptions.config import subscription_prices_for, validate_payment_settings

BACKEND_DIR = Path(settings.BASE_DIR)


class PaymentEnvironmentRulesTests(SimpleTestCase):

    def test_allowed_combinations(self):
        validate_payment_settings('production', 'payhero', False)
        validate_payment_settings('development', 'mock', False)
        validate_payment_settings('staging', 'mock', False)
        validate_payment_settings('staging', 'payhero', True)
        validate_payment_settings('test', 'mock', False)

    def test_rejected_combinations(self):
        for args in [
            ('production', 'mock', False),        # free upgrades in production
            ('production', 'stripe', False),      # unknown provider
            ('development', 'payhero', False),    # development is always mock
            ('development', 'payhero', True),     # ... even with the staging opt-in flag
            ('staging', 'payhero', False),
            ('test', 'payhero', True),
            ('prod', 'payhero', False),           # typo in APP_ENV
        ]:
            with self.assertRaises(ImproperlyConfigured, msg=str(args)):
                validate_payment_settings(*args)

    def test_prices_per_environment(self):
        self.assertEqual(subscription_prices_for('production'), {'mentor_elite': 199, 'scholar_vvip': 499})
        for env in ('development', 'test', 'staging'):
            self.assertEqual(subscription_prices_for(env)['mentor_elite'], 1)

    def test_this_test_run_is_isolated(self):
        self.assertEqual(settings.APP_ENV, 'test')
        self.assertEqual(settings.PAYMENT_PROVIDER, 'mock')
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')

    def _boot(self, **env):
        """Import settings in a clean subprocess with only placeholder values."""
        base = {
            'PATH': os.environ.get('PATH', ''),
            'APP_ENV': 'production',
            'SECRET_KEY': 'placeholder',
            'DATABASE_URL': 'postgres://user:pass@127.0.0.1:59999/placeholder',
            'SUPABASE_JWT_SECRET': 'placeholder',
            'REDIS_URL': '',
            'REDIS_HOST': '127.0.0.255',
            'DJANGO_SETTINGS_MODULE': 'course_recomeder_backend.settings',
        }
        base.update(env)
        return subprocess.run(
            [sys.executable, '-c', 'import django; django.setup(); from django.conf import settings; '
                                   'print(settings.PAYMENT_PROVIDER, settings.SUBSCRIPTION_PRICES_KES["mentor_elite"])'],
            cwd=BACKEND_DIR, env=base, capture_output=True, text=True, timeout=120,
        )

    def test_production_refuses_mock_provider_at_startup(self):
        result = self._boot(PAYMENT_PROVIDER='mock')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires PAYMENT_PROVIDER=payhero', result.stderr)

    def test_production_defaults_to_payhero_at_199(self):
        result = self._boot()
        self.assertEqual(result.returncode, 0, result.stderr[-500:])
        self.assertEqual(result.stdout.strip().splitlines()[-1], 'payhero 199')


class NoHardcodedCredentialsTests(SimpleTestCase):
    """Production configuration must come from the environment, never from source."""

    SECRET_NAMES = ('PAYHERO_CHANNEL_ID', 'PAYHERO_API_USERNAME', 'PAYHERO_API_PASSWORD',
                    'PAYHERO_CALLBACK_URL', 'PAYHERO_CALLBACK_SECRET')

    def test_settings_read_payhero_values_from_env_with_empty_default(self):
        source = (BACKEND_DIR / 'course_recomeder_backend' / 'settings.py').read_text()
        for name in self.SECRET_NAMES:
            assignments = re.findall(rf'^{name}\s*=\s*(.+)$', source, re.M)
            self.assertEqual(len(assignments), 1, name)
            self.assertEqual(assignments[0].strip(), f'os.environ.get("{name}", "").strip()', name)

    def test_no_payhero_literals_in_payment_code(self):
        for path in (BACKEND_DIR / 'apps' / 'subscriptions').glob('*.py'):
            source = path.read_text()
            for name in self.SECRET_NAMES:
                self.assertIsNone(re.search(rf'{name}\s*=\s*["\'][^"\']+["\']', source), f'{path.name}: {name}')
            self.assertIsNone(re.search(r'Basic\s+[A-Za-z0-9+/=]{12,}', source), path.name)

    def test_env_example_has_names_only(self):
        example = (BACKEND_DIR / '.env.example').read_text()
        for name in self.SECRET_NAMES:
            self.assertRegex(example, rf'(?m)^{name}=$')

    def test_no_legacy_daraja_configuration(self):
        for path in list((BACKEND_DIR / 'apps').rglob('*.py')) + [BACKEND_DIR / 'course_recomeder_backend' / 'settings.py']:
            if 'migrations' in path.parts or 'tests' in path.parts:
                continue
            self.assertIsNone(re.search(r'MPESA_|DARAJA|REQUIRE_MPESA', path.read_text()), str(path))
