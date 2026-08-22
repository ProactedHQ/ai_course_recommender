#!/usr/bin/env python
import os
import sys
import json

import django
from django.contrib.auth import get_user_model

def main():
    # Setup Django environment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
    django.setup()

    # Get or create test user
    User = get_user_model()

    username = "wizard_tester"
    email = "[REDACTED_EMAIL]"
    password = "[REDACTED_CREDENTIAL]"

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_student": True,
        },
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"Created test user: {username}")
    else:
        print(f"Using existing test user: {username}")

    # Simulate authenticated request (no DRF needed for simple POST)
    from django.test import Client
    client = Client(HTTP_HOST='proactedai.co.ke')
    client.login(username=username, password=password)

    # Hardcoded payload — change phone/amount as needed
    payload = {
        "phone_number": "[REDACTED_PHONE]",  # ← Change to a real test number
        "amount": 5               # KES 50 for testing
    }

    print("\nSending POST to api/subscriptions/initiate/ ...")
    print("Payload:", json.dumps(payload, indent=2))

    response = client.post(
        '/api/subscriptions/initiate/',
        data=json.dumps(payload),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Optional: helps some CSRF setups
    )

    print("\nResponse status:", response.status_code)

    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, default=str))
    except Exception:
        print("Raw content (not JSON):")
        print(response.content.decode('utf-8') if response.content else "<empty>")

    if response.status_code == 200 and response.json().get('success'):
        print("\nSUCCESS: STK Push should be on the phone now.")
    elif response.status_code in [400, 401, 403]:
        print("\nClient error — check phone number, auth, or payload.")
    else:
        print("\nServer error — check logs / PayHero dashboard.")


if __name__ == "__main__":
    main()