from django.core.management.base import BaseCommand
from apps.buildings.models import Building
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Approve all pending buildings and set admin as union_head'

    def handle(self, *args, **options):
        admin = User.objects.filter(email='admin@gmail.com').first()
        if not admin:
            self.stdout.write(self.style.ERROR('Admin user not found'))
            return

        buildings = Building.objects.filter(approval_status='pending')
        for building in buildings:
            building.approval_status = 'approved'
            building.approved_by = admin
            building.union_head = admin  # Set admin as union_head
            building.save()

        self.stdout.write(self.style.SUCCESS(f'Approved {buildings.count()} buildings and set admin as union_head'))
