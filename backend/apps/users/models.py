from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import date


def get_first_day_of_month():
    """Returns the first day of the current month."""
    return date.today().replace(day=1)


class CustomUser(AbstractUser): 
    """
    Custom user model to handle both students and admins.
    
    Role invariants (enforced in clean/save):
      - Student:    is_student=True,  is_staff=False, is_superuser=False
      - Staff:      is_student=False, is_staff=True
      - Superuser:  is_student=False, is_staff=True,  is_superuser=True
    
    A user CANNOT be both staff and student simultaneously.
    """
    is_student = models.BooleanField(default=False)
    is_institution_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # --- Subscription Fields ---
    SUBSCRIPTION_TIERS = [
        ('explorer', 'Explorer'),
        ('mentor_elite', 'Mentor Elite'),
        ('scholar_vvip', 'Scholar VVIP'),
    ]
    subscription_tier = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_TIERS, 
        default='explorer',
        db_index=True
    )
    prompts_used_in_period = models.PositiveIntegerField(default=0)
    prompt_period_start = models.DateField(default=get_first_day_of_month)

    def clean(self):
        super().clean()

        # Rule 1: staff cannot be a student
        if self.is_staff and self.is_student:
            raise ValidationError(
                "Invalid role state: staff user cannot be a student."
            )

        # Rule 2: superuser must be staff and not student
        if self.is_superuser and (not self.is_staff or self.is_student):
            raise ValidationError(
                "Invalid role state: superuser must be staff and not a student."
            )

    def save(self, *args, **kwargs):
        self.clean()  # Only validate role invariants
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username

"""
class SubscriptionTransaction(models.Model):
    # Tracks payment attempts and tier upgrades.
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    target_tier = models.CharField(
        max_length=20, 
        choices=CustomUser.SUBSCRIPTION_TIERS
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=50, help_text="e.g. mpesa")
    reference = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="M-Pesa CheckoutRequestID or Receipt number"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    raw_payload = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Raw callback payload from provider for auditing"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TXN {self.reference} - {self.user.username} ({self.status})"
"""
