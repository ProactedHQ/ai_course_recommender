"""
PayHero client helpers.

PayHero (https://backend.payhero.co.ke) is the payment provider behind the
subscription upgrade flow. It sends an M-Pesa STK push to the student's phone and
later POSTs the outcome to PAYHERO_CALLBACK_URL (handled by views.confirmation).
"""
import base64
import logging
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PAYHERO_PAYMENTS_URL = 'https://backend.payhero.co.ke/api/v2/payments'


def build_callback_url():
    """
    Return PAYHERO_CALLBACK_URL with ?secret=<MPESA_CALLBACK_SECRET> appended.

    PayHero calls this exact URL back, so the secret proves the callback came from
    a push we started. views.confirmation rejects callbacks without it.
    """
    callback_url = settings.PAYHERO_CALLBACK_URL
    secret = settings.MPESA_CALLBACK_SECRET
    if not secret:
        return callback_url

    parts = urlparse(callback_url)
    query = dict(parse_qsl(parts.query))
    query['secret'] = secret
    return urlunparse(parts._replace(query=urlencode(query)))


def initiate_payhero_stk_push(phone_number, amount, external_reference, customer_name, provider="m-pesa", network_code=None):
    """
    Ask PayHero to send an STK push to `phone_number` for `amount` KES.

    `external_reference` is our Transaction.ref_id; PayHero echoes it back in the
    callback as ExternalReference so we can find the transaction.

    Returns PayHero's JSON on success (expect {"success": True, "status": "QUEUED", ...}),
    or {"success": False, "error": "..."} on any network/HTTP/parse failure. Never raises.
    """
    # Normalize phone to international format (07XXXXXXXX -> +2547XXXXXXXX)
    if phone_number.startswith('0'):
        phone_number = '+254' + phone_number[1:]

    if not settings.PAYHERO_CHANNEL_ID or not settings.PAYHERO_CALLBACK_URL:
        logger.error("PayHero is not configured: set PAYHERO_CHANNEL_ID, PAYHERO_API_USERNAME, "
                     "PAYHERO_API_PASSWORD and PAYHERO_CALLBACK_URL.")
        return {"success": False, "error": "Payments are temporarily unavailable."}

    payload = {
        "amount": int(amount),
        "phone_number": phone_number,
        "channel_id": int(settings.PAYHERO_CHANNEL_ID),
        "provider": provider,
        "external_reference": external_reference,
        "customer_name": customer_name,
        "callback_url": build_callback_url(),
    }

    if network_code:
        payload["network_code"] = network_code

    # PayHero uses HTTP Basic auth with the API username/password from the dashboard
    auth_str = f"{settings.PAYHERO_API_USERNAME}:{settings.PAYHERO_API_PASSWORD}"
    encoded_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_auth}"
    }

    response = None
    try:
        response = requests.post(PAYHERO_PAYMENTS_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"PayHero request failed: {str(e)} - Response: {response.text if response is not None else 'N/A'}")
        return {"success": False, "error": str(e)}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response from PayHero"}
