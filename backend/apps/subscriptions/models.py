"""
Payment records (PostgreSQL). One Transaction per upgrade attempt; rows are never deleted.

Status lifecycle (enforced in services.apply_payment_outcome):
  PENDING  -> SUCCESS | FAILED | CANCELLED | EXPIRED | VERIFYING
  VERIFYING-> SUCCESS | FAILED            (callback passed, waiting for PayHero status API)
  EXPIRED  -> SUCCESS                     (a verified late payment still counts)
  SUCCESS, FAILED, CANCELLED are final.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Transaction(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFYING = 'VERIFYING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFYING, 'Verifying'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_transactions'
    )
    phone = models.CharField(max_length=20, blank=True, default='Unknown')
    # Our reference (PH-XXXXXXXX); sent to PayHero as external_reference and echoed in the callback
    ref_id = models.CharField(max_length=100, unique=True)
    # PayHero's own reference from the initiate response; used for GET transaction-status
    provider_reference = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Receipt number reported in the provider callback. Column name kept from the original schema.
    provider_receipt = models.CharField(max_length=100, blank=True, null=True, db_column='mpesa_receipt')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    target_tier = models.CharField(
        max_length=50,
        choices=[('explorer', 'Explorer'), ('mentor_elite', 'Mentor Elite'), ('scholar_vvip', 'Scholar VVIP')],
        default='mentor_elite'
    )
    failure_reason = models.TextField(blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions_transaction'  # matches your raw SQL table name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['ref_id']),
        ]

    def __str__(self):
        return f"Tx {self.ref_id} - {self.status} - KES {self.amount}"


class Coupon(models.Model):
    code = models.CharField(max_length=5, unique=True, db_index=True)
    marketer_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.marketer_email})"


class CouponUsed(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='uses')
    transaction = models.ForeignKey(
        'Transaction', 
        on_delete=models.CASCADE, 
        related_name='coupon_uses'
    )
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'transaction')