"""
Environment rules for payments. Imported by settings.py, so it must not import Django models.

APP_ENV          development | test | staging | production
PAYMENT_PROVIDER mock | payhero

Rules (enforced at startup by validate_payment_settings):
  - production must use payhero (a mock provider in production would hand out free upgrades)
  - test always uses mock
  - development always uses mock (it also never sees PayHero credentials - see settings.py)
  - staging may use payhero only with PAYHERO_ALLOW_NON_PRODUCTION=true and its own credentials
"""
from django.core.exceptions import ImproperlyConfigured

APP_ENVS = ("development", "test", "staging", "production")
PAYMENT_PROVIDERS = ("mock", "payhero")

# KES per paid tier. The amount charged is always taken from here, never from the client.
PRODUCTION_PRICES_KES = {"mentor_elite": 199, "scholar_vvip": 499}
NON_PRODUCTION_PRICES_KES = {"mentor_elite": 1, "scholar_vvip": 499}


def default_payment_provider(app_env: str) -> str:
    return "payhero" if app_env == "production" else "mock"


def subscription_prices_for(app_env: str) -> dict:
    prices = PRODUCTION_PRICES_KES if app_env == "production" else NON_PRODUCTION_PRICES_KES
    return dict(prices)


def validate_payment_settings(app_env: str, provider: str, allow_payhero_outside_production: bool) -> None:
    """Raise ImproperlyConfigured for any unsafe environment/provider combination."""
    if app_env not in APP_ENVS:
        raise ImproperlyConfigured(f"APP_ENV must be one of {APP_ENVS}, got {app_env!r}.")
    if provider not in PAYMENT_PROVIDERS:
        raise ImproperlyConfigured(f"PAYMENT_PROVIDER must be one of {PAYMENT_PROVIDERS}, got {provider!r}.")
    if app_env == "production" and provider != "payhero":
        raise ImproperlyConfigured("APP_ENV=production requires PAYMENT_PROVIDER=payhero.")
    if app_env == "test" and provider != "mock":
        raise ImproperlyConfigured("APP_ENV=test always uses PAYMENT_PROVIDER=mock.")
    if app_env == "development" and provider != "mock":
        raise ImproperlyConfigured("APP_ENV=development always uses PAYMENT_PROVIDER=mock.")
    if app_env == "staging" and provider == "payhero" and not allow_payhero_outside_production:
        raise ImproperlyConfigured(
            "PAYMENT_PROVIDER=payhero in APP_ENV=staging needs PAYHERO_ALLOW_NON_PRODUCTION=true "
            "and non-production PayHero credentials."
        )
