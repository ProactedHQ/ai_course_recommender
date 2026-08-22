from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import uuid
import logging
from .utils import initiate_payhero_stk_push
from .models import Transaction, Coupon, CouponUsed
import random
import string
from django.contrib.auth.decorators import login_required

User = get_user_model()
logger = logging.getLogger(__name__)


# --- Helper Functions ---

def get_base_amount(target_tier):
    """Returns the base price for each subscription tier (1 KES for testing)"""
    amounts = {
        'mentor_elite': 1,
        'scholar_vvip': 499,
    }
    return amounts.get(target_tier)


def validate_coupon(coupon_code):
    """Checks if a coupon exists and is valid"""
    if not coupon_code:
        return None
    try:
        return Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return None


def calculate_discounted_amount(base_amount, coupon_obj):
    """Applies a 10% discount if a valid coupon is provided"""
    if coupon_obj:
        discount = float(base_amount) * 0.10
        return round(float(base_amount) - discount, 2)
    return base_amount


def record_coupon_usage(txn):
    """Records coupon usage in the CouponUsed table after successful payment"""
    if txn.coupon:
        try:
            # Check if usage already recorded for this transaction to avoid duplicates
            if not CouponUsed.objects.filter(transaction=txn).exists():
                CouponUsed.objects.create(
                    coupon=txn.coupon,
                    transaction=txn
                )
                print(f"[OK] [COUPON] Usage recorded: {txn.coupon.code} for transaction {txn.ref_id}")
        except Exception as e:
            print(f"[ERROR] [COUPON] Failed to record usage: {str(e)}")
            logger.error(f"Coupon usage recording failed: {str(e)}")


