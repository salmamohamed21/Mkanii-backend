from django.core.management.base import BaseCommand
from apps.accounts.models import User, Role, UserRole
from apps.accounts.models import ResidentProfile
from apps.buildings.models import Building

class Command(BaseCommand):
    help = 'Sync user roles based on their profiles (ResidentProfile and Building union_head)'

    def handle(self, *args, **options):
        # Get or create roles
        resident_role, _ = Role.objects.get_or_create(name='resident')
        union_head_role, _ = Role.objects.get_or_create(name='union_head')

        # Sync for residents
        resident_profiles = ResidentProfile.objects.all()
        for profile in resident_profiles:
            user = profile.user
            if not user.userrole_set.filter(role=resident_role).exists():
                UserRole.objects.create(user=user, role=resident_role)
                self.stdout.write(f"Added 'resident' role to user {user.email}")

        # Sync for union_heads
        buildings = Building.objects.filter(union_head__isnull=False)
        for building in buildings:
            user = building.union_head
            if not user.userrole_set.filter(role=union_head_role).exists():
                UserRole.objects.create(user=user, role=union_head_role)
                self.stdout.write(f"Added 'union_head' role to user {user.email}")

        self.stdout.write(self.style.SUCCESS('Successfully synced user roles'))
