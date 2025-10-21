from django.core.management.base import BaseCommand
from mkani.apps.accounts.models import User, Role, ResidentProfile, TechnicianProfile
from mkani.apps.buildings.models import Building


class Command(BaseCommand):
    help = 'Assign roles to existing users based on their profiles'

    def handle(self, *args, **options):
        # Get or create roles
        resident_role, _ = Role.objects.get_or_create(name='resident')
        technician_role, _ = Role.objects.get_or_create(name='technician')
        union_head_role, _ = Role.objects.get_or_create(name='union_head')

        users_updated = 0

        # Assign roles based on profiles
        for user in User.objects.all():
            roles_to_assign = []

            # Check for resident profile
            if ResidentProfile.objects.filter(user=user).exists():
                roles_to_assign.append(resident_role)

            # Check for technician profile
            if TechnicianProfile.objects.filter(user=user).exists():
                roles_to_assign.append(technician_role)

            # Check for union_head
            if Building.objects.filter(union_head=user).exists():
                roles_to_assign.append(union_head_role)

            # Assign roles if any
            if roles_to_assign:
                user.roles.set(roles_to_assign)
                users_updated += 1
                self.stdout.write(f'Updated roles for user: {user.email} - Roles: {[r.name for r in roles_to_assign]}')

        self.stdout.write(self.style.SUCCESS(f'Successfully assigned roles to {users_updated} users'))
