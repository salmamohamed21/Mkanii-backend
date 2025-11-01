from django.core.management.base import BaseCommand
from apps.core.tasks import check_rental_end_dates


class Command(BaseCommand):
    help = 'Check for expired rentals and deactivate tenants if not renewed'

    def handle(self, *args, **options):
        self.stdout.write('Checking for expired rentals...')
        check_rental_end_dates()
        self.stdout.write(self.style.SUCCESS('Rental check completed successfully'))
