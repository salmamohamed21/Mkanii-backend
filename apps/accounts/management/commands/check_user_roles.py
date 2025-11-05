from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Check roles for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
            roles = user.roles
            self.stdout.write(f"User {email} has roles: {roles}")
            # Also check userrole_set
            db_roles = [ur.role.name for ur in user.userrole_set.all()]
            self.stdout.write(f"DB roles: {db_roles}")
        except User.DoesNotExist:
            self.stdout.write(f"User {email} not found")
