"""
Subscription payment endpoints (mounted at /api/subscriptions/). PayHero is the only real provider.

  POST initiate/        logged-in user starts an upgrade        -> services.start_payment
  POST confirmation/    PayHero callback (secret in query)      -> services.apply_payment_outcome
  GET  status/          frontend polls its latest payment       -> services.refresh_pending_state
  POST generate-coupon/ referral coupon
  POST mock/complete/   DEVELOPMENT/TEST ONLY (mock provider): finish a pending payment by hand

Flow: frontend -> initiate -> PayHero -> customer's M-Pesa prompt -> PayHero -> confirmation
      -> (optional PayHero status check) -> Transaction SUCCESS + user tier -> frontend sees it via status.
"""
import hmac
import logging
import random
import string

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from . import services
from .models import Coupon, Transaction
from .providers import get_provider

logger = logging.getLogger(__name__)

# What the frontend sees for each stored status
STATUS_FOR_CLIENT = {
    Transaction.STATUS_PENDING: 'pending',
    Transaction.STATUS_VERIFYING: 'pending',
    Transaction.STATUS_SUCCESS: 'completed',
    Transaction.STATUS_FAILED: 'failed',
    Transaction.STATUS_CANCELLED: 'cancelled',
    Transaction.STATUS_EXPIRED: 'expired',
}
CLIENT_MESSAGES = {
    'pending': 'Waiting for payment confirmation.',
    'completed': 'Payment completed.',
    'failed': 'Payment failed. Please try again.',
    'cancelled': 'Payment was cancelled.',
    'expired': 'We did not receive a payment confirmation in time.',
}


