"""
Payment flow tests. Run with APP_ENV=test (python run_tests.py does this): mock provider,
in-memory SQLite. Real PayHero HTTP is never called - requests is patched where PayHero is used.
All credential-like values below are fake test fixtures.
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import Coupon, CouponUsed, Transaction

User = get_user_model()

SECRET = 'test-callback-secret'
CALLBACK = '/api/subscriptions/confirmation/'
INITIATE = '/api/subscriptions/initiate/'
STATUS = '/api/subscriptions/status/'
MOCK_COMPLETE = '/api/subscriptions/mock/complete/'

PAYHERO_TEST_SETTINGS = dict(
    PAYMENT_PROVIDER='payhero',
    PAYHERO_CHANNEL_ID='123',
    PAYHERO_API_USERNAME='test-user',
    PAYHERO_API_PASSWORD='test-pass',
    PAYHERO_CALLBACK_URL='https://api.example.test/api/subscriptions/confirmation/',
    PAYHERO_CALLBACK_SECRET=SECRET,
    PAYHERO_VERIFY_WITH_STATUS_API=False,
)


def http_response(status_code=200, body=None):
    resp = MagicMock(status_code=status_code)
    resp.json.return_value = body if body is not None else {}
    return resp


def payhero_callback(ref, status_str='Success', amount=1, result_code=0, receipt='SGR7XYZ123'):
    """Shape of the body PayHero POSTs to the callback URL."""
    data = {
        'ExternalReference': ref,
        'MpesaReceiptNumber': receipt,
        'ResultCode': result_code,
        'ResultDesc': 'The service request is processed successfully.',
        'Status': status_str,
    }
    if amount is not None:
        data['Amount'] = amount
    return {'response': data}


class PaymentTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='payer', email='payer@example.test',
                                             password='x', is_student=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def pending(self, ref='PH-TEST0001', amount='1.00', tier='mentor_elite', coupon=None, provider_ref='PR-1'):
        return Transaction.objects.create(user=self.user, phone='+254700000000', ref_id=ref,
                                          amount=Decimal(amount), target_tier=tier, coupon=coupon,
                                          provider_reference=provider_ref, status=Transaction.STATUS_PENDING)

    def post_callback(self, body, secret=SECRET):
        url = f'{CALLBACK}?secret={secret}' if secret is not None else CALLBACK
        return APIClient().post(url, body, format='json')

    def tier(self):
        self.user.refresh_from_db()
        return self.user.subscription_tier


# ─────────────────────────────────────────────────────────────────────────────
# Initiation
# ─────────────────────────────────────────────────────────────────────────────
class InitiateTests(PaymentTestBase):

    def test_mock_initiate_creates_pending_with_server_price(self):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['provider'], 'mock')
        txn = Transaction.objects.get(ref_id=res.data['external_reference'])
        self.assertEqual(txn.status, Transaction.STATUS_PENDING)
        self.assertEqual(txn.amount, Decimal('1'))  # non-production price
        self.assertEqual(txn.phone, '+254712345678')
        self.assertTrue(txn.provider_reference.startswith('MOCK-'))

    def test_client_cannot_set_amount_or_status(self):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'scholar_vvip',
                                          'amount': 1, 'status': 'SUCCESS'}, format='json')
        txn = Transaction.objects.get(ref_id=res.data['external_reference'])
        self.assertEqual(txn.amount, Decimal('499'))
        self.assertEqual(txn.status, Transaction.STATUS_PENDING)
        self.assertEqual(self.tier(), 'explorer')

    def test_invalid_tier_and_phone(self):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'explorer'}, format='json')
        self.assertEqual(res.data['error'], 'INVALID_TIER')
        res = self.client.post(INITIATE, {'phone_number': '12345', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.data['error'], 'INVALID_PHONE')
        self.assertFalse(Transaction.objects.exists())

    def test_requires_login(self):
        res = APIClient().post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertIn(res.status_code, (401, 403))

    def test_rate_limited_after_three_attempts(self):
        body = {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}
        for _ in range(3):
            self.assertEqual(self.client.post(INITIATE, body, format='json').status_code, 200)
        res = self.client.post(INITIATE, body, format='json')
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.data['error'], 'TOO_MANY_ATTEMPTS')

    @override_settings(SUBSCRIPTION_PRICES_KES={'mentor_elite': 199, 'scholar_vvip': 499})
    def test_coupon_discount_is_whole_shillings(self):
        Coupon.objects.create(code='PA1B2', marketer_email='m@example.test')
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite',
                                          'coupon': 'PA1B2'}, format='json')
        self.assertEqual(Transaction.objects.get(ref_id=res.data['external_reference']).amount, Decimal('179'))

    @override_settings(**{**PAYHERO_TEST_SETTINGS, 'PAYHERO_API_PASSWORD': ''})
    def test_missing_configuration_returns_503(self):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data['error'], 'PAYMENTS_UNAVAILABLE')
        self.assertFalse(Transaction.objects.exists())

    @override_settings(**PAYHERO_TEST_SETTINGS, IS_PRODUCTION=True)
    @patch('apps.subscriptions.providers.requests.post')
    def test_payhero_request_built_from_settings(self, mock_post):
        mock_post.return_value = http_response(200, {'success': True, 'status': 'QUEUED', 'reference': 'PR-ABC'})
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertNotIn('provider', res.data)  # never revealed in production
        sent = mock_post.call_args.kwargs
        self.assertEqual(sent['json']['channel_id'], 123)
        self.assertEqual(sent['json']['phone_number'], '+254712345678')
        self.assertTrue(sent['json']['callback_url'].endswith(f'?secret={SECRET}'))
        self.assertTrue(sent['headers']['Authorization'].startswith('Basic '))
        self.assertEqual(Transaction.objects.get().provider_reference, 'PR-ABC')

    @override_settings(**PAYHERO_TEST_SETTINGS)
    @patch('apps.subscriptions.providers.requests.post')
    def test_payhero_api_failure(self, mock_post):
        mock_post.return_value = http_response(500)
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.status_code, 502)
        self.assertEqual(res.data['error'], 'PAYMENT_INITIATION_FAILED')
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_FAILED)

    @override_settings(**PAYHERO_TEST_SETTINGS)
    @patch('apps.subscriptions.providers.requests.post', side_effect=requests.Timeout)
    def test_payhero_timeout(self, _):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.status_code, 502)
        txn = Transaction.objects.get()
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)
        self.assertEqual(txn.failure_reason, 'PayHero timed out')

    @override_settings(**PAYHERO_TEST_SETTINGS)
    @patch('apps.subscriptions.providers.requests.post')
    def test_payhero_not_queued(self, mock_post):
        mock_post.return_value = http_response(200, {'success': False, 'status': 'FAILED'})
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        self.assertEqual(res.status_code, 502)

    @override_settings(**PAYHERO_TEST_SETTINGS)
    @patch('apps.subscriptions.providers.requests.post')
    def test_error_responses_leak_nothing(self, mock_post):
        mock_post.return_value = http_response(401, {'error': 'bad credentials for test-user'})
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': 'mentor_elite'}, format='json')
        text = str(res.data)
        for leaked in ('test-user', 'test-pass', SECRET, 'Basic', 'PayHero HTTP'):
            self.assertNotIn(leaked, text)


# ─────────────────────────────────────────────────────────────────────────────
# PayHero callback
# ─────────────────────────────────────────────────────────────────────────────
@override_settings(**PAYHERO_TEST_SETTINGS)
class CallbackTests(PaymentTestBase):

    def test_success_upgrades_user(self):
        self.pending()
        res = self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])
        txn = Transaction.objects.get()
        self.assertEqual(txn.status, Transaction.STATUS_SUCCESS)
        self.assertEqual(txn.provider_receipt, 'SGR7XYZ123')
        self.assertEqual(self.tier(), 'mentor_elite')

    def test_failed_payment(self):
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001', status_str='Failed', result_code=1))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_FAILED)
        self.assertEqual(self.tier(), 'explorer')

    def test_cancelled_payment(self):
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001', status_str='Failed', result_code=1032))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_CANCELLED)
        self.assertEqual(self.tier(), 'explorer')

    def test_unauthorized_callbacks(self):
        self.pending()
        self.assertEqual(self.post_callback(payhero_callback('PH-TEST0001'), secret=None).status_code, 403)
        self.assertEqual(self.post_callback(payhero_callback('PH-TEST0001'), secret='wrong').status_code, 403)
        # a logged-in customer can't confirm their own payment either
        self.assertEqual(self.client.post(CALLBACK, payhero_callback('PH-TEST0001'), format='json').status_code, 403)
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_PENDING)
        self.assertEqual(self.tier(), 'explorer')

    @override_settings(PAYHERO_CALLBACK_SECRET='')
    def test_rejected_when_secret_not_configured(self):
        self.pending()
        self.assertEqual(self.post_callback(payhero_callback('PH-TEST0001'), secret='').status_code, 403)

    def test_invalid_callback_bodies(self):
        self.pending()
        self.assertEqual(self.post_callback({'response': {'Status': 'Success'}}).status_code, 400)
        self.assertEqual(self.post_callback({'response': 'oops'}).status_code, 400)
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_PENDING)

    def test_incorrect_transaction_reference(self):
        self.pending()
        self.assertEqual(self.post_callback(payhero_callback('PH-NOPE')).status_code, 404)
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_PENDING)

    def test_incorrect_amount_lower_higher_missing(self):
        for i, amount in enumerate([0.5, 2, None]):
            ref = f'PH-AMT{i}'
            self.pending(ref=ref)
            self.post_callback(payhero_callback(ref, amount=amount))
            txn = Transaction.objects.get(ref_id=ref)
            self.assertEqual(txn.status, Transaction.STATUS_FAILED, amount)
        self.assertEqual(self.tier(), 'explorer')

    def test_duplicate_callback_is_idempotent(self):
        coupon = Coupon.objects.create(code='PA1B2', marketer_email='m@example.test')
        self.pending(coupon=coupon)
        self.post_callback(payhero_callback('PH-TEST0001'))
        res = self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(res.data['message'], 'Already processed')
        late_failure = self.post_callback(payhero_callback('PH-TEST0001', status_str='Failed', result_code=1))
        self.assertEqual(late_failure.data['message'], 'Already processed')
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_SUCCESS)
        self.assertEqual(CouponUsed.objects.count(), 1)

    def test_late_success_after_expiry_still_counts(self):
        txn = self.pending()
        Transaction.objects.filter(pk=txn.pk).update(status=Transaction.STATUS_EXPIRED)
        self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_SUCCESS)
        self.assertEqual(self.tier(), 'mentor_elite')

    def test_failure_after_cancel_is_ignored(self):
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001', status_str='Failed', result_code=1032))
        self.post_callback(payhero_callback('PH-TEST0001'))  # success after cancel: not applied
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_CANCELLED)
        self.assertEqual(self.tier(), 'explorer')


# ─────────────────────────────────────────────────────────────────────────────
# Server-side verification with PayHero's status API
# ─────────────────────────────────────────────────────────────────────────────
@override_settings(**{**PAYHERO_TEST_SETTINGS, 'PAYHERO_VERIFY_WITH_STATUS_API': True})
class VerificationTests(PaymentTestBase):

    @patch('apps.subscriptions.providers.requests.get')
    def test_verified_success_activates(self, mock_get):
        mock_get.return_value = http_response(200, {'status': 'SUCCESS'})
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(mock_get.call_args.kwargs['params'], {'reference': 'PR-1'})
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_SUCCESS)

    @patch('apps.subscriptions.providers.requests.get')
    def test_unconfirmed_success_waits_then_activates_on_poll(self, mock_get):
        mock_get.return_value = http_response(200, {'status': 'QUEUED'})
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_VERIFYING)
        self.assertEqual(self.tier(), 'explorer')
        self.assertEqual(self.client.get(STATUS).data['status'], 'pending')

        mock_get.return_value = http_response(200, {'status': 'SUCCESS'})
        res = self.client.get(STATUS)
        self.assertEqual(res.data['status'], 'completed')
        self.assertEqual(self.tier(), 'mentor_elite')

    @patch('apps.subscriptions.providers.requests.get')
    def test_status_api_failure_never_activates(self, mock_get):
        mock_get.side_effect = requests.Timeout
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_VERIFYING)
        mock_get.side_effect = None
        mock_get.return_value = http_response(200, {'status': 'FAILED'})
        self.client.get(STATUS)
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_FAILED)
        self.assertEqual(self.tier(), 'explorer')

    @patch('apps.subscriptions.providers.requests.get')
    def test_unrecognised_status_response_is_unknown(self, mock_get):
        mock_get.return_value = http_response(200, {'something': 'else'})
        self.pending()
        self.post_callback(payhero_callback('PH-TEST0001'))
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_VERIFYING)


# ─────────────────────────────────────────────────────────────────────────────
# Status polling & expiry
# ─────────────────────────────────────────────────────────────────────────────
class StatusTests(PaymentTestBase):

    def test_not_found_then_pending(self):
        self.assertEqual(self.client.get(STATUS).data['status'], 'not_found')
        self.pending()
        self.assertEqual(self.client.get(STATUS).data['status'], 'pending')

    def test_stale_pending_expires(self):
        txn = self.pending()
        Transaction.objects.filter(pk=txn.pk).update(created_at=timezone.now() - timedelta(minutes=30))
        self.assertEqual(self.client.get(STATUS).data['status'], 'expired')
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_EXPIRED)

    def test_status_endpoint_is_read_only(self):
        self.pending()
        self.assertEqual(self.client.post(STATUS, {'status': 'completed'}, format='json').status_code, 405)
        self.assertEqual(Transaction.objects.get().status, Transaction.STATUS_PENDING)
        self.assertEqual(self.tier(), 'explorer')


# ─────────────────────────────────────────────────────────────────────────────
# Local mock payments (no credentials)
# ─────────────────────────────────────────────────────────────────────────────
class MockPaymentTests(PaymentTestBase):

    def start(self, tier='mentor_elite'):
        res = self.client.post(INITIATE, {'phone_number': '0712345678', 'target_tier': tier}, format='json')
        return res.data['external_reference']

    def test_full_mock_flow_success(self):
        ref = self.start()
        self.assertEqual(self.client.get(STATUS).data['status'], 'pending')
        res = self.client.post(MOCK_COMPLETE, {'external_reference': ref, 'outcome': 'success'}, format='json')
        self.assertEqual(res.data['status'], 'completed')
        self.assertEqual(self.client.get(STATUS).data['status'], 'completed')
        self.assertEqual(self.tier(), 'mentor_elite')

    def test_mock_failed_cancelled_and_duplicate(self):
        ref = self.start()
        self.client.post(MOCK_COMPLETE, {'external_reference': ref, 'outcome': 'cancelled'}, format='json')
        res = self.client.post(MOCK_COMPLETE, {'external_reference': ref, 'outcome': 'success'}, format='json')
        self.assertEqual(res.data['reason'], 'ALREADY_FINAL')
        self.assertEqual(self.client.get(STATUS).data['status'], 'cancelled')

        Transaction.objects.all().delete()
        ref = self.start()
        self.client.post(MOCK_COMPLETE, {'external_reference': ref, 'outcome': 'failed'}, format='json')
        self.assertEqual(self.client.get(STATUS).data['status'], 'failed')
        self.assertEqual(self.tier(), 'explorer')

    def test_cannot_complete_someone_elses_payment(self):
        ref = self.start()
        other = User.objects.create_user(username='other', email='o@example.test', password='x')
        client = APIClient()
        client.force_authenticate(user=other)
        res = client.post(MOCK_COMPLETE, {'external_reference': ref, 'outcome': 'success'}, format='json')
        self.assertEqual(res.status_code, 404)

    @override_settings(**PAYHERO_TEST_SETTINGS)
    def test_mock_endpoint_disabled_with_real_provider(self):
        txn = self.pending()
        res = self.client.post(MOCK_COMPLETE, {'external_reference': txn.ref_id, 'outcome': 'success'}, format='json')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(self.tier(), 'explorer')

    @override_settings(IS_PRODUCTION=True)
    def test_mock_endpoint_disabled_in_production(self):
        txn = self.pending()
        res = self.client.post(MOCK_COMPLETE, {'external_reference': txn.ref_id, 'outcome': 'success'}, format='json')
        self.assertEqual(res.status_code, 404)

    def test_management_command(self):
        ref = self.start()
        out = StringIO()
        call_command('mock_payment', ref, 'success', stdout=out)
        self.assertIn('status=SUCCESS', out.getvalue())
        self.assertEqual(self.tier(), 'mentor_elite')
