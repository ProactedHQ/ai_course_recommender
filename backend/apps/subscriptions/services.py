"""
Payment business logic, shared by every entry point (views, mock endpoint, management command).

Only apply_payment_outcome() moves a Transaction to SUCCESS, and only after:
  - the outcome came from the provider callback (secret-checked) or the dev-only mock path,
  - the transaction reference exists,
  - the reported amount equals the amount we charged, exactly,
  - the transition is allowed from the current status (row-locked, so duplicates are no-ops),
  - (optionally) PayHero's status API agrees - see verify_with_provider().
The frontend can never declare a payment successful.
"""
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Coupon, CouponUsed, Transaction
from .providers import get_provider

logger = logging.getLogger(__name__)

SUCCESS, FAILED, CANCELLED = 'SUCCESS', 'FAILED', 'CANCELLED'

# PayHero passes through the mobile-money result code; 1032 = customer cancelled the prompt.
RESULT_CODE_CANCELLED_BY_USER = 1032

KENYAN_MOBILE_RE = re.compile(r'^(?:\+?254|0)?([17]\d{8})$')


class PaymentError(Exception):
    """A request-level failure with a safe, customer-facing message."""

    def __init__(self, code, detail, http_status):
        super().__init__(detail)
        self.code, self.detail, self.http_status = code, detail, http_status


@dataclass
class ApplyResult:
    applied: bool
    status: str        # the transaction's status afterwards ('' if not found)
    reason: str = ''   # NOT_FOUND | ALREADY_FINAL | AMOUNT_MISMATCH | AWAITING_VERIFICATION


# ---------------------------------------------------------------------------
# Pricing & input
# ---------------------------------------------------------------------------

def price_for_tier(target_tier):
    """KES price for a paid tier from settings.SUBSCRIPTION_PRICES_KES, or None."""
    price = settings.SUBSCRIPTION_PRICES_KES.get(target_tier)
    return Decimal(price) if price is not None else None


