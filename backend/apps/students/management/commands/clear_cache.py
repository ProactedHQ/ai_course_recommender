"""
Management command to clear Redis cache.
Usage: 
  python manage.py clear_cache              # Clear all cache
  python manage.py clear_cache --pattern subjects_*   # Clear specific pattern
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear Redis cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            help='Cache key pattern to clear (e.g., subjects_*)',
        )

    def handle(self, *args, **options):
        pattern = options.get('pattern')
        
        if pattern:
            try:
                cache.delete_pattern(pattern)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully cleared cache for pattern: {pattern}')
                )
            except AttributeError:
                self.stdout.write(
                    self.style.WARNING('⚠️  Cache backend does not support pattern deletion (using in-memory cache)')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error clearing cache: {e}')
                )
        else:
            try:
                cache.clear()
                self.stdout.write(
                    self.style.WARNING('✅ Successfully cleared ALL cache')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error clearing cache: {e}')
                )
