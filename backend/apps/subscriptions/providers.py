"""
Payment providers. Business logic (services.py) only talks to these through:

    provider.is_configured() -> bool
    provider.initiate(phone, amount, external_reference, customer_name) -> InitiateResult
    provider.get_status(provider_reference) -> StatusResult

PayHeroProvider  the only real provider (production, or staging with explicit opt-in)
MockProvider     development/test: no network, no credentials. Payments are completed
                 by hand through the dev-only mock endpoint / `manage.py mock_payment`.

PayHero endpoints used (base https://backend.payhero.co.ke/api/v2/, HTTP Basic auth), as in
PayHero's official SDK (github.com/PAY-HERO-KENYA/payhero-php-package):
    POST payments                              start an M-Pesa prompt via the PayHero channel
    GET  transaction-status?reference=<ref>    look up a payment by PayHero's reference

Never log credentials, the Authorization header, or full provider responses.
"""
import base64
import logging
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PAYHERO_API_BASE = 'https://backend.payhero.co.ke/api/v2/'


@dataclass
class InitiateResult:
    ok: bool
    provider_reference: str = ''
    error: str = ''  # internal reason; never shown to the customer verbatim


@dataclass
class StatusResult:
    # SUCCESS | FAILED | PENDING | UNKNOWN. UNKNOWN = could not tell; never activates a plan.
    state: str


class MockProvider:
    """Local development/test provider. Accepts every request; nothing leaves the machine."""
    name = 'mock'

    def is_configured(self):
        return True

    def initiate(self, phone, amount, external_reference, customer_name):
        logger.info("[mock] Payment %s started for KES %s (no real charge)", external_reference, amount)
        return InitiateResult(ok=True, provider_reference=f"MOCK-{uuid.uuid4().hex[:12].upper()}")

    def get_status(self, provider_reference):
        return StatusResult(state='UNKNOWN')


class PayHeroProvider:
    name = 'payhero'

    def is_configured(self):
        return all([
            settings.PAYHERO_CHANNEL_ID,
            settings.PAYHERO_API_USERNAME,
            settings.PAYHERO_API_PASSWORD,
            settings.PAYHERO_CALLBACK_URL,
            settings.PAYHERO_CALLBACK_SECRET,  # without it every callback is rejected
        ])

    def callback_url(self):
        """PAYHERO_CALLBACK_URL with ?secret=<PAYHERO_CALLBACK_SECRET>; views.confirmation checks it."""
        parts = urlparse(settings.PAYHERO_CALLBACK_URL)
        query = dict(parse_qsl(parts.query))
        query['secret'] = settings.PAYHERO_CALLBACK_SECRET
        return urlunparse(parts._replace(query=urlencode(query)))

    def _headers(self):
        token = f"{settings.PAYHERO_API_USERNAME}:{settings.PAYHERO_API_PASSWORD}"
        return {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(token.encode()).decode(),
        }

    def initiate(self, phone, amount, external_reference, customer_name):
        if not self.is_configured():
            return InitiateResult(ok=False, error='PayHero is not configured')
        try:
            channel_id = int(settings.PAYHERO_CHANNEL_ID)
        except ValueError:
            return InitiateResult(ok=False, error='PAYHERO_CHANNEL_ID is not a number')

        payload = {
            "amount": int(amount),
            "phone_number": phone,
            "channel_id": channel_id,
            "provider": "m-pesa",  # PayHero's value for its M-Pesa collection method
            "external_reference": external_reference,
            "customer_name": customer_name,
            "callback_url": self.callback_url(),
        }
        try:
            response = requests.post(PAYHERO_API_BASE + 'payments', json=payload, headers=self._headers(),
                                     timeout=settings.PAYHERO_TIMEOUT_SECONDS)
        except requests.Timeout:
            logger.error("[payhero] Initiate timed out for %s", external_reference)
            return InitiateResult(ok=False, error='PayHero timed out')
        except requests.RequestException as e:
            logger.error("[payhero] Initiate request error for %s: %s", external_reference, type(e).__name__)
            return InitiateResult(ok=False, error='PayHero unreachable')

        if response.status_code >= 400:
            logger.error("[payhero] Initiate HTTP %s for %s", response.status_code, external_reference)
            return InitiateResult(ok=False, error=f'PayHero HTTP {response.status_code}')
        try:
            data = response.json()
        except ValueError:
            return InitiateResult(ok=False, error='PayHero returned invalid JSON')

        if data.get('success') is True and str(data.get('status', '')).upper() == 'QUEUED':
            return InitiateResult(ok=True, provider_reference=str(data.get('reference') or ''))
        logger.warning("[payhero] Initiate not queued for %s (status=%s)", external_reference, data.get('status'))
        return InitiateResult(ok=False, error='PayHero did not queue the payment')

    def get_status(self, provider_reference):
        """
        GET transaction-status?reference=... . PayHero does not publish the response fields,
        so only an explicit top-level "status" of SUCCESS / FAILED / QUEUED is trusted;
        anything else is UNKNOWN and never activates a plan.
        """
        if not self.is_configured() or not provider_reference:
            return StatusResult(state='UNKNOWN')
        try:
            response = requests.get(PAYHERO_API_BASE + 'transaction-status',
                                    params={'reference': provider_reference},
                                    headers=self._headers(), timeout=settings.PAYHERO_TIMEOUT_SECONDS)
            if response.status_code >= 400:
                logger.warning("[payhero] Status HTTP %s for %s", response.status_code, provider_reference)
                return StatusResult(state='UNKNOWN')
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("[payhero] Status lookup failed for %s: %s", provider_reference, type(e).__name__)
            return StatusResult(state='UNKNOWN')

        status = str(data.get('status', '')).upper() if isinstance(data, dict) else ''
        state = {'SUCCESS': 'SUCCESS', 'FAILED': 'FAILED', 'QUEUED': 'PENDING'}.get(status, 'UNKNOWN')
        logger.info("[payhero] Status for %s: %s", provider_reference, state)
        return StatusResult(state=state)


def get_provider():
    """The provider selected by settings.PAYMENT_PROVIDER (validated at startup)."""
    return PayHeroProvider() if settings.PAYMENT_PROVIDER == 'payhero' else MockProvider()
