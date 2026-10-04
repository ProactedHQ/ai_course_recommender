"""
CI guard: prove the backend is running in the isolated test configuration before any test runs.

Fails (exit 1) unless: APP_ENV=test, SQLite in memory, mock payments, no Redis, no PayHero
credentials, and no production Supabase project configured. Prints only booleans/names.
Run from backend/:  APP_ENV=test python ci/check_test_environment.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

PRODUCTION_SUPABASE_REF = "zuoujlipkmoqxrwcrdij"
db = settings.DATABASES["default"]
checks = {
    "APP_ENV is test": settings.APP_ENV == "test",
    "database is in-memory SQLite": db["ENGINE"].endswith("sqlite3") and str(db["NAME"]) == ":memory:",
    "payment provider is mock": settings.PAYMENT_PROVIDER == "mock",
    "Redis disabled": settings.REDIS_AVAILABLE is False,
    "no PayHero credentials": not any([settings.PAYHERO_CHANNEL_ID, settings.PAYHERO_API_USERNAME,
                                       settings.PAYHERO_API_PASSWORD, settings.PAYHERO_CALLBACK_SECRET]),
    "no production Supabase": PRODUCTION_SUPABASE_REF not in os.environ.get("SUPABASE_URL", ""),
}
for name, ok in checks.items():
    print(f"{'OK  ' if ok else 'FAIL'} {name}")
sys.exit(0 if all(checks.values()) else 1)