def _error(err):
    return Response({'error': err.code, 'detail': err.detail}, status=err.http_status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Body: {"phone_number": "07...", "target_tier": "mentor_elite"|"scholar_vvip", "coupon"?: "AB12C"}
    Any amount/status sent by the client is ignored; the price comes from settings.

    200 {"success": true, "external_reference": "PH-XXXXXXXX", "amount": "199.00", "message": ...,
         "provider": "mock"  (only outside production)}
    4xx/5xx {"error": CODE, "detail": message}
    """
    try:
        txn = services.start_payment(
            request.user,
            request.data.get('target_tier'),
            request.data.get('phone_number'),
            request.data.get('coupon') or None,
        )
    except services.PaymentError as err:
        return _error(err)
    except Exception:
        logger.exception("[initiate_payment] Unexpected error for user %s", request.user.id)
        return Response({'error': 'PAYMENT_INITIATION_FAILED',
                         'detail': 'We could not start the payment. Please try again.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    body = {
        'success': True,
        'external_reference': txn.ref_id,
        'amount': str(txn.amount),
        'message': 'Payment request sent. Check your phone.',
    }
    if not settings.IS_PRODUCTION:
        body['provider'] = get_provider().name  # lets the dev UI offer mock completion buttons
    return Response(body)


def _callback_secret_is_valid(request):
    expected = settings.PAYHERO_CALLBACK_SECRET
    if not expected:
        logger.error("[confirmation] PAYHERO_CALLBACK_SECRET is not set - rejecting all payment callbacks.")
        return False
    return hmac.compare_digest(str(request.query_params.get('secret', '')), str(expected))


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation(request):
    """
    PayHero -> us (server-to-server). Never called by the frontend.

    403 bad/missing secret · 400 unusable body · 404 unknown reference · otherwise 200,
    including duplicates (acknowledged, not re-applied) so PayHero doesn't keep retrying.
    """
    if not _callback_secret_is_valid(request):
        logger.warning("[confirmation] Rejected callback with missing/invalid secret")
        return Response({'success': False, 'message': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    try:
        data = services.parse_payhero_callback(request.data)
    except ValueError as e:
        logger.warning("[confirmation] Unusable callback body: %s", e)
        return Response({'success': False, 'message': 'Invalid callback'}, status=status.HTTP_400_BAD_REQUEST)

    logger.info("[confirmation] %s outcome=%s result_code=%s", data['ref_id'], data['outcome'], data['result_code'])

    txn = Transaction.objects.filter(ref_id=data['ref_id']).first()
    if txn is None:
        logger.warning("[confirmation] Unknown reference %s", data['ref_id'])
        return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    verified = True
    if data['outcome'] == services.SUCCESS:
        verified, provider_state = services.verify_with_provider(txn)
        if not verified:
            logger.warning("[confirmation] %s not yet confirmed by PayHero status API (%s)",
                           txn.ref_id, provider_state)

    try:
        result = services.apply_payment_outcome(
            data['ref_id'], data['outcome'], amount=data['amount'], receipt=data['receipt'],
            reason=data['reason'], verified=verified, source='payhero-callback',
        )
    except Exception:
        logger.exception("[confirmation] Error applying %s", data['ref_id'])
        return Response({'success': False, 'message': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if result.reason == 'ALREADY_FINAL':
        return Response({'success': result.status == Transaction.STATUS_SUCCESS, 'message': 'Already processed'})
    return Response({'success': result.status == Transaction.STATUS_SUCCESS,
                     'message': STATUS_FOR_CLIENT.get(result.status, 'pending')})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request):
    """
    The caller's most recent payment: {"status": completed|pending|failed|cancelled|expired|not_found,
    "message", "external_reference"?, "tier"?}. Read-only for the client; it can never set a status.
    """
    txn = Transaction.objects.filter(user=request.user).order_by('-created_at').first()
    if txn is None:
        return Response({'status': 'not_found', 'message': 'No transaction found'})

    txn = services.refresh_pending_state(txn)
    request.user.refresh_from_db(fields=['subscription_tier'])  # may have just been upgraded above

    # Self-healing: a SUCCESS whose tier was not applied (e.g. crash mid-callback) is applied here
    if txn.status == Transaction.STATUS_SUCCESS and request.user.subscription_tier != txn.target_tier:
        logger.warning("[payment_status] Repairing tier for user %s from %s", request.user.id, txn.ref_id)
        request.user.subscription_tier = txn.target_tier
        request.user.save(update_fields=['subscription_tier'])

    client_status = STATUS_FOR_CLIENT[txn.status]
    body = {'status': client_status, 'message': CLIENT_MESSAGES[client_status],
            'external_reference': txn.ref_id}
    if client_status == 'completed':
        body['tier'] = request.user.subscription_tier
    return Response(body)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mock_complete_payment(request):
    """
    DEVELOPMENT/TEST ONLY. Finishes the caller's own pending mock payment through the same
    services.apply_payment_outcome() used by the real callback.
    Body: {"external_reference": "PH-...", "outcome": "success"|"failed"|"cancelled"}
    404 unless PAYMENT_PROVIDER=mock outside production.
    """
    if settings.IS_PRODUCTION or settings.PAYMENT_PROVIDER != 'mock':
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    outcome = str(request.data.get('outcome', '')).upper()
    if outcome not in (services.SUCCESS, services.FAILED, services.CANCELLED):
        return Response({'error': 'INVALID_OUTCOME', 'detail': 'outcome must be success, failed or cancelled'},
                        status=status.HTTP_400_BAD_REQUEST)

    txn = Transaction.objects.filter(ref_id=request.data.get('external_reference'), user=request.user).first()
    if txn is None:
        return Response({'error': 'NOT_FOUND', 'detail': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    result = services.apply_payment_outcome(txn.ref_id, outcome, amount=txn.amount,
                                            receipt=f"MOCK{txn.pk:06d}", source='mock')
    return Response({'applied': result.applied, 'status': STATUS_FOR_CLIENT.get(result.status, 'pending'),
                     'reason': result.reason})


def generate_unique_coupon(marketer_email: str):
    """Creates a unique 5-char coupon with at least one letter from 'PROACTED' and digits"""
    proacted_letters = "PROACTED"
    full_pool = string.ascii_uppercase + string.digits
    while True:
        code_chars = [random.choice(proacted_letters)]
        code_chars += random.choices(full_pool, k=4)
        random.shuffle(code_chars)
        code = "".join(code_chars)
        if not Coupon.objects.filter(code=code).exists():
            return Coupon.objects.create(code=code, marketer_email=marketer_email)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_my_coupon(request):
    """Mint a new referral coupon tied to the caller's email. Returns {"success": true, "coupon": "AB12C"}."""
    if not request.user.email:
        return Response({'error': 'User email not found'}, status=status.HTTP_400_BAD_REQUEST)
    coupon = generate_unique_coupon(request.user.email)
    return Response({
        'success': True,
        'coupon': coupon.code,
        'message': 'Your referral coupon has been created successfully!'
    })