# --- Views ---

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    print("\n--- [initiate_payment] Starting payment initiation ---")
    try:
        data = request.data # DRF handles JSON parsing
        phone_number = data.get('phone_number')
        target_tier = data.get('target_tier') # explorer, mentor_elite, scholar_vvip
        coupon_code = data.get('coupon') # Optional coupon from frontend
        
        print(f"[initiate_payment] Data received: phone={phone_number}, tier={target_tier}, coupon={coupon_code}")

        # 1. Get base amount
        base_amount = get_base_amount(target_tier)
        
        if not phone_number:
            print("[initiate_payment] Error: Phone number is missing")
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if base_amount is None:
            print("[initiate_payment] Error: Invalid tier selected")
            return Response({'error': 'Invalid tier selected'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check for coupon and calculate discount
        coupon_obj = validate_coupon(coupon_code)
        amount = calculate_discounted_amount(base_amount, coupon_obj)
        
        if coupon_code and not coupon_obj:
            print(f"[initiate_payment] Warning: Invalid coupon code '{coupon_code}' provided")
            # Optionally, you could return an error here, but typically we just proceed with the full amount

        print(f"\n--- [initiate_payment] REQUEST ---")
        print(f"User: {request.user.username} | Current Tier: {request.user.subscription_tier}")
        print(f"Target Tier: {target_tier}")
        print(f"Base Amount: {base_amount} | Final Amount: {amount}")
        if coupon_obj:
            print(f"Applied Coupon: {coupon_obj.code} (10% Discount)")

        # 3. Create a pending transaction record
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
        print("[initiate_payment] Pending transaction record created in DB")

        print("[initiate_payment] Calling initiate_payhero_stk_push...")
        response = initiate_payhero_stk_push(
            phone_number=phone_number,
            amount=amount,
            external_reference=external_reference,
            customer_name=customer_name,
            provider="m-pesa"
        )
        print(f"[initiate_payment] PayHero Response: {response}")

        if response.get('success') and response.get('status') == 'QUEUED':
            print("[initiate_payment] STK push queued successfully")
            return Response({
                'success': True,
                'reference': response.get('reference'),
                'CheckoutRequestID': response.get('CheckoutRequestID'),
                'external_reference': external_reference,
                'message': 'Payment request sent. Check your phone.'
            })

        print(f"[initiate_payment] STK push failed: {response.get('error', 'Payment initiation failed')}")
        return Response({
            'error': response.get('error', 'Payment initiation failed')
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"[initiate_payment] Exception occurred: {str(e)}")
        logger.error(f"Payment initiation failed: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation(request):
    print("\n--- [confirmation] Received callback from PayHero ---")
    try:
        payload = request.data
        print(f"[confirmation] Full payload received: {payload}")
        
        # PayHero usually sends data in a 'response' or directly
        response_data = payload.get('response', payload) 

        amount = response_data.get('Amount')
        checkout_request_id = response_data.get('CheckoutRequestID')
        external_reference = response_data.get('ExternalReference')
        mpesa_receipt = response_data.get('MpesaReceiptNumber')
        phone = response_data.get('Phone')
        result_code = response_data.get('ResultCode')
        status_str = response_data.get('Status')
        result_desc = response_data.get('ResultDesc', response_data.get('Description', ''))
        
        print(f"[confirmation] Extracted: ref={external_reference}, status={status_str}, result={result_code}, receipt={mpesa_receipt}, desc={result_desc}")

        if not external_reference:
            print("[confirmation] Error: Missing external reference in payload")
            logger.error(f"Missing external reference in payload: {payload}")
            return Response({'success': False, 'message': 'Missing external reference'}, status=status.HTTP_400_BAD_REQUEST)

        payment_success = (status_str == 'Success' or status_str == 'SUCCESS' or result_code == 0)
        print(f"[confirmation] Payment success status: {payment_success}")

        with transaction.atomic():
            try:
                txn = Transaction.objects.get(ref_id=external_reference)
                print(f"[confirmation] Found transaction in DB for ref: {external_reference}")
                
                txn.status = 'SUCCESS' if payment_success else 'FAILED'
                txn.mpesa_receipt = mpesa_receipt
                if not payment_success:
                    txn.failure_reason = result_desc
                txn.save()
                print(f"[confirmation] Updated transaction status to: {txn.status}")

                if payment_success and txn.user:
                    user = txn.user
                    print(f"[UPGRADE_FLOW] Processing successful payment for {user.username}")
                    
                    # Record coupon usage if applicable
                    record_coupon_usage(txn)
                    
                    print(f"[UPGRADE_FLOW] Stored target_tier in txn: {txn.target_tier}")
                    
                    # Use the stored target tier instead of guessing from amount
                    user.subscription_tier = txn.target_tier
                    user.save(update_fields=['subscription_tier'])
                    
                    # Force refresh from DB to verify
                    user.refresh_from_db()
                    print(f"[UPGRADE_FLOW] User tier AFTER save: {user.subscription_tier}")
                    
                    if user.subscription_tier == txn.target_tier:
                        print(f"[OK] [UPGRADE_FLOW] SUCCESS: User {user.username} successfully moved to {user.subscription_tier}")
                    else:
                        print(f"[ERROR] [UPGRADE_FLOW] ERROR: User tier mismatch! Expected {txn.target_tier}, got {user.subscription_tier}")
                    
                    logger.info(f"User {user.id} upgraded to {user.subscription_tier} via PayHero")

            except Transaction.DoesNotExist:
                print(f"[confirmation] Error: Transaction not found for ref: {external_reference}")
                logger.error(f"Transaction not found: {external_reference}")
                return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': payment_success,
            'message': 'Payment confirmed' if payment_success else 'Payment failed'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[confirmation] Exception occurred: {str(e)}")
        logger.error(f"Confirmation error: {str(e)}", exc_info=True)
        return Response({'success': False, 'message': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request):
    print(f"\n--- [payment_status] Checking status for user: {request.user.username} ---")
    txn = Transaction.objects.filter(user=request.user).order_by('-created_at').first()

    if txn:
        print(f"[payment_status] Latest transaction found: ref={txn.ref_id}, status={txn.status}, target={txn.target_tier}")
        
        # Self-healing: If txn is SUCCESS but user tier doesn't match, fix it now
        if txn.status == 'SUCCESS' and txn.target_tier and request.user.subscription_tier != txn.target_tier:
            print(f"[WARN] [payment_status] Tier mismatch detected! Repairing: {request.user.subscription_tier} -> {txn.target_tier}")
            request.user.subscription_tier = txn.target_tier
            request.user.save(update_fields=['subscription_tier'])
            print(f"[OK] [payment_status] Repair successful")

        if txn.status == 'SUCCESS':
            print(f"[payment_status] Returning success. Current user tier: {request.user.subscription_tier}")
            return Response({
                'status': 'completed',
                'message': 'Payment completed',
                'tier': request.user.subscription_tier
            })
        elif txn.status == 'FAILED':
            print("[payment_status] Returning failed status")
            return Response({'status': 'failed', 'message': txn.failure_reason or 'Payment failed. Please try again.'})
        
        print("[payment_status] Returning pending status")
        return Response({'status': 'pending', 'message': 'Waiting for confirmation'})

    print("[payment_status] No transaction found for user")
    return Response({'status': 'not_found', 'message': 'No transaction found'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def test_stk(request):

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
    # Use logged-in user's email as marketer ID
    marketer_email = request.user.email

    if not marketer_email:
        return Response({'error': 'User email not found'}, status=status.HTTP_400_BAD_REQUEST)

    coupon = generate_unique_coupon(marketer_email)

    return Response({
        'success': True,
        'coupon': coupon.code,
        'message': 'Your referral coupon has been created successfully!'
    }, status=status.HTTP_201_CREATED)