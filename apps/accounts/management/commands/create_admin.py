from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@gmail.com'
        password = '123'

        # Get or create admin role
        admin_role, created = Role.objects.get_or_create(name='admin')

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists.'))
            return

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            full_name='Admin User',
            phone_number='0000000000',
            national_id='0000000000',
            is_superuser=True,
            is_staff=True
        )

        # Assign admin role
        user.roles.add(admin_role)

        self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {email}'))
