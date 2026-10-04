"""
PayHero-only payment records. Additive: no rows or columns are dropped.

Database changes:
  - new nullable column provider_reference (PayHero's reference, for status lookups)
State-only changes (no SQL):
  - mpesa_receipt field renamed to provider_receipt; the column stays "mpesa_receipt"
  - status gains VERIFYING / CANCELLED / EXPIRED choices (choices are not stored in Postgres)
  - user reverse accessor renamed to payment_transactions
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_transaction_failure_reason'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(
                    model_name='transaction',
                    old_name='mpesa_receipt',
                    new_name='provider_receipt',
                ),
                migrations.AlterField(
                    model_name='transaction',
                    name='provider_receipt',
                    field=models.CharField(blank=True, db_column='mpesa_receipt', max_length=100, null=True),
                ),
            ],
            database_operations=[],
        ),
        migrations.AddField(
            model_name='transaction',
            name='provider_reference',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'), ('VERIFYING', 'Verifying'), ('SUCCESS', 'Success'),
                    ('FAILED', 'Failed'), ('CANCELLED', 'Cancelled'), ('EXPIRED', 'Expired'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payment_transactions',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
