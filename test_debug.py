import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

from apps.accounts.models import ResidentProfile
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(id=22)
print('User:', user)
print('ResidentProfile exists:', ResidentProfile.objects.filter(user=user).exists())
if ResidentProfile.objects.filter(user=user).exists():
    rp = ResidentProfile.objects.get(user=user)
    print('ResidentProfile:', rp)
    print('Unit:', rp.unit)
    print('Floor number:', rp.floor_number)
    print('Apartment number:', rp.apartment_number)
    print('Building:', rp.building)
