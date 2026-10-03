"""
Subscription upgrades via PayHero (M-Pesa STK push) and referral coupons.

Upgrade flow (frontend: pages/app/Subscription.jsx):
  1. POST /api/subscriptions/initiate/      -> creates a PENDING Transaction, PayHero sends STK push
  2. Student enters M-Pesa PIN on their phone
  3. POST /api/subscriptions/confirmation/  <- PayHero callback (server-to-server, secret-checked)
                                               marks the Transaction SUCCESS/FAILED and upgrades the user
  4. GET  /api/subscriptions/status/        <- frontend polls every 3s until completed/failed

Coupons: any logged-in user can mint a 5-char referral code (generate-coupon/);
a valid code gives 10% off and is recorded in CouponUsed once the payment succeeds.
"""
import hmac
import logging
import random
import string
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Transaction, Coupon, CouponUsed
from .utils import initiate_payhero_stk_push

User = get_user_model()
logger = logging.getLogger(__name__)


# --- Helper Functions ---

def get_base_amount(target_tier):
    """Return the KES price for a paid tier, or None for an unknown/free tier."""
    # NOTE: mentor_elite is still at the 1 KES test price.
    amounts = {
        'mentor_elite': 1,
        'scholar_vvip': 499,
    }
    return amounts.get(target_tier)


def validate_coupon(coupon_code):
    """Return the Coupon for `coupon_code`, or None if it is empty or unknown."""
    if not coupon_code:
        return None
    try:
        return Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return None


def calculate_discounted_amount(base_amount, coupon_obj):
    """Apply the flat 10% coupon discount (rounded to 2dp) when a coupon is present."""
    if coupon_obj:
        discount = float(base_amount) * 0.10
        return round(float(base_amount) - discount, 2)
    return base_amount


def record_coupon_usage(txn):
    """Record one CouponUsed row for a successful transaction that used a coupon (idempotent)."""
    if txn.coupon:
        try:
            if not CouponUsed.objects.filter(transaction=txn).exists():
                CouponUsed.objects.create(
                    coupon=txn.coupon,
                    transaction=txn
                )
                logger.info(f"[COUPON] Usage recorded: {txn.coupon.code} for transaction {txn.ref_id}")
        except Exception as e:
            logger.error(f"[COUPON] Coupon usage recording failed: {str(e)}")


def _callback_secret_is_valid(request):
    """
    True if the callback carries ?secret= matching MPESA_CALLBACK_SECRET.

    utils.build_callback_url() puts the secret on the URL we hand to PayHero, so only
    callbacks for pushes we started can pass. With no secret configured, nothing passes.
    """
    expected = settings.MPESA_CALLBACK_SECRET
    if not expected:
        logger.error("[confirmation] MPESA_CALLBACK_SECRET is not set - rejecting all payment callbacks.")
        return False
    provided = request.query_params.get('secret', '')
    return hmac.compare_digest(str(provided), str(expected))


def _paid_amount_covers(txn, amount):
    """True if the amount PayHero reports is at least what we charged (missing amount = trust status)."""
    if amount in (None, ''):
        return True
    try:
        return Decimal(str(amount)) >= txn.amount
    except (InvalidOperation, TypeError):
        return False


