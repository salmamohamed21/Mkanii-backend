from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.buildings.models import Building

class Command(BaseCommand):
    help = 'Check buildings for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
            buildings = Building.objects.filter(union_head=user)
            self.stdout.write(f"User {email} has {buildings.count()} buildings:")
            for b in buildings:
                self.stdout.write(f"  - {b.name} (id: {b.id})")
        except User.DoesNotExist:
            self.stdout.write(f"User {email} not found")
