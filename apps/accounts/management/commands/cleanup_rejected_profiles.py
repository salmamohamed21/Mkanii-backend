from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import ResidentProfile


class Command(BaseCommand):
    help = 'Delete rejected resident profiles older than 15 days'

    def handle(self, *args, **options):
        fifteen_days_ago = timezone.now() - timedelta(days=15)
        deleted_count, _ = ResidentProfile.objects.filter(
            status='rejected',
            rejected_at__lt=fifteen_days_ago
        ).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} rejected resident profiles older than 15 days')
        )