# --- Views ---

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Start an upgrade: price the tier (minus coupon), store a PENDING Transaction,
    and ask PayHero to send the STK push.

    Body: {"phone_number": "07...", "target_tier": "mentor_elite"|"scholar_vvip", "coupon": "AB12C"?}
    200:  {"success": true, "external_reference": "PH-XXXXXXXX", "message": ...}
    400:  {"error": "..."}  (missing phone, bad tier, or PayHero refused the push)
    """
    try:
        data = request.data
        phone_number = data.get('phone_number')
        target_tier = data.get('target_tier')  # mentor_elite | scholar_vvip
        coupon_code = data.get('coupon')  # Optional referral coupon

        # 1. Get base amount
        base_amount = get_base_amount(target_tier)

        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if base_amount is None:
            return Response({'error': 'Invalid tier selected'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check for coupon and calculate discount (an unknown coupon just means full price)
        coupon_obj = validate_coupon(coupon_code)
        amount = calculate_discounted_amount(base_amount, coupon_obj)

        logger.info(
            "[initiate_payment] user=%s current_tier=%s target_tier=%s amount=%s coupon=%s",
            request.user.id, request.user.subscription_tier, target_tier, amount,
            coupon_obj.code if coupon_obj else None,
        )

        # 3. Create a pending transaction record; its ref_id is how the callback finds it
        external_reference = f"PH-{uuid.uuid4().hex[:8].upper()}"
        customer_name = request.user.get_full_name() or request.user.username

        Transaction.objects.create(
            user=request.user,
            phone=phone_number,
            ref_id=external_reference,
            amount=amount,
            target_tier=target_tier,
            coupon=coupon_obj,
            status='PENDING'
        )

        # 4. Ask PayHero to push the M-Pesa prompt to the phone
        response = initiate_payhero_stk_push(
            phone_number=phone_number,
            amount=amount,
            external_reference=external_reference,
            customer_name=customer_name,
            provider="m-pesa"
        )
        logger.info("[initiate_payment] PayHero response for %s: %s", external_reference, response)

        if response.get('success') and response.get('status') == 'QUEUED':
            return Response({
                'success': True,
                'reference': response.get('reference'),
                'CheckoutRequestID': response.get('CheckoutRequestID'),
                'external_reference': external_reference,
                'message': 'Payment request sent. Check your phone.'
            })

        # Push was not queued: close the transaction so status polling reports it
        Transaction.objects.filter(ref_id=external_reference).update(
            status='FAILED', failure_reason=str(response.get('error', 'Payment initiation failed'))
        )
        return Response({
            'error': response.get('error', 'Payment initiation failed')
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Payment initiation failed: {str(e)}", exc_info=True)
        return Response({'error': 'Payment initiation failed. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation(request):
    """
    PayHero callback (server-to-server). Not called by the frontend.

    Security checks, in order:
      1. ?secret= must match MPESA_CALLBACK_SECRET            -> else 403
      2. ExternalReference must match a Transaction we created  -> else 404
      3. Only PENDING transactions are processed (replays are acknowledged, not re-applied)
      4. A "success" must report an Amount >= what we charged   -> else marked FAILED

    On success the user's subscription_tier is set to the transaction's target_tier.
    """
    if not _callback_secret_is_valid(request):
        logger.warning("[confirmation] Rejected callback with missing/invalid secret from %s",
                       request.META.get('REMOTE_ADDR'))
        return Response({'success': False, 'message': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    try:
        payload = request.data
        logger.info(f"[confirmation] Payload received: {payload}")

        # PayHero usually nests the data under 'response'
        response_data = payload.get('response', payload)

        amount = response_data.get('Amount')
        external_reference = response_data.get('ExternalReference')
        mpesa_receipt = response_data.get('MpesaReceiptNumber')
        result_code = response_data.get('ResultCode')
        status_str = response_data.get('Status')
        result_desc = response_data.get('ResultDesc', response_data.get('Description', ''))

        if not external_reference:
            logger.error(f"[confirmation] Missing external reference in payload: {payload}")
            return Response({'success': False, 'message': 'Missing external reference'}, status=status.HTTP_400_BAD_REQUEST)

        payment_success = (status_str in ('Success', 'SUCCESS') or result_code == 0)

        with transaction.atomic():
            try:
                # Lock the row so two callbacks for the same payment can't both apply
                txn = Transaction.objects.select_for_update().get(ref_id=external_reference)
            except Transaction.DoesNotExist:
                logger.error(f"[confirmation] Transaction not found: {external_reference}")
                return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

            if txn.status != 'PENDING':
                logger.info("[confirmation] %s already %s - ignoring repeat callback", txn.ref_id, txn.status)
                return Response({'success': txn.status == 'SUCCESS', 'message': 'Already processed'},
                                status=status.HTTP_200_OK)

            if payment_success and not _paid_amount_covers(txn, amount):
                logger.error("[confirmation] %s reported Amount=%s but we charged %s - marking FAILED",
                             txn.ref_id, amount, txn.amount)
                payment_success = False
                result_desc = 'Paid amount does not match the subscription price.'

            txn.status = 'SUCCESS' if payment_success else 'FAILED'
            txn.mpesa_receipt = mpesa_receipt
            if not payment_success:
                txn.failure_reason = result_desc
            txn.save()

            if payment_success and txn.user:
                user = txn.user
                record_coupon_usage(txn)

                # Use the tier stored at initiation, never one guessed from the amount
                user.subscription_tier = txn.target_tier
                user.save(update_fields=['subscription_tier'])
                logger.info(f"[confirmation] User {user.id} upgraded to {user.subscription_tier} via {txn.ref_id}")

        return Response({
            'success': payment_success,
            'message': 'Payment confirmed' if payment_success else 'Payment failed'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"[confirmation] Confirmation error: {str(e)}", exc_info=True)
        return Response({'success': False, 'message': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request):
    """
    Report the state of the user's most recent Transaction.

    Polled every 3s by the frontend after initiate/. Returns
    {"status": "completed"|"failed"|"pending"|"not_found", "message": ..., "tier"?: ...}.
    Also self-heals: a SUCCESS transaction whose tier was not applied gets applied here.
    """
    txn = Transaction.objects.filter(user=request.user).order_by('-created_at').first()

    if txn:
        # Self-healing: If txn is SUCCESS but user tier doesn't match, fix it now
        if txn.status == 'SUCCESS' and txn.target_tier and request.user.subscription_tier != txn.target_tier:
            logger.warning("[payment_status] Repairing tier for user %s: %s -> %s",
                           request.user.id, request.user.subscription_tier, txn.target_tier)
            request.user.subscription_tier = txn.target_tier
            request.user.save(update_fields=['subscription_tier'])

        if txn.status == 'SUCCESS':
            return Response({
                'status': 'completed',
                'message': 'Payment completed',
                'tier': request.user.subscription_tier
            })
        elif txn.status == 'FAILED':
            return Response({'status': 'failed', 'message': txn.failure_reason or 'Payment failed. Please try again.'})

        return Response({'status': 'pending', 'message': 'Waiting for confirmation'})

    return Response({'status': 'not_found', 'message': 'No transaction found'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def test_stk(request):
    """DEBUG-only (see urls.py): send a 10 KES test push to a hardcoded number."""
    phone_number = '[REDACTED_PHONE]'  # change for real testing
    amount = 10
    external_reference = str(request.user.id)
    customer_name = request.user.get_full_name() or request.user.username

    try:
        response = initiate_payhero_stk_push(
            phone_number=phone_number,
            amount=amount,
            external_reference=external_reference,
            customer_name=customer_name,
            provider="m-pesa"
        )

        if response.get('success') and response.get('status') == 'QUEUED':
            return Response({
                'success': True,
                'message': 'Test payment initiated',
                'reference': response.get('reference')
            })

        return Response({'error': response.get('error', 'Failed')}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Test STK failed: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def debug_headers(request):
    """DEBUG-only (see urls.py): echo request headers to diagnose proxy/header stripping."""
    headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
    return Response({
        'headers': headers,
        'origin': request.META.get('HTTP_ORIGIN'),
        'referer': request.META.get('HTTP_REFERER'),
        'method': request.method,
        'is_secure': request.is_secure(),
        'csrf_cookie': request.COOKIES.get('csrftoken'),
    })


def generate_unique_coupon(marketer_email: str):
    """Creates a unique 5-char coupon with at least one letter from 'PROACTED' and digits"""
    proacted_letters = "PROACTED"
    full_pool = string.ascii_uppercase + string.digits
    while True:
        # 1. Guarantee at least one letter from PROACTED
        code_chars = [random.choice(proacted_letters)]
        # 2. Fill the rest (4 more) from the full pool of uppercase + digits
        code_chars += random.choices(full_pool, k=4)
        # 3. Shuffle so the PROACTED letter isn't always in the same spot
        random.shuffle(code_chars)
        code = "".join(code_chars)

        if not Coupon.objects.filter(code=code).exists():
            coupon = Coupon.objects.create(
                code=code,
                marketer_email=marketer_email
            )
            return coupon


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_my_coupon(request):
    """Mint a new referral coupon tied to the caller's email. Returns {"success": true, "coupon": "AB12C"}."""
    marketer_email = request.user.email

    if not marketer_email:
        return Response({'error': 'User email not found'}, status=status.HTTP_400_BAD_REQUEST)

    coupon = generate_unique_coupon(marketer_email)

    return Response({
        'success': True,
        'coupon': coupon.code,
        'message': 'Your referral coupon has been created successfully!'
    })
