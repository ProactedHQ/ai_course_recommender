from django.db import models
from django.conf import settings
from django.utils import timezone


class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mpesatransactions'
    )
    phone = models.CharField(max_length=20, blank=True, default='Unknown')
    ref_id = models.CharField(max_length=100, unique=True)  # external_reference or receipt
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')],
        default='PENDING'
    )
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