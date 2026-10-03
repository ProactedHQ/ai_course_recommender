"""
=======================================================================
 KeDira — PayHero Payment Test Suite
=======================================================================
 Covers:
   ✔ POST /api/subscriptions/initiate/     → Creates PENDING txn + STK push
   ✔ POST /api/subscriptions/confirmation/ → PayHero callback (secret-checked)
   ✔ Replayed / underpaid / forged callbacks do not upgrade anyone
   ✔ GET  /api/subscriptions/status/       → Polling result

 Run these tests with:
   python manage.py test apps.users.tests.test_payments -v 2
=======================================================================
"""

import base64
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import Transaction, Coupon, CouponUsed
from apps.subscriptions.utils import build_callback_url, initiate_payhero_stk_push

User = get_user_model()

SECRET = 'test-callback-secret'
CALLBACK = '/api/subscriptions/confirmation/'


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'─' * 60}")
    print(f"  💸  PAYMENT │ {title}")
    print(f"{'─' * 60}")

def ok(msg):  print(f"    ✅  {msg}")


def payhero_callback(ref, status_str='Success', amount=1, result_code=0):
    """Shape of the body PayHero POSTs to the callback URL."""
    return {'response': {
        'Amount': amount,
        'ExternalReference': ref,
        'MpesaReceiptNumber': 'SGR7XYZ123',
        'Phone': '+254700000000',
        'ResultCode': result_code,
        'ResultDesc': 'The service request is processed successfully.',
        'Status': status_str,
    }}


