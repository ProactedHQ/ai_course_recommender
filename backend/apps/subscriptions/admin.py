from django.contrib import admin

from .models import Coupon, CouponUsed, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Read-only payment history. Status changes only happen through services.apply_payment_outcome."""
    list_display = ('ref_id', 'status', 'amount', 'target_tier', 'user', 'provider_reference', 'created_at')
    list_filter = ('status', 'target_tier')
    search_fields = ('ref_id', 'provider_reference', 'provider_receipt', 'user__email')
    readonly_fields = [f.name for f in Transaction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Coupon)
admin.site.register(CouponUsed)
