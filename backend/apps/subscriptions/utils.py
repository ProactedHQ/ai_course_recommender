import requests
import logging

logger = logging.getLogger(__name__)

def initiate_payhero_stk_push(phone_number, amount, external_reference, customer_name, provider="m-pesa", network_code=None):
    url = 'https://backend.payhero.co.ke/api/v2/payments'

    # Normalize phone to international format
    if phone_number.startswith('0'):
        phone_number = '+254' + phone_number[1:]

    # Get credentials from Django settings
    from django.conf import settings
    channel_id = settings.PAYHERO_CHANNEL_ID
    username = settings.PAYHERO_API_USERNAME
    password = settings.PAYHERO_API_PASSWORD
    callback_url = settings.PAYHERO_CALLBACK_URL

    payload = {
        "amount": int(amount),
        "phone_number": phone_number,
        "channel_id": int(channel_id),
        "provider": provider,
        "external_reference": external_reference,
        "customer_name": customer_name,
        "callback_url": callback_url
    }

    if network_code:
        payload["network_code"] = network_code

    import base64
    auth_str = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_auth}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"PayHero request failed: {str(e)} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return {"success": False, "error": str(e)}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response from PayHero"}