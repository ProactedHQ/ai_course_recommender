"""
=======================================================================
 KeDira — M-Pesa Payment Test Suite
=======================================================================
 Covers:
   ✔ POST /api/subscription/upgrade/ → Initiates STK Push
   ✔ POST /api/subscription/callback/ → M-Pesa Result Handler (fixed BUG 2)
   ✔ Payment verification → Reference lookup (CheckoutRequestID)
   ✔ Tier update after success

 Run these tests with:
   python manage.py test apps.users.tests.test_payments -v 2
=======================================================================
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.users.models import SubscriptionTransaction
from unittest.mock import patch

User = get_user_model()

# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'─' * 60}")
    print(f"  💸  PAYMENT │ {title}")
    print(f"{'─' * 60}")

def ok(msg):  print(f"    ✅  {msg}")
def fail(msg): print(f"    ❌  {msg}")
def info(msg): print(f"    ℹ️   {msg}")


class PaymentFlowTests(TestCase):
    """Tests for the M-Pesa payment integration."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='pay_test_user',
            email='pay@kedira.ac.ke',
            password='testpass123',
            is_student=True
        )
        self.client.force_authenticate(user=self.user)

    # ── 1. Upgrade Initiation ──────────────────────────────────────────
    @patch('apps.users.utils.mpesa.MpesaClient.stk_push')
    def test_upgrade_initiation_success(self, mock_stk_push):
        section("Upgrade Initiation → Pending transaction created")
        
        # Mocking successful STK push initiation
        mock_stk_push.return_value = {"CheckoutRequestID": "ws_CO_001", "ResponseCode": "0"}
        
        data = {
            "target_tier": "mentor_elite",
            "phone_number": "254712345678"
        }
        
        response = self.client.post('/api/subscription/upgrade/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify transaction record
        txn = SubscriptionTransaction.objects.get(user=self.user)
        self.assertEqual(txn.status, 'pending')
        self.assertEqual(txn.reference, 'ws_CO_001')
        self.assertEqual(float(txn.amount), 199.00)
        
        ok("STK Push call succeeded")
        ok(f"Pending transaction created with Ref: {txn.reference}")

    # ── 2. Handle Callback (BUG 2 Fix Validation) ───────────────────────
    def test_callback_updates_user_tier(self):
        section("M-Pesa Callback (Success) → Updates Tier & Status")
        
        # Create a pending transaction
        checkout_id = "ws_CO_CALLBACK_001"
        txn = SubscriptionTransaction.objects.create(
            user=self.user,
            target_tier='scholar_vvip',
            amount=499.00,
            reference=checkout_id,
            status='pending'
        )
        
        # Simulating Safaricom Callback Body
        callback_data = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34621005-1",
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 499.00},
                            {"Name": "MpesaReceiptNumber", "Value": "RHKXXXXXXX"},
                            {"Name": "TransactionDate", "Value": 20230101000000},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }
        
        # Call the endpoint (providing secret token in URL)
        from django.conf import settings
        token = getattr(settings, 'MPESA_CALLBACK_SECRET', 'test_secret')
        url = f'/api/subscription/callback/?token={token}'
        
        response = self.client.post(url, callback_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # 1. Verification: Transaction table updated
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'completed')
        ok("Transaction status updated to 'completed'")
        
        # 2. Verification: User tier updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'scholar_vvip')
        ok(f"User tier correctly updated to '{self.user.subscription_tier}'")

    # ── 3. Handle Callback (Failure) ──────────────────────────────────
    def test_callback_handles_failure(self):
        section("M-Pesa Callback (Failure) → Marks transaction as failed")
        
        checkout_id = "ws_CO_FAIL_001"
        txn = SubscriptionTransaction.objects.create(
            user=self.user,
            target_tier='mentor_elite',
            amount=199.00,
            reference=checkout_id,
            status='pending'
        )
        
        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 1,
                    "ResultDesc": "Request cancelled by user"
                }
            }
        }
        
        from django.conf import settings
        token = getattr(settings, 'MPESA_CALLBACK_SECRET', 'test_secret')
        url = f'/api/subscription/callback/?token={token}'
        
        response = self.client.post(url, callback_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'failed')
        
        # Tier should NOT be changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'explorer')
        
        ok("Failed payment correctly handled (status='failed')")
        ok("Tier unchanged as expected")
