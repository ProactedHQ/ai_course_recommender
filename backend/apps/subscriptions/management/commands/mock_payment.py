"""
Development/test only: finish a pending mock payment from the terminal.

    APP_ENV=development python manage.py mock_payment PH-1A2B3C4D success
    APP_ENV=development python manage.py mock_payment PH-1A2B3C4D cancelled
    APP_ENV=development python manage.py mock_payment --list

Uses the same services.apply_payment_outcome() as the real PayHero callback.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.subscriptions import services
from apps.subscriptions.models import Transaction


class Command(BaseCommand):
    help = "Complete a pending MOCK payment (development/test only)."

    def add_arguments(self, parser):
        parser.add_argument('ref_id', nargs='?', help="Transaction reference, e.g. PH-1A2B3C4D")
        parser.add_argument('outcome', nargs='?', choices=['success', 'failed', 'cancelled'])
        parser.add_argument('--list', action='store_true', help="Show the 10 most recent transactions")

    def handle(self, *args, **opts):
        if settings.IS_PRODUCTION or settings.PAYMENT_PROVIDER != 'mock':
            raise CommandError("mock_payment only works with PAYMENT_PROVIDER=mock outside production.")

        if opts['list']:
            for t in Transaction.objects.order_by('-created_at')[:10]:
                self.stdout.write(f"{t.ref_id}  {t.status:<9}  KES {t.amount}  {t.target_tier}  user={t.user_id}")
            return
        if not opts['ref_id'] or not opts['outcome']:
            raise CommandError("Usage: mock_payment <ref_id> <success|failed|cancelled>  (or --list)")

        txn = Transaction.objects.filter(ref_id=opts['ref_id']).first()
        if txn is None:
            raise CommandError(f"No transaction {opts['ref_id']}")
        result = services.apply_payment_outcome(txn.ref_id, opts['outcome'].upper(), amount=txn.amount,
                                                receipt=f"MOCK{txn.pk:06d}", source='mock-command')
        self.stdout.write(f"{txn.ref_id}: status={result.status} applied={result.applied} {result.reason}")