@override_settings(
    PAYHERO_CALLBACK_SECRET=SECRET,
    PAYHERO_CALLBACK_URL='https://api.example.com/api/subscriptions/confirmation/',
    PAYHERO_CHANNEL_ID='123',
)
class PaymentFlowTests(TestCase):
    """Tests for the PayHero payment integration."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='pay_test_user',
            email='pay@kedira.ac.ke',
            password='testpass123',
            is_student=True
        )
        self.client.force_authenticate(user=self.user)

    def _pending_txn(self, amount='1.00', tier='mentor_elite', coupon=None):
        return Transaction.objects.create(
            user=self.user, phone='0700000000', ref_id='PH-TEST0001',
            amount=Decimal(amount), target_tier=tier, coupon=coupon, status='PENDING',
        )

    # ── Initiation ────────────────────────────────────────────────────
    @patch('apps.subscriptions.views.initiate_payhero_stk_push')
    def test_initiate_creates_pending_transaction(self, mock_push):
        section("Initiate → PENDING transaction")
        mock_push.return_value = {'success': True, 'status': 'QUEUED', 'reference': 'R1'}

        res = self.client.post('/api/subscriptions/initiate/',
                               {'phone_number': '0700000000', 'target_tier': 'mentor_elite'}, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        txn = Transaction.objects.get(ref_id=res.data['external_reference'])
        self.assertEqual(txn.status, 'PENDING')
        self.assertEqual(txn.target_tier, 'mentor_elite')
        ok("Pending transaction stored and reference returned")

    @patch('apps.subscriptions.views.initiate_payhero_stk_push')
    def test_initiate_failure_marks_transaction_failed(self, mock_push):
        section("Initiate refused by PayHero → FAILED")
        mock_push.return_value = {'success': False, 'error': 'Invalid phone'}

        res = self.client.post('/api/subscriptions/initiate/',
                               {'phone_number': '0700000000', 'target_tier': 'mentor_elite'}, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid phone')
        self.assertEqual(Transaction.objects.get(user=self.user).status, 'FAILED')
        ok("Transaction closed so polling reports the failure")

    def test_initiate_rejects_unknown_tier(self):
        res = self.client.post('/api/subscriptions/initiate/',
                               {'phone_number': '0700000000', 'target_tier': 'explorer'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_callback_url_carries_secret(self):
        self.assertIn(f'secret={SECRET}', build_callback_url())

    @override_settings(PAYHERO_CHANNEL_ID='4321', PAYHERO_API_USERNAME='new-user', PAYHERO_API_PASSWORD='new-pass')
    @patch('apps.subscriptions.utils.requests.post')
    def test_stk_push_uses_configured_credentials(self, mock_post):
        section("STK push is built from settings (env), not code")
        mock_post.return_value.json.return_value = {'success': True, 'status': 'QUEUED'}

        initiate_payhero_stk_push('0700000000', 1, 'PH-TEST0001', 'Test User')

        sent = mock_post.call_args.kwargs
        self.assertEqual(sent['json']['channel_id'], 4321)
        self.assertEqual(sent['json']['phone_number'], '+254700000000')
        self.assertTrue(sent['json']['callback_url'].startswith(
            'https://api.example.com/api/subscriptions/confirmation/?secret='))
        self.assertEqual(sent['headers']['Authorization'],
                         'Basic ' + base64.b64encode(b'new-user:new-pass').decode())
        ok("Channel ID, API user/password and callback URL all come from configuration")

    @override_settings(PAYHERO_CHANNEL_ID='')
    @patch('apps.subscriptions.utils.requests.post')
    def test_stk_push_refuses_when_unconfigured(self, mock_post):
        result = initiate_payhero_stk_push('0700000000', 1, 'PH-TEST0001', 'Test User')
        self.assertFalse(result['success'])
        mock_post.assert_not_called()

    # ── Callback security ─────────────────────────────────────────────
    def test_callback_without_secret_is_rejected(self):
        section("Forged callback (no secret) → 403")
        self._pending_txn()
        anon = APIClient()

        res = anon.post(CALLBACK, payhero_callback('PH-TEST0001'), format='json')

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'explorer')
        self.assertEqual(Transaction.objects.get(ref_id='PH-TEST0001').status, 'PENDING')
        ok("Tier unchanged")

    def test_callback_with_wrong_secret_is_rejected(self):
        self._pending_txn()
        res = APIClient().post(f'{CALLBACK}?secret=wrong', payhero_callback('PH-TEST0001'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PAYHERO_CALLBACK_SECRET='')
    def test_callback_rejected_when_secret_not_configured(self):
        self._pending_txn()
        res = APIClient().post(f'{CALLBACK}?secret=', payhero_callback('PH-TEST0001'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Callback outcomes ─────────────────────────────────────────────
    def test_callback_success_upgrades_user(self):
        section("Valid callback → upgrade")
        self._pending_txn()

        res = APIClient().post(f'{CALLBACK}?secret={SECRET}', payhero_callback('PH-TEST0001'), format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'mentor_elite')
        txn = Transaction.objects.get(ref_id='PH-TEST0001')
        self.assertEqual(txn.status, 'SUCCESS')
        self.assertEqual(txn.mpesa_receipt, 'SGR7XYZ123')
        ok("User moved to mentor_elite")

    def test_callback_failure_does_not_upgrade(self):
        self._pending_txn()
        res = APIClient().post(f'{CALLBACK}?secret={SECRET}',
                               payhero_callback('PH-TEST0001', status_str='Failed', result_code=1032),
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['success'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'explorer')
        self.assertEqual(Transaction.objects.get(ref_id='PH-TEST0001').status, 'FAILED')

    def test_underpaid_callback_is_marked_failed(self):
        section("Underpaid callback → FAILED")
        self._pending_txn(amount='499.00', tier='scholar_vvip')

        APIClient().post(f'{CALLBACK}?secret={SECRET}', payhero_callback('PH-TEST0001', amount=1), format='json')

        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'explorer')
        self.assertEqual(Transaction.objects.get(ref_id='PH-TEST0001').status, 'FAILED')
        ok("1 KES cannot buy a 499 KES plan")

    def test_replayed_callback_is_not_reapplied(self):
        coupon = Coupon.objects.create(code='PA1B2', marketer_email='m@example.com')
        self._pending_txn(coupon=coupon)
        url = f'{CALLBACK}?secret={SECRET}'

        APIClient().post(url, payhero_callback('PH-TEST0001'), format='json')
        res = APIClient().post(url, payhero_callback('PH-TEST0001', status_str='Failed', result_code=1),
                               format='json')

        self.assertEqual(res.data['message'], 'Already processed')
        self.assertEqual(Transaction.objects.get(ref_id='PH-TEST0001').status, 'SUCCESS')
        self.assertEqual(CouponUsed.objects.count(), 1)

    def test_callback_unknown_reference(self):
        res = APIClient().post(f'{CALLBACK}?secret={SECRET}', payhero_callback('PH-NOPE'), format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ── Status polling ────────────────────────────────────────────────
    def test_status_reports_pending_then_completed(self):
        self._pending_txn()
        self.assertEqual(self.client.get('/api/subscriptions/status/').data['status'], 'pending')

        APIClient().post(f'{CALLBACK}?secret={SECRET}', payhero_callback('PH-TEST0001'), format='json')

        res = self.client.get('/api/subscriptions/status/')
        self.assertEqual(res.data['status'], 'completed')
        self.assertEqual(res.data['tier'], 'mentor_elite')