def apply_coupon(base_amount, coupon):
    """10% off with a valid coupon, rounded to whole shillings (mobile money has no cents), min 1."""
    if not coupon:
        return base_amount
    discounted = (base_amount * Decimal('0.9')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return max(discounted, Decimal('1'))


def normalize_phone(phone):
    """07XXXXXXXX / 2547XXXXXXXX / +2547XXXXXXXX (and 01...) -> +2547XXXXXXXX, else None."""
    match = KENYAN_MOBILE_RE.match(str(phone or '').strip().replace(' ', ''))
    return f"+254{match.group(1)}" if match else None


def mask_phone(phone):
    return f"{phone[:4]}****{phone[-3:]}" if phone and len(phone) > 7 else '****'


# ---------------------------------------------------------------------------
# Start a payment
# ---------------------------------------------------------------------------

def start_payment(user, target_tier, phone_number, coupon_code=None):
    """
    Create a PENDING Transaction and ask the provider to prompt the customer.
    The amount comes only from server-side prices. Raises PaymentError.
    """
    base_amount = price_for_tier(target_tier)
    if base_amount is None:
        raise PaymentError('INVALID_TIER', 'Please choose a valid plan.', 400)

    phone = normalize_phone(phone_number)
    if not phone:
        raise PaymentError('INVALID_PHONE', 'Please enter a valid Safaricom/Kenyan mobile number.', 400)

    provider = get_provider()
    if not provider.is_configured():
        logger.error("[payments] Provider %s is not configured - payments unavailable", provider.name)
        raise PaymentError('PAYMENTS_UNAVAILABLE', 'Payments are temporarily unavailable. Please try again later.', 503)

    window_start = timezone.now() - timedelta(minutes=settings.PAYMENT_ATTEMPT_WINDOW_MINUTES)
    if Transaction.objects.filter(user=user, created_at__gte=window_start).count() >= settings.PAYMENT_MAX_ATTEMPTS_PER_WINDOW:
        raise PaymentError('TOO_MANY_ATTEMPTS', 'Too many payment attempts. Please wait a few minutes.', 429)

    coupon = Coupon.objects.filter(code=coupon_code).first() if coupon_code else None
    amount = apply_coupon(base_amount, coupon)

    txn = Transaction.objects.create(
        user=user,
        phone=phone,
        ref_id=f"PH-{uuid.uuid4().hex[:8].upper()}",
        amount=amount,
        target_tier=target_tier,
        coupon=coupon,
        status=Transaction.STATUS_PENDING,
    )

    result = provider.initiate(phone, amount, txn.ref_id, user.get_full_name() or user.username)
    if not result.ok:
        txn.status = Transaction.STATUS_FAILED
        txn.failure_reason = result.error
        txn.save(update_fields=['status', 'failure_reason', 'updated_at'])
        logger.error("[payments] %s initiation failed via %s: %s", txn.ref_id, provider.name, result.error)
        raise PaymentError('PAYMENT_INITIATION_FAILED',
                           'We could not start the payment. Please try again.', 502)

    txn.provider_reference = result.provider_reference or None
    txn.save(update_fields=['provider_reference', 'updated_at'])
    logger.info("[payments] %s started via %s: user=%s tier=%s amount=%s phone=%s",
                txn.ref_id, provider.name, user.id, target_tier, amount, mask_phone(phone))
    return txn


# ---------------------------------------------------------------------------
# Record an outcome
# ---------------------------------------------------------------------------

_ALLOWED = {
    Transaction.STATUS_PENDING: {SUCCESS, FAILED, CANCELLED},
    Transaction.STATUS_VERIFYING: {SUCCESS, FAILED},
    Transaction.STATUS_EXPIRED: {SUCCESS},
}


def _amount_matches(txn, amount):
    try:
        return Decimal(str(amount)).quantize(Decimal('0.01')) == txn.amount.quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return False


def apply_payment_outcome(ref_id, outcome, *, amount=None, receipt=None, reason='', verified=True, source=''):
    """
    The single place a payment changes state. `verified=False` parks a valid success in
    VERIFYING instead of activating the plan. Safe to call repeatedly with the same input.
    """
    with db_transaction.atomic():
        txn = Transaction.objects.select_for_update().filter(ref_id=ref_id).first()
        if txn is None:
            return ApplyResult(False, '', 'NOT_FOUND')

        if outcome not in _ALLOWED.get(txn.status, set()):
            logger.info("[payments] %s: ignoring %s from %s (already %s)", ref_id, outcome, source, txn.status)
            return ApplyResult(False, txn.status, 'ALREADY_FINAL')

        if outcome == SUCCESS and txn.status != Transaction.STATUS_VERIFYING and not _amount_matches(txn, amount):
            txn.status = Transaction.STATUS_FAILED
            txn.failure_reason = 'Paid amount does not match the subscription price.'
            txn.save(update_fields=['status', 'failure_reason', 'updated_at'])
            logger.error("[payments] %s: amount mismatch from %s (reported=%s expected=%s) - marked FAILED",
                         ref_id, source, amount, txn.amount)
            return ApplyResult(False, txn.status, 'AMOUNT_MISMATCH')

        if receipt:
            txn.provider_receipt = str(receipt)[:100]

        if outcome == SUCCESS and not verified:
            txn.status = Transaction.STATUS_VERIFYING
            txn.save(update_fields=['status', 'provider_receipt', 'updated_at'])
            logger.warning("[payments] %s: callback OK, awaiting provider verification", ref_id)
            return ApplyResult(False, txn.status, 'AWAITING_VERIFICATION')

        if outcome == SUCCESS:
            txn.status = Transaction.STATUS_SUCCESS
            txn.failure_reason = None
            txn.save(update_fields=['status', 'provider_receipt', 'failure_reason', 'updated_at'])
            if txn.coupon and not CouponUsed.objects.filter(transaction=txn).exists():
                CouponUsed.objects.create(coupon=txn.coupon, transaction=txn)
            if txn.user:
                txn.user.subscription_tier = txn.target_tier
                txn.user.save(update_fields=['subscription_tier'])
            logger.info("[payments] %s SUCCESS via %s: user=%s -> %s", ref_id, source,
                        txn.user_id, txn.target_tier)
            return ApplyResult(True, txn.status)

        txn.status = Transaction.STATUS_CANCELLED if outcome == CANCELLED else Transaction.STATUS_FAILED
        txn.failure_reason = (reason or ('Payment was cancelled.' if outcome == CANCELLED else 'Payment failed.'))[:500]
        txn.save(update_fields=['status', 'provider_receipt', 'failure_reason', 'updated_at'])
        logger.info("[payments] %s %s via %s", ref_id, txn.status, source)
        return ApplyResult(True, txn.status)


# ---------------------------------------------------------------------------
# PayHero callback & verification
# ---------------------------------------------------------------------------

def parse_payhero_callback(payload):
    """
    Extract what we need from a PayHero callback body. Raises ValueError if unusable.
    Returns dict(ref_id, outcome, amount, receipt, reason, result_code).
    """
    if not isinstance(payload, dict):
        raise ValueError('callback body is not an object')
    data = payload.get('response', payload)
    if not isinstance(data, dict):
        raise ValueError('callback "response" is not an object')

    ref_id = str(data.get('ExternalReference') or '').strip()
    if not ref_id:
        raise ValueError('missing ExternalReference')

    try:
        result_code = int(data.get('ResultCode')) if data.get('ResultCode') is not None else None
    except (TypeError, ValueError):
        result_code = None
    status_str = str(data.get('Status') or '').strip().lower()

    if status_str == 'success' or result_code == 0:
        outcome = SUCCESS
    elif result_code == RESULT_CODE_CANCELLED_BY_USER:
        outcome = CANCELLED
    else:
        outcome = FAILED

    return {
        'ref_id': ref_id,
        'outcome': outcome,
        'amount': data.get('Amount'),
        'receipt': data.get('MpesaReceiptNumber'),  # PayHero's field name for the receipt
        'reason': str(data.get('ResultDesc') or '')[:200],
        'result_code': result_code,
    }


def verify_with_provider(txn):
    """
    True if a success may be applied now. When PAYHERO_VERIFY_WITH_STATUS_API is on and the
    provider is PayHero, PayHero's status API must report SUCCESS for this payment.
    Returns (verified: bool, provider_state: str).
    """
    provider = get_provider()
    if provider.name != 'payhero' or not settings.PAYHERO_VERIFY_WITH_STATUS_API:
        return True, 'NOT_REQUIRED'
    if not txn.provider_reference:
        return False, 'NO_REFERENCE'
    state = provider.get_status(txn.provider_reference).state
    return state == 'SUCCESS', state


def refresh_pending_state(txn):
    """
    Called while the customer polls. Re-checks VERIFYING payments with PayHero and expires
    PENDING ones older than PAYMENT_PENDING_TIMEOUT_MINUTES. Returns the (reloaded) txn.
    """
    if txn.status == Transaction.STATUS_VERIFYING:
        verified, state = verify_with_provider(txn)
        if verified:
            apply_payment_outcome(txn.ref_id, SUCCESS, verified=True, source='status-recheck')
        elif state == 'FAILED':
            apply_payment_outcome(txn.ref_id, FAILED, reason='Provider reported the payment as failed.',
                                  source='status-recheck')
    elif txn.status == Transaction.STATUS_PENDING:
        cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_PENDING_TIMEOUT_MINUTES)
        if txn.created_at < cutoff:
            Transaction.objects.filter(pk=txn.pk, status=Transaction.STATUS_PENDING).update(
                status=Transaction.STATUS_EXPIRED,
                failure_reason='No payment confirmation was received in time.',
                updated_at=timezone.now(),
            )
            logger.info("[payments] %s EXPIRED", txn.ref_id)
    txn.refresh_from_db()
    return txn
