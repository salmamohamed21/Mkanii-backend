import os
import django
from django.conf import settings
from django.db import models

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

# Add the fields back to ResidentProfile model
from apps.accounts.models import ResidentProfile

# Check if fields exist, if not add them
if not hasattr(ResidentProfile, 'apartment_number'):
    ResidentProfile.add_to_class('apartment_number', models.CharField(max_length=10, null=True, blank=True))
if not hasattr(ResidentProfile, 'manual_building_name'):
    ResidentProfile.add_to_class('manual_building_name', models.CharField(max_length=255, null=True, blank=True))
if not hasattr(ResidentProfile, 'manual_address'):
    ResidentProfile.add_to_class('manual_address', models.TextField(null=True, blank=True))

print("Fields added to ResidentProfile model")
